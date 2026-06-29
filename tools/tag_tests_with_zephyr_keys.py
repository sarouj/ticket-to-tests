#!/usr/bin/env python3
"""
Tag test functions with Zephyr test case decorators using zephyr_responses.json.

Reads jira.url and test_framework.name from team_config.yaml.
Python files: injects @allure.testcase decorators.
Other frameworks: prints annotations for manual insertion.

Usage:
    python ~/.agents/skills/ticket-to-tests/tools/tag_tests_with_zephyr_keys.py \\
        --responses zephyr_responses.json \\
        --test-file tests/items/create_item/create_item_test.py \\
        [--key-range PROJ-T100:PROJ-T200] \\
        [--dry-run]
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

_tools_dir = Path(__file__).parent
sys.path.insert(0, str(_tools_dir))
from team_config import load_config, jira_url as _jira_url, framework_name as _framework_name


def load_mapping(responses_path: str, key_range: Optional[Tuple[int, int]] = None) -> Dict[str, str]:
    with open(responses_path) as f:
        data = json.load(f)
    mapping: Dict[str, str] = {}
    for entry in data:
        key = entry["response"]["key"]
        func = entry["functionName"]
        if key_range:
            try:
                key_num = int(key.split("-T")[1])
                lo, hi = key_range
                if key_num < lo or key_num > hi:
                    continue
            except (IndexError, ValueError):
                pass
        mapping[func] = key
    return mapping


def parse_key_range(range_str: str) -> Tuple[int, int]:
    parts = range_str.split(":")
    if len(parts) != 2:
        raise ValueError(f"Key range must be 'PREFIX-Tnnn:PREFIX-Tmmm', got '{range_str}'")
    lo = int(parts[0].split("-T")[1])
    hi = int(parts[1].split("-T")[1])
    return (lo, hi)


def _build_testcase_url(jira_url: str, zephyr_key: str) -> str:
    return f"{jira_url.rstrip('/')}/secure/Tests.jspa#/testCase/{zephyr_key}"


def tag_python_file(file_path: str, mapping: Dict[str, str], jira_url: str, dry_run: bool = False) -> List[str]:
    path = Path(file_path)
    lines = path.read_text().splitlines(keepends=True)
    tagged: List[str] = []
    new_lines: List[str] = []

    i = 0
    while i < len(lines):
        line = lines[i]
        if re.match(r"\s*@allure\.title\(", line):
            indent = re.match(r"(\s*)", line).group(1)
            func_line_idx = i + 1
            while func_line_idx < len(lines):
                fline = lines[func_line_idx].strip()
                if fline.startswith("def "):
                    break
                func_line_idx += 1
            func_name = None
            if func_line_idx < len(lines):
                m = re.match(r"\s*def\s+(\w+)\s*\(", lines[func_line_idx])
                if m:
                    func_name = m.group(1)
            if func_name and func_name in mapping:
                zephyr_key = mapping[func_name]
                tc_url = _build_testcase_url(jira_url, zephyr_key)
                decorator_line = f'{indent}@allure.testcase("{tc_url}", "{zephyr_key}")\n'
                already_tagged = i > 0 and "@allure.testcase" in lines[i - 1]
                if not already_tagged:
                    new_lines.append(decorator_line)
                    tagged.append(func_name)
        new_lines.append(line)
        i += 1

    if tagged and not dry_run:
        path.write_text("".join(new_lines))
    return tagged


def tag_generic_file(file_path: str, mapping: Dict[str, str], jira_url: str, framework: str, dry_run: bool = False) -> List[str]:
    path = Path(file_path)
    content = path.read_text(encoding="utf-8", errors="ignore")
    tagged = []
    for func_name, zephyr_key in mapping.items():
        if func_name in content:
            tc_url = _build_testcase_url(jira_url, zephyr_key)
            tagged.append(func_name)
            if dry_run:
                print(f"  [{framework}] Add Zephyr annotation to '{func_name}' \u2192 {zephyr_key}")
                print(f"    URL: {tc_url}")
    return tagged


def main():
    parser = argparse.ArgumentParser(description="Tag test functions with Zephyr test case decorators")
    parser.add_argument("--responses", required=True, help="Path to zephyr_responses.json")
    parser.add_argument("--jira-url", default=None, help="Jira base URL (overrides team_config.yaml)")
    parser.add_argument("--test-file", action="append", required=True, help="Test file(s) to tag")
    parser.add_argument("--key-range", help="Only use entries in key range (e.g. PROJ-T100:PROJ-T200)")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be tagged without modifying files")
    parser.add_argument("--config", default=None, help="Path to team_config.yaml")
    args = parser.parse_args()

    cfg = load_config(args.config)
    resolved_jira_url = (args.jira_url or _jira_url(cfg) or "").rstrip("/")
    framework = _framework_name(cfg) or "pytest"

    if not resolved_jira_url:
        parser.error("--jira-url or team_config.yaml \u2192 jira.url is required")

    key_range = parse_key_range(args.key_range) if args.key_range else None
    mapping = load_mapping(args.responses, key_range)
    print(f"Loaded {len(mapping)} function->key mappings from {args.responses}")

    total_tagged = 0
    for fp in args.test_file:
        if fp.endswith(".py"):
            tagged = tag_python_file(fp, mapping, resolved_jira_url, args.dry_run)
        else:
            tagged = tag_generic_file(fp, mapping, resolved_jira_url, framework, args.dry_run)
            if tagged and not args.dry_run:
                print(f"  NOTE: Non-Python file '{fp}' \u2014 add annotations manually for {framework}:")
                for fn in tagged:
                    zephyr_key = mapping[fn]
                    tc_url = _build_testcase_url(resolved_jira_url, zephyr_key)
                    print(f"    {fn} \u2192 {zephyr_key}  {tc_url}")
        if tagged:
            action = "Would tag" if args.dry_run else "Tagged"
            print(f"  {fp}: {action} {len(tagged)} functions")
        else:
            print(f"  {fp}: No functions to tag")
        total_tagged += len(tagged)

    action = "would be tagged" if args.dry_run else "tagged"
    print(f"\nTotal: {total_tagged} functions {action}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
