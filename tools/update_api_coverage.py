#!/usr/bin/env python3
"""
Regenerate api_coverage_report.json by mapping test files to OpenAPI spec endpoints.

Reads from team_config.yaml:
    openapi.spec_path   — Path to the OpenAPI YAML spec
    test_dir_root       — Root directory to scan for test files
    test_framework.file_pattern — Glob pattern for test files

Exit code:
    0 — coverage count is >= baseline
    1 — covered count regressed below baseline
    2 — invocation error
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML is not installed.\nInstall it with: pip install pyyaml", file=sys.stderr)
    raise SystemExit(2)

_tools_dir = Path(__file__).parent
sys.path.insert(0, str(_tools_dir))
try:
    from team_config import load_config
except ImportError:
    def load_config(path=None):
        return {}


def load_spec_endpoints(spec_path: Path) -> list[dict[str, Any]]:
    with spec_path.open(encoding="utf-8") as fh:
        spec = yaml.safe_load(fh)
    endpoints = []
    paths: dict = spec.get("paths", {})
    for path, path_item in paths.items():
        if not isinstance(path_item, dict):
            continue
        for method in ("get", "post", "put", "patch", "delete", "head", "options"):
            operation = path_item.get(method)
            if not operation:
                continue
            responses = list((operation.get("responses") or {}).keys())
            parameters = [p.get("name", "") for p in (operation.get("parameters") or []) if isinstance(p, dict)]
            endpoints.append({
                "endpoint": path, "method": method.upper(), "covered": False,
                "parameters": parameters, "responses": [str(r) for r in responses],
            })
    return endpoints


_ACTION_CALL_RE = re.compile(r"\b([a-z][a-z0-9_]+)\s*\(", re.IGNORECASE)


def _path_segments(path: str) -> list[str]:
    return [seg for seg in path.split("/") if seg and not seg.startswith("{")]


def _collect_test_tokens(test_root: Path, file_extensions: list[str]) -> set[str]:
    tokens: set[str] = set()
    if not file_extensions:
        file_extensions = [".py", ".ts", ".js", ".java", ".go", ".rb"]
    for ext in file_extensions:
        for test_file in test_root.rglob(f"*{ext}"):
            try:
                source = test_file.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            for m in _ACTION_CALL_RE.finditer(source):
                tokens.add(m.group(1).lower())
            for dq in re.findall(r'"""(.*?)"""', source, re.DOTALL):
                tokens.update(w.lower() for w in re.split(r"\W+", dq) if len(w) > 3)
            for comment in re.findall(r"(?://|#)\s*(.*)", source):
                tokens.update(w.lower() for w in re.split(r"\W+", comment) if len(w) > 3)
    return tokens


def _endpoint_is_covered(endpoint: dict, tokens: set[str]) -> bool:
    path: str = endpoint["endpoint"]
    segments = _path_segments(path)
    if not segments:
        return False
    for seg in segments:
        seg_lower = seg.lower()
        if seg_lower in tokens:
            return True
        for token in tokens:
            if seg_lower in token or token in seg_lower:
                return True
    return False


def main() -> None:
    parser = argparse.ArgumentParser(description="Regenerate api_coverage_report.json.")
    parser.add_argument("--spec", default=None, metavar="PATH",
        help="Path to the OpenAPI YAML spec. Defaults to team_config.yaml \u2192 openapi.spec_path.")
    parser.add_argument("--tests", default=None, metavar="DIR",
        help="Root directory to scan. Defaults to team_config.yaml \u2192 test_dir_root.")
    parser.add_argument("--output", default="api_coverage_report.json", metavar="FILE")
    parser.add_argument("--no-regression-check", action="store_true")
    parser.add_argument("--config", default=None)
    args = parser.parse_args()

    cfg = load_config(args.config)
    spec_default = cfg.get("openapi", {}).get("spec_path") if cfg else None
    tests_default = cfg.get("test_dir_root") if cfg else None
    file_pattern = cfg.get("test_framework", {}).get("file_pattern", "**/*_test.*") if cfg else "**/*_test.*"

    spec_path_str = args.spec or spec_default
    tests_dir_str = args.tests or tests_default

    if not spec_path_str:
        print("ERROR: No OpenAPI spec path. Set --spec or team_config.yaml \u2192 openapi.spec_path.", file=sys.stderr)
        raise SystemExit(2)
    if not tests_dir_str:
        print("ERROR: No tests directory. Set --tests or team_config.yaml \u2192 test_dir_root.", file=sys.stderr)
        raise SystemExit(2)

    spec_path = Path(spec_path_str)
    if not spec_path.exists():
        print(f"ERROR: spec not found: {spec_path}", file=sys.stderr)
        raise SystemExit(2)

    tests_root = Path(tests_dir_str)
    if not tests_root.is_dir():
        print(f"ERROR: tests directory not found: {tests_root}", file=sys.stderr)
        raise SystemExit(2)

    ext_match = re.search(r"\*(\.[a-z]+)$", file_pattern)
    extensions = [ext_match.group(1)] if ext_match else [".py", ".ts", ".js", ".java", ".go", ".rb"]

    output_path = Path(args.output)
    baseline_covered = 0
    if output_path.exists() and not args.no_regression_check:
        try:
            old_data = json.loads(output_path.read_text(encoding="utf-8"))
            baseline_covered = sum(1 for e in old_data if e.get("covered"))
        except (json.JSONDecodeError, TypeError):
            pass

    print(f"Loading spec:  {spec_path}")
    endpoints = load_spec_endpoints(spec_path)
    print(f"  {len(endpoints)} endpoint+method pairs found")

    print(f"Scanning tests: {tests_root}")
    tokens = _collect_test_tokens(tests_root, extensions)
    print(f"  {len(tokens)} unique tokens collected")

    for ep in endpoints:
        ep["covered"] = _endpoint_is_covered(ep, tokens)

    new_covered = sum(1 for ep in endpoints if ep["covered"])
    total = len(endpoints)
    output_path.write_text(json.dumps(endpoints, indent=2), encoding="utf-8")
    print(f"\nCoverage: {new_covered}/{total} endpoints covered")
    print(f"Report written to: {output_path}")

    if not args.no_regression_check and new_covered < baseline_covered:
        print(f"\nREGRESSION: covered count dropped from {baseline_covered} to {new_covered}.", file=sys.stderr)
        raise SystemExit(1)
    if not args.no_regression_check:
        print("Coverage check passed.")


if __name__ == "__main__":
    main()
