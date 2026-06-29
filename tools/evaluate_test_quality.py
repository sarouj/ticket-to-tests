#!/usr/bin/env python3
"""
AI meta-evaluation of agent-generated test code using DeepEval G-Eval.

Language- and framework-agnostic. Reads team_config.yaml from CWD to determine
the framework adapter; uses adapter-aware grading criteria for each metric.

Scores the test suite against four criteria:
  1. AC Coverage       — every Jira acceptance criterion has a test
  2. Error Contract    — every non-2xx test calls ASSERT_CONTRACT (status + error body)
  3. BVA Coverage      — boundary values are expressed using PARAMETRIZE per spec parameter
  4. SETUP_SCOPE       — shared read-only setup vs per-test mutating setup is correctly applied

Scores are 0-1. Any metric below its threshold is printed as a must-fix.
Exit code 0 = all metrics pass. Exit code 1 = one or more metrics fail.

Usage:
  python ~/.agents/skills/ticket-to-tests/tools/evaluate_test_quality.py \\
      --tests tests/items/create_item/ \\
      --ac "AC1: Create returns 201. AC2: Name must be unique." \\
      [--spec "name: string, max 255 chars. ownerId: UUID, required"] \\
      [--adapter pytest]            \\
      [--model groq/llama-3.1-70b-versatile] \\
      [--report-json deepeval_report.json]

Environment:
  GROQ_API_KEY      — free; get at console.groq.com
  OPENAI_API_KEY    — for OpenAI models
  ANTHROPIC_API_KEY — for Claude via Anthropic API
  AWS_PROFILE       — AWS named profile for Bedrock
  AWS_REGION        — AWS region for Bedrock (default: us-east-1)

Requires:
  pip install deepeval pyyaml
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path
from typing import Optional

try:
    from deepeval import evaluate
    from deepeval.metrics import GEval
    from deepeval.metrics.base_metric import BaseMetric
    from deepeval.test_case import LLMTestCase, SingleTurnParams
except ImportError as exc:
    print(
        "ERROR: deepeval is not installed.\n"
        "Install it with:  pip install deepeval\n"
        "Then set an API key (GROQ_API_KEY, OPENAI_API_KEY, or AWS_PROFILE for Bedrock).",
        file=sys.stderr,
    )
    raise SystemExit(1) from exc

_tools_dir = Path(__file__).parent
sys.path.insert(0, str(_tools_dir))
try:
    from team_config import load_config, framework_name as _framework_name, deepeval_model as _deepeval_model
except ImportError:
    load_config = None  # type: ignore[assignment]


_LOCAL_SCORING_PROMPT = """\
You are a senior QA engineer evaluating AI-generated test code.
Your task: read the CRITERIA below, then read the TEST CODE, and output a
JSON object with exactly two keys — "score" (a float between 0.0 and 1.0)
and "reason" (a one-sentence explanation).

EVALUATION CRITERIA:
{criteria}

CONTEXT (acceptance criteria / API spec for this feature):
{input_context}

TEST CODE TO EVALUATE:
{test_code}

Instructions:
- Apply the EVALUATION CRITERIA to the TEST CODE.
- Output ONLY a valid JSON object on a single line. No markdown, no extra text.
- Example output: {{"score": 0.8, "reason": "Most error tests call ASSERT_CONTRACT but two are missing it."}}
"""


class LocalGEval(BaseMetric):
    """Single-prompt G-Eval substitute for local (Ollama) models."""

    def __init__(self, name: str, criteria: str, threshold: float, model: object) -> None:
        self.name = name
        self.criteria = criteria
        self.threshold = threshold
        self._model = model
        self.score: float = 0.0
        self.reason: str = ""
        self.success: bool = False

    def measure(self, test_case: LLMTestCase) -> float:  # type: ignore[override]
        prompt = _LOCAL_SCORING_PROMPT.format(
            criteria=self.criteria.strip(),
            input_context=test_case.input or "(no context provided)",
            test_code=test_case.actual_output or "",
        )
        raw, _ = self._model.generate(prompt)
        try:
            json_match = re.search(r"\{[^{}]+\}", raw, re.DOTALL)
            if not json_match:
                raise ValueError(f"No JSON object found in response: {raw!r}")
            parsed = json.loads(json_match.group())
            self.score = float(parsed["score"])
            self.reason = str(parsed.get("reason", ""))
        except (ValueError, KeyError, json.JSONDecodeError) as exc:
            self.score = 0.0
            self.reason = f"Could not parse model response: {exc} — raw: {raw!r}"
        self.success = self.score >= self.threshold
        return self.score

    def is_successful(self) -> bool:
        return self.success


def _ac_coverage_criteria(framework: str) -> str:
    return f"""\
You are evaluating AI-generated test code (framework: {framework}) for a REST API service.

The INPUT contains the acceptance criteria (AC) and/or spec excerpts for a feature.
The ACTUAL OUTPUT contains the full content of one or more generated test files.

Score how well the test suite covers the acceptance criteria:
- For each distinct AC in the INPUT, determine whether there is at least one test function
  that references that criterion AND exercises the described behavior via an API call.
- Partial coverage (test only checks the status code without body assertions) counts as partial.

Return a score between 0 and 1:
  1.0 = all ACs have full test coverage
  0.75 = most ACs covered but some partially covered or missing
  0.0 = no ACs are covered
"""


def _error_contract_criteria(framework: str) -> str:
    return f"""\
You are evaluating AI-generated test code (framework: {framework}) for a REST API service.

Evaluate whether every test that expects a non-2xx HTTP response adheres to the error contract:

RULE: Every test that asserts a non-2xx status code MUST call BOTH:
  1. A status code assertion
  2. An error body assertion — validates the error response body shape

A test that only checks the status code without also asserting the error body is a violation.

Score:
  1.0 = all non-2xx tests call both status assertion AND error body assertion
  0.85 = a small minority (1-2) are missing the error body assertion
  0.5 = roughly half are missing the error body assertion
  0.0 = no non-2xx test asserts the error body at all
"""


def _bva_coverage_criteria(framework: str) -> str:
    return f"""\
You are evaluating AI-generated test code (framework: {framework}) for a REST API service.

Evaluate boundary value analysis (BVA) coverage for the parameters listed in the INPUT.

For each string or numeric parameter, check whether there is a parametrized test covering:
  - The MINIMUM valid value
  - The MAXIMUM valid value
  - A value JUST OVER the maximum (expecting 400 or 422)
  - NULL or EMPTY value when required (expecting 400)
  - WHITESPACE-ONLY string (expecting 400)
  - For enum parameters: an UNKNOWN enum value (expecting 400)

Score:
  1.0 = all parameters have all BVA cases covered and parametrized/data-driven
  0.7 = most parameters have BVA cases but some boundary cases are missing
  0.5 = BVA tests exist but are sparse
  0.0 = no BVA tests or no data-driven/parametrized tests for boundary cases
"""


def _setup_scope_criteria(framework: str) -> str:
    return f"""\
You are evaluating AI-generated test code (framework: {framework}) for a REST API service.

Evaluate whether the test code correctly applies SETUP_SCOPE (shared vs. per-test setup):

RULE 1 — Read-only tests MUST use shared/session-scoped setup helpers.
RULE 2 — Mutating tests MUST use per-test setup helpers with cleanup.
RULE 3 — No test function should create API resources directly in the test body.

Score:
  1.0 = all rules followed; setup scopes are correct for every test
  0.8 = mostly correct, with 1-2 minor violations
  0.5 = several violations (mutating tests using shared setup, or inline resource creation)
  0.0 = setup scope conventions are ignored
"""


def _resolve_model(model_str: str):
    import os
    if model_str.startswith("ollama/"):
        from deepeval.models import OllamaModel
        return OllamaModel(model=model_str.split("/", 1)[1], base_url="http://localhost:11434"), True
    if model_str.startswith("groq/"):
        from deepeval.models import LiteLLMModel
        groq_model = model_str.split("/", 1)[1]
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            raise SystemExit("ERROR: GROQ_API_KEY is not set.\nGet a free key at https://console.groq.com")
        return LiteLLMModel(model=f"groq/{groq_model}", api_key=api_key), False
    if model_str.startswith("bedrock/"):
        import boto3
        from deepeval.models import AmazonBedrockModel
        bedrock_model_id = model_str.split("/", 1)[1]
        aws_profile = os.environ.get("AWS_PROFILE", "default")
        aws_region = os.environ.get("AWS_REGION", "us-east-1")
        session = boto3.Session(profile_name=aws_profile, region_name=aws_region)
        creds = session.get_credentials().get_frozen_credentials()
        return AmazonBedrockModel(
            model=bedrock_model_id,
            aws_access_key_id=creds.access_key,
            aws_secret_access_key=creds.secret_key,
            aws_session_token=creds.token,
            region=aws_region,
        ), False
    return model_str, False


def _build_metric(name: str, criteria: str, threshold: float, model: str):
    resolved_model, is_local = _resolve_model(model)
    if is_local:
        return LocalGEval(name=name, criteria=criteria, threshold=threshold, model=resolved_model)
    return GEval(
        name=name,
        criteria=criteria,
        evaluation_params=[SingleTurnParams.INPUT, SingleTurnParams.ACTUAL_OUTPUT],
        threshold=threshold,
        model=resolved_model,
        verbose_mode=False,
    )


def _load_test_content(tests_path: str, file_pattern: str = "**/*_test.*") -> str:
    p = Path(tests_path)
    if p.is_file():
        return p.read_text(encoding="utf-8")
    if p.is_dir():
        parts: list[str] = []
        for f in sorted(p.rglob("*")):
            if f.is_file() and f.suffix in (".py", ".ts", ".java", ".go", ".rb", ".js"):
                parts.append(f"# === {f} ===\n")
                parts.append(f.read_text(encoding="utf-8"))
                parts.append("\n\n")
        if not parts:
            raise ValueError(f"No test files found under {p}")
        return "".join(parts)
    raise ValueError(f"--tests argument is neither a file nor a directory: {p}")


def _load_ac(ac: Optional[str], ac_file: Optional[str]) -> str:
    if ac:
        return ac
    if ac_file:
        return Path(ac_file).read_text(encoding="utf-8")
    return ""


def run_evaluation(
    test_content: str, ac_text: str, spec_text: str, model: str,
    report_json: Optional[str], framework: str, skip_ids: list[str],
) -> bool:
    input_context_parts = []
    if ac_text.strip():
        input_context_parts.append(f"Acceptance Criteria:\n{ac_text.strip()}")
    if spec_text.strip():
        input_context_parts.append(f"API Spec / Parameters:\n{spec_text.strip()}")
    combined_input = "\n\n".join(input_context_parts) if input_context_parts else "(no AC/spec provided)"

    METRICS_CONFIG = [
        {"id": "ac_coverage", "name": "AC Coverage", "criteria": _ac_coverage_criteria(framework), "threshold": 0.75, "needs_input": True},
        {"id": "error_contract", "name": "Error Response Contract", "criteria": _error_contract_criteria(framework), "threshold": 0.85, "needs_input": False},
        {"id": "bva_coverage", "name": "BVA PARAMETRIZE Coverage", "criteria": _bva_coverage_criteria(framework), "threshold": 0.70, "needs_input": True},
        {"id": "setup_scope", "name": "SETUP_SCOPE Adherence", "criteria": _setup_scope_criteria(framework), "threshold": 0.80, "needs_input": False},
    ]

    if skip_ids:
        METRICS_CONFIG = [m for m in METRICS_CONFIG if m["id"] not in skip_ids]
        if not METRICS_CONFIG:
            print("ERROR: all metrics were skipped — nothing to evaluate.", file=sys.stderr)
            raise SystemExit(1)

    metrics = []
    test_cases = []
    for cfg in METRICS_CONFIG:
        metric = _build_metric(cfg["name"], cfg["criteria"], cfg["threshold"], model)
        metrics.append((cfg, metric))
        test_cases.append(LLMTestCase(
            input=combined_input if cfg["needs_input"] else "(self-contained — see criteria)",
            actual_output=test_content,
        ))

    print(f"\n{'='*70}")
    print(f"DeepEval: Test Quality Evaluation  [{framework}]")
    print(f"Model: {model}")
    print(f"{'='*70}\n")

    results = []
    all_passed = True

    for idx, ((cfg, metric), test_case) in enumerate(zip(metrics, test_cases)):
        if idx > 0:
            time.sleep(15)
        print(f"Evaluating: {cfg['name']} (threshold >= {cfg['threshold']}) ...", end=" ", flush=True)
        _max_retries = 3
        for attempt in range(_max_retries):
            try:
                metric.measure(test_case)
                score = metric.score
                reason = metric.reason or ""
                passed = score >= cfg["threshold"]
                if not passed:
                    all_passed = False
                status = "PASS" if passed else "FAIL"
                print(f"{status}  (score: {score:.3f})")
                if not passed:
                    print(f"  Reason: {reason}")
                results.append({"metric": cfg["name"], "id": cfg["id"], "threshold": cfg["threshold"], "score": score, "passed": passed, "reason": reason})
                break
            except Exception as exc:
                exc_str = str(exc)
                is_rate_limit = "429" in exc_str or "RESOURCE_EXHAUSTED" in exc_str
                if is_rate_limit and attempt < _max_retries - 1:
                    delay_match = re.search(r"retry[^\d]*(\d+\.?\d*)\s*s", exc_str, re.IGNORECASE)
                    wait_s = float(delay_match.group(1)) + 2 if delay_match else 35
                    print(f"  [rate-limited, waiting {wait_s:.0f}s before retry {attempt + 2}/{_max_retries}]", end=" ", flush=True)
                    time.sleep(wait_s)
                else:
                    print(f"ERROR  ({exc_str[:120]})")
                    all_passed = False
                    results.append({"metric": cfg["name"], "id": cfg["id"], "threshold": cfg["threshold"], "score": None, "passed": False, "reason": exc_str})
                    break

    print(f"\n{'='*70}")
    print("SUMMARY")
    print(f"{'='*70}")
    passed_count = sum(1 for r in results if r["passed"])
    print(f"  {passed_count}/{len(results)} metrics passed\n")
    for r in results:
        score_str = f"{r['score']:.3f}" if r["score"] is not None else "N/A"
        flag = "v" if r["passed"] else "x"
        print(f"  {flag}  {r['metric']:<32} score={score_str}  threshold>={r['threshold']}")
    must_fix = [r for r in results if not r["passed"]]
    if must_fix:
        print(f"\nMUST-FIX ({len(must_fix)} metric(s) below threshold):")
        for r in must_fix:
            print(f"  [{r['metric']}] {r['reason']}")
    print(f"\nOverall verdict: {'PASS' if all_passed else 'FAIL — fix must-fix items before merge'}")
    print(f"{'='*70}\n")
    if report_json:
        report = {"overall_passed": all_passed, "model": model, "framework": framework, "metrics": results}
        Path(report_json).write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(f"JSON report written to: {report_json}")
    return all_passed


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="AI meta-evaluation of generated test code using DeepEval G-Eval.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--tests", required=True, metavar="PATH")
    ac_group = parser.add_mutually_exclusive_group()
    ac_group.add_argument("--ac", metavar="TEXT", default="")
    ac_group.add_argument("--ac-file", metavar="FILE")
    parser.add_argument("--spec", metavar="TEXT", default="")
    parser.add_argument("--adapter", metavar="FRAMEWORK", default=None)
    parser.add_argument("--model", default=None, metavar="MODEL")
    parser.add_argument("--report-json", metavar="FILE", default=None)
    parser.add_argument("--skip", metavar="METRIC_ID", action="append", default=[])
    parser.add_argument("--config", metavar="FILE", default=None)
    return parser


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()
    cfg = {}
    if load_config is not None:
        try:
            cfg = load_config(args.config)
        except Exception:
            pass
    framework = args.adapter or (cfg.get("test_framework", {}).get("name") if cfg else None) or "pytest"
    model = args.model or (cfg.get("deepeval", {}).get("default_model") if cfg else None) or "groq/llama-3.1-70b-versatile"
    file_pattern = cfg.get("test_framework", {}).get("file_pattern", "**/*_test.*") if cfg else "**/*_test.*"
    try:
        test_content = _load_test_content(args.tests, file_pattern)
    except ValueError as exc:
        print(f"ERROR loading tests: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
    ac_text = _load_ac(args.ac or None, args.ac_file or None)
    all_passed = run_evaluation(
        test_content=test_content, ac_text=ac_text, spec_text=args.spec,
        model=model, report_json=args.report_json, framework=framework, skip_ids=args.skip,
    )
    raise SystemExit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
