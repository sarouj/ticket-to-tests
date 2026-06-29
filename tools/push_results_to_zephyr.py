#!/usr/bin/env python3
"""
Push test results to Zephyr Scale via the automation execution API.

Reads project configuration from team_config.yaml in CWD.
Credentials are read from .cursor/mcp.json (JIRA_USERNAME, JIRA_API_TOKEN).

Usage:
    python ~/.agents/skills/ticket-to-tests/tools/push_results_to_zephyr.py \\
        --results-file test-results.xml \\
        --zephyr-log zephyr_responses.json \\
        [--results-format junit-xml]       \\
        [--cycle-name "Feature - QA - Sprint 42"] \\
        [--key-range PROJECT-T100:PROJECT-T200] \\
        [--auto-create] \\
        [--dry-run]
"""

import argparse
import io
import json
import os
import sys
import xml.etree.ElementTree as ET
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import requests

_tools_dir = Path(__file__).parent
sys.path.insert(0, str(_tools_dir))
from team_config import load_config, jira_url as _jira_url, project_key as _project_key


def _read_mcp_credentials() -> Tuple[Optional[str], Optional[str]]:
    for search_dir in [Path.cwd(), Path.home()]:
        mcp_path = search_dir / ".cursor" / "mcp.json"
        if mcp_path.is_file():
            try:
                data = json.loads(mcp_path.read_text())
                env = data.get("mcpServers", {}).get("mcp-atlassian", {}).get("env", {})
                return env.get("JIRA_USERNAME"), env.get("JIRA_API_TOKEN")
            except Exception:
                pass
    return None, None


@dataclass
class TestResult:
    classname: str
    func_name: str
    duration_ms: int
    status: str
    message: Optional[str] = None


STATUS_MAP = {"pass": "Pass", "fail": "Fail", "error": "Fail", "skip": "Not Executed"}


def parse_junit_xml(xml_path: str) -> List[TestResult]:
    tree = ET.parse(xml_path)
    root = tree.getroot()
    results = []
    for tc in root.iter("testcase"):
        classname = tc.get("classname", "")
        name = tc.get("name", "")
        time_s = float(tc.get("time", "0"))
        failure = tc.find("failure")
        error = tc.find("error")
        skipped = tc.find("skipped")
        if failure is not None:
            status, message = "fail", failure.get("message", "")
        elif error is not None:
            status, message = "error", error.get("message", "")
        elif skipped is not None:
            status, message = "skip", skipped.get("message", "")
        else:
            status, message = "pass", None
        results.append(TestResult(
            classname=classname, func_name=name,
            duration_ms=int(time_s * 1000), status=STATUS_MAP[status], message=message,
        ))
    return results


def load_func_set(zephyr_log_path: str, key_range: Optional[Tuple[int, int]] = None) -> set:
    with open(zephyr_log_path) as f:
        data = json.load(f)
    func_set = set()
    for entry in data:
        key = entry["response"]["key"]
        if key_range:
            try:
                key_num = int(key.split("-T")[1])
                lo, hi = key_range
                if key_num < lo or key_num > hi:
                    continue
            except (IndexError, ValueError):
                pass
        func_set.add(entry["functionName"])
    return func_set


def parse_key_range(range_str: str) -> Tuple[int, int]:
    parts = range_str.split(":")
    if len(parts) != 2:
        raise ValueError(f"Key range must be 'PREFIX-Tnnn:PREFIX-Tmmm', got '{range_str}'")
    lo = int(parts[0].split("-T")[1])
    hi = int(parts[1].split("-T")[1])
    return (lo, hi)


def build_automation_json(results: List[TestResult], func_set: set, cycle_name: Optional[str] = None) -> dict:
    executions = []
    unmatched = []
    for r in results:
        if r.func_name not in func_set:
            unmatched.append(r.func_name)
            continue
        execution = {"source": r.func_name, "result": r.status}
        if r.message:
            execution["comment"] = r.message[:2000]
        executions.append(execution)
    payload = {"version": 1, "executions": executions}
    if unmatched:
        print(f"WARNING: {len(unmatched)} test(s) not in zephyr_responses filter:")
        for fn in unmatched[:10]:
            print(f"  - {fn}")
        if len(unmatched) > 10:
            print(f"  ... and {len(unmatched) - 10} more")
    print(f"Matched {len(executions)}/{len(results)} test results")
    return payload


def _try_rename_cycle(jira_url: str, cycle_key: str, new_name: str, auth: tuple) -> bool:
    url = f"{jira_url}/rest/atm/1.0/testrun/{cycle_key}"
    resp = requests.put(url, json={"name": new_name}, auth=auth, headers={"Content-Type": "application/json"})
    return resp.status_code == 200


def upload_results(payload: dict, jira_url: str, username: str, api_token: str,
                   project_key: str, auto_create: bool = False, cycle_name: Optional[str] = None) -> dict:
    json_bytes = json.dumps(payload, indent=2).encode("utf-8")
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("test_result.json", json_bytes)
    zip_buffer.seek(0)
    from urllib.parse import quote
    auto_create_str = "true" if auto_create else "false"
    url = f"{jira_url}/rest/atm/1.0/automation/execution/{project_key}?autoCreateTestCases={auto_create_str}"
    if cycle_name:
        url += f"&testCycleName={quote(cycle_name)}"
    print(f"Uploading to: {url}")
    print(f"  Executions: {len(payload['executions'])}")
    response = requests.post(url, files={"file": ("test_result.zip", zip_buffer, "application/zip")},
                             auth=(username, api_token))
    print(f"Response status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        cycle_key = result.get("testCycle", {}).get("key", "")
        cycle_url = result.get("testCycle", {}).get("url", "N/A")
        print(f"Test cycle created: {cycle_key}")
        print(f"URL: {cycle_url}")
        if cycle_name and cycle_key:
            if not _try_rename_cycle(jira_url, cycle_key, cycle_name, auth=(username, api_token)):
                print(f"  NOTE: Could not set cycle name to '{cycle_name}'. Rename manually.")
        return result
    else:
        print(f"ERROR: {response.text[:500]}")
        return {"error": response.text, "status_code": response.status_code}


def main():
    parser = argparse.ArgumentParser(description="Push test results to Zephyr Scale")
    parser.add_argument("--results-file", required=True)
    parser.add_argument("--results-format", default="junit-xml", choices=["junit-xml"])
    parser.add_argument("--zephyr-log", required=True)
    parser.add_argument("--jira-url", default=None)
    parser.add_argument("--username", default=None)
    parser.add_argument("--api-token", default=None)
    parser.add_argument("--project-key", default=None)
    parser.add_argument("--cycle-name")
    parser.add_argument("--key-range")
    parser.add_argument("--auto-create", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--config", default=None)
    args = parser.parse_args()

    cfg = load_config(args.config)
    resolved_jira_url = (args.jira_url or _jira_url(cfg)).rstrip("/")
    resolved_project_key = args.project_key or _project_key(cfg)

    if not resolved_jira_url:
        parser.error("--jira-url or team_config.yaml -> jira.url is required")
    if not resolved_project_key:
        parser.error("--project-key or team_config.yaml -> jira.project_key is required")

    mcp_user, mcp_token = _read_mcp_credentials()
    username = args.username or mcp_user
    api_token = args.api_token or mcp_token
    if not username or not api_token:
        parser.error("Jira credentials not found. Set JIRA_USERNAME and JIRA_API_TOKEN in .cursor/mcp.json")

    print(f"Parsing results: {args.results_file}")
    results = parse_junit_xml(args.results_file)
    print(f"  Found {len(results)} test results")

    key_range = parse_key_range(args.key_range) if args.key_range else None
    func_set = load_func_set(args.zephyr_log, key_range)
    print(f"  Loaded {len(func_set)} function names from zephyr log")

    payload = build_automation_json(results, func_set, args.cycle_name)

    if not payload["executions"]:
        print("ERROR: No matched executions to upload. Aborting.")
        return 1

    if args.dry_run:
        print("\n--- DRY RUN: Automation JSON payload ---")
        print(json.dumps(payload, indent=2)[:3000])
        print(f"\nTotal executions: {len(payload['executions'])}")
        return 0

    result = upload_results(payload, resolved_jira_url, username, api_token,
                            resolved_project_key, auto_create=args.auto_create, cycle_name=args.cycle_name)
    return 1 if "error" in result else 0


if __name__ == "__main__":
    sys.exit(main())
