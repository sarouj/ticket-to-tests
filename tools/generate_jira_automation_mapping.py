#!/usr/bin/env python3
"""
Build jira_automation_mapping.json: test node ID -> Jira issue key + optional Zephyr testcase key.

Reads from team_config.yaml:
    test_dir_root              — Root directory to scan
    test_framework.name        — Framework name
    test_framework.file_pattern — Glob pattern

Usage:
    python ~/.agents/skills/ticket-to-tests/tools/generate_jira_automation_mapping.py
    python ~/.agents/skills/ticket-to-tests/tools/generate_jira_automation_mapping.py \\
        --tests-root tests --output jira_automation_mapping.json
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator, Optional

_tools_dir = Path(__file__).parent
sys.path.insert(0, str(_tools_dir))
try:
    from team_config import load_config, framework_name as _framework_name
except ImportError:
    def load_config(path=None):
        return {}
    def _framework_name(cfg):
        return "pytest"

JIRA_KEY_RE = re.compile(r"\b([A-Z][A-Z0-9_]{1,9}-\d+)\b")


def _str_arg(node: ast.AST) -> Optional[str]:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def _issue_key_from_url(url: str) -> Optional[str]:
    m = re.search(r"/browse/([A-Z][A-Z0-9_]{1,9}-\d+)", url, re.I)
    if m:
        return m.group(1).upper()
    m2 = JIRA_KEY_RE.search(url)
    return m2.group(1).upper() if m2 else None


def _decorator_name(dec: ast.AST) -> Optional[str]:
    if isinstance(dec, ast.Call):
        dec = dec.func
    if isinstance(dec, ast.Attribute):
        parts = []
        cur: ast.AST = dec
        while isinstance(cur, ast.Attribute):
            parts.append(cur.attr)
            cur = cur.value
        if isinstance(cur, ast.Name):
            parts.append(cur.id)
        parts.reverse()
        return ".".join(parts) if parts else None
    if isinstance(dec, ast.Name):
        return dec.id
    return None


def _extract_jira_from_decorators(decorators: list[ast.AST]) -> tuple[Optional[str], Optional[str]]:
    jira_mark: Optional[str] = None
    allure_issue: Optional[str] = None
    for dec in decorators:
        name = _decorator_name(dec)
        if not name:
            continue
        if name in ("pytest.mark.jira", "mark.jira") or name.endswith(".jira"):
            if isinstance(dec, ast.Call) and dec.args:
                raw = _str_arg(dec.args[0])
                if raw:
                    jm = JIRA_KEY_RE.search(raw)
                    jira_mark = jm.group(1).upper() if jm else raw.strip().upper()
        if name == "allure.issue":
            if isinstance(dec, ast.Call) and dec.args:
                url = _str_arg(dec.args[0])
                if url:
                    k = _issue_key_from_url(url)
                    if k:
                        allure_issue = k
    return jira_mark, allure_issue


def _iter_test_functions(tree: ast.AST) -> Iterator[ast.FunctionDef]:
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test_"):
            yield node  # type: ignore[misc]


@dataclass
class TestRef:
    rel_path: str
    func_name: str
    jira_issue_key: str
    source: str


def _parse_python_file(path: Path, tests_root: Path) -> list[TestRef]:
    base = tests_root.resolve()
    rel_from_tests = path.resolve().relative_to(base)
    nodeid_path = f"tests/{rel_from_tests.as_posix()}"
    try:
        src = path.read_text(encoding="utf-8", errors="replace")
        tree = ast.parse(src, filename=str(path))
    except SyntaxError:
        return []
    out: list[TestRef] = []
    for fn in _iter_test_functions(tree):
        jira_m, allure_m = _extract_jira_from_decorators(fn.decorator_list)
        key: Optional[str] = None
        source: str = ""
        if jira_m:
            key, source = jira_m, "pytest_mark_jira"
        elif allure_m:
            key, source = allure_m, "allure_issue"
        if not key:
            continue
        out.append(TestRef(rel_path=nodeid_path, func_name=fn.name, jira_issue_key=key, source=source))
    return out


def _parse_generic_file(path: Path, tests_root: Path, framework: str) -> list[TestRef]:
    base = tests_root.resolve()
    try:
        rel_from_tests = path.resolve().relative_to(base)
    except ValueError:
        rel_from_tests = path.name
    nodeid_path = str(rel_from_tests)
    try:
        src = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return []
    test_patterns = [
        r'\btest\s+["\']([^"\']+)["\']',
        r'\bit\s+["\']([^"\']+)["\']',
        r'\bfunc\s+(Test\w+)\s*\(',
        r'\bvoid\s+(test\w+)\s*\(',
        r'def\s+(test_\w+)\s*\(',
    ]
    jira_keys = JIRA_KEY_RE.findall(src)
    if not jira_keys:
        return []
    out: list[TestRef] = []
    func_names: list[str] = []
    for pattern in test_patterns:
        func_names.extend(re.findall(pattern, src))
    for func_name in func_names:
        key_match = JIRA_KEY_RE.search(src[max(0, src.find(func_name) - 200):src.find(func_name) + 500])
        if key_match:
            out.append(TestRef(rel_path=nodeid_path, func_name=func_name,
                               jira_issue_key=key_match.group(1).upper(), source="annotation"))
    return out


def _load_zephyr_index(zephyr_log: Path) -> dict[str, str]:
    if not zephyr_log.is_file():
        return {}
    try:
        data = json.loads(zephyr_log.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}
    if not isinstance(data, list):
        return {}
    index: dict[str, str] = {}
    for row in data:
        if not isinstance(row, dict):
            continue
        fn = row.get("functionName")
        resp = row.get("response") or {}
        zkey = resp.get("key")
        if isinstance(fn, str) and isinstance(zkey, str):
            index[fn] = zkey
    return index


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate Jira \u2194 test automation mapping.")
    parser.add_argument("--tests-root", type=Path, default=None)
    parser.add_argument("--output", type=Path, default=Path("jira_automation_mapping.json"))
    parser.add_argument("--zephyr-log", type=Path, default=None)
    parser.add_argument("--config", default=None)
    args = parser.parse_args()

    cfg = load_config(args.config)
    framework = _framework_name(cfg) or "pytest"
    tests_root_default = cfg.get("test_dir_root") if cfg else None

    tests_root_str = str(args.tests_root) if args.tests_root else tests_root_default or "tests"
    tests_root = Path(tests_root_str).resolve()
    if not tests_root.is_dir():
        print(f"Tests root not found: {tests_root}", file=sys.stderr)
        return 1

    zephyr_index: dict[str, str] = {}
    if args.zephyr_log:
        zephyr_index = _load_zephyr_index(args.zephyr_log.resolve())

    entries: list[dict[str, Any]] = []
    if framework in ("pytest", "python"):
        for py in sorted(tests_root.rglob("*_test.py")):
            if "__pycache__" in py.parts:
                continue
            for ref in _parse_python_file(py, tests_root):
                nodeid = f"{ref.rel_path}::{ref.func_name}"
                zkey = zephyr_index.get(ref.func_name)
                entries.append({"nodeid": nodeid, "jira_issue_key": ref.jira_issue_key,
                                 "zephyr_testcase_key": zkey, "source": ref.source})
    else:
        ext_map = {
            "jest": [".spec.ts", ".spec.js", ".test.ts", ".test.js"],
            "mocha": [".spec.js", ".test.js"],
            "junit": [".java"],
            "go-test": ["_test.go"],
            "rspec": ["_spec.rb"],
        }
        extensions = ext_map.get(framework, [".py"])
        for ext in extensions:
            for fp in sorted(tests_root.rglob(f"*{ext}")):
                for ref in _parse_generic_file(fp, tests_root, framework):
                    nodeid = f"{ref.rel_path}::{ref.func_name}"
                    zkey = zephyr_index.get(ref.func_name)
                    entries.append({"nodeid": nodeid, "jira_issue_key": ref.jira_issue_key,
                                     "zephyr_testcase_key": zkey, "source": ref.source})

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "tests_root": str(tests_root),
        "framework": framework,
        "entries": entries,
    }
    args.output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Wrote {len(entries)} mapped test(s) to {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
