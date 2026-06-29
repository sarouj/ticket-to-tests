#!/usr/bin/env python3
"""
create_tests_in_zephyr.py

Parses test files and creates Zephyr test cases in Jira using the Zephyr Scale API.
Framework-agnostic: detects Allure metadata from Python test files; for other frameworks,
relies on TEST_METADATA tags parsed from the file.

Reads configuration from team_config.yaml in CWD:
  jira.url              - Jira base URL
  jira.project_key      - Jira project key
  jira.component        - Optional Jira component
  zephyr.epic_folder_map - Maps epic labels to Zephyr folder names

Reads credentials from .cursor/mcp.json:
  JIRA_USERNAME         - Jira email
  JIRA_API_TOKEN        - Jira API token

Usage:
    python ~/.agents/skills/ticket-to-tests/tools/create_tests_in_zephyr.py \\
        --test-dir tests/items/create_item/ \\
        [--link-issue PROJ-123] \\
        [--dry-run]
"""

import os
import re
import ast
import json
import argparse
import sys
import datetime

import requests
from pathlib import Path
from dataclasses import dataclass
from typing import List, Optional, Dict, Any, Tuple

_tools_dir = Path(__file__).parent
sys.path.insert(0, str(_tools_dir))
from team_config import load_config, jira_url as _jira_url, project_key as _project_key, jira_component as _jira_component


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
class TestCase:
    name: str
    title: str
    description: Optional[str]
    epic: Optional[str]
    feature: Optional[str]
    story: Optional[str]
    labels: List[str]
    file_path: str
    component: Optional[str] = None
    fixtures: List[str] = None
    steps: List[str] = None


class TestExtractor:
    def __init__(self, test_dir: str, file_pattern: str = "**/*_test.*"):
        self.test_dir = test_dir
        self.file_pattern = file_pattern

    def find_test_files(self) -> List[str]:
        test_files = []
        for root, _, files in os.walk(self.test_dir):
            for file in files:
                fp = os.path.join(root, file)
                if any(file.endswith(ext) for ext in ("_test.py", ".spec.ts", ".spec.js", "_test.go", "_spec.rb", ".test.js")):
                    test_files.append(fp)
                    print(f"Found test file: {fp}")
        print(f"Total test files found: {len(test_files)}")
        return test_files

    def extract_tests(self) -> List[TestCase]:
        test_cases = []
        for file_path in self.find_test_files():
            test_cases.extend(self.extract_tests_from_file(file_path))
        return test_cases

    def extract_allure_attribute(self, node, attr_name: str) -> Optional[str]:
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Attribute):
                if (decorator.func.attr == attr_name and
                        isinstance(decorator.func.value, ast.Name) and
                        decorator.func.value.id == "allure"):
                    if decorator.args:
                        arg = decorator.args[0]
                        if isinstance(arg, ast.Str):
                            return arg.s
                        elif isinstance(arg, ast.Constant):
                            return arg.value
                        elif isinstance(arg, ast.Attribute):
                            return arg.attr
                        elif isinstance(arg, ast.Name):
                            return arg.id
                        else:
                            try:
                                return ast.unparse(arg)
                            except Exception:
                                return str(arg)
        return None

    def extract_allure_steps(self, func_node) -> List[str]:
        steps = []
        for node in ast.walk(func_node):
            if not isinstance(node, ast.With):
                continue
            for item in node.items:
                ctx = item.context_expr
                if not isinstance(ctx, ast.Call):
                    continue
                func = ctx.func
                if (isinstance(func, ast.Attribute) and func.attr == "step" and
                        isinstance(func.value, ast.Name) and func.value.id == "allure" and ctx.args):
                    arg = ctx.args[0]
                    if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                        steps.append(arg.value)
                    elif isinstance(arg, ast.Str):
                        steps.append(arg.s)
        return steps

    def extract_tests_from_file(self, file_path: str) -> List[TestCase]:
        if not file_path.endswith(".py"):
            return self._extract_generic(file_path)
        try:
            with open(file_path, "r") as f:
                file_content = f.read()
            tree = ast.parse(file_content)
            test_cases = []
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    epic = self.extract_allure_attribute(node, "epic")
                    feature = self.extract_allure_attribute(node, "feature")
                    story = self.extract_allure_attribute(node, "story")
                    component = self.extract_allure_attribute(node, "component")
                    for child in node.body:
                        if isinstance(child, ast.FunctionDef) and child.name.startswith("test_"):
                            title = self.extract_allure_attribute(child, "title")
                            if not title:
                                title = child.name.replace("test_", "").replace("_", " ").title()
                            docstring = ast.get_docstring(child) or ""
                            method_component = self.extract_allure_attribute(child, "component")
                            final_component = method_component if method_component else component
                            fixtures = []
                            if hasattr(child, "args") and hasattr(child.args, "args"):
                                for arg in child.args.args:
                                    if arg.arg != "self":
                                        fixtures.append(arg.arg)
                            steps = self.extract_allure_steps(child)
                            test_cases.append(TestCase(
                                name=child.name, title=title, description=docstring,
                                epic=epic, feature=feature, story=story, labels=["test"],
                                file_path=file_path, component=final_component,
                                fixtures=fixtures, steps=steps or None,
                            ))
            return test_cases
        except SyntaxError:
            print(f"Error parsing file: {file_path}")
            return []
        except Exception as e:
            print(f"Error extracting tests from {file_path}: {e}")
            return []

    def _extract_generic(self, file_path: str) -> List[TestCase]:
        test_cases = []
        try:
            content = Path(file_path).read_text(encoding="utf-8", errors="ignore")
            patterns = [
                r'\btest\s+["\']([^"\']+)["\']',
                r'\bit\s+["\']([^"\']+)["\']',
                r'\bfunc\s+(Test\w+)\s*\(',
                r'\bvoid\s+(test\w+)\s*\(',
                r'def\s+(test_\w+)\s*\(',
            ]
            found = []
            for pattern in patterns:
                found.extend(re.findall(pattern, content))
            for name in found:
                title = re.sub(r'[_\-]', ' ', name).strip()
                if title.lower().startswith("test "):
                    title = title[5:]
                test_cases.append(TestCase(
                    name=name, title=title.title(), description=None,
                    epic=None, feature=None, story=None,
                    labels=["test"], file_path=file_path,
                ))
        except Exception as e:
            print(f"Error extracting generic tests from {file_path}: {e}")
        return test_cases


class JiraZephyrClient:
    def __init__(self, jira_url: str, username: str, api_token: str, project_key: str,
                 epic_folder_map: Dict[str, str], default_label: str = "test",
                 component: str = "", issue_links: List[int] = None):
        self.jira_url = jira_url.rstrip("/")
        self.auth = (username, api_token)
        self.project_key = project_key
        self.headers = {"Accept": "application/json", "Content-Type": "application/json"}
        self.epic_folder_map = epic_folder_map
        self.default_label = default_label
        self.component_str = component
        self.issue_links = issue_links or []
        self.issue_link_keys: List[str] = []
        self.created_keys: List[str] = []
        self.json_log_file = "zephyr_responses.json"
        self._folder_id_cache: Dict[str, Optional[int]] = {}
        self._project_id_cache: Optional[int] = None
        self._ensure_valid_json_log()

    def _ensure_valid_json_log(self):
        try:
            if not os.path.exists(self.json_log_file):
                with open(self.json_log_file, "w") as f:
                    json.dump([], f)
            else:
                try:
                    with open(self.json_log_file, "r") as f:
                        data = json.load(f)
                    if not isinstance(data, list):
                        with open(self.json_log_file, "w") as f:
                            json.dump([], f)
                except json.JSONDecodeError:
                    with open(self.json_log_file, "w") as f:
                        json.dump([], f)
        except Exception as e:
            print(f"Error initializing JSON log: {e}")

    def resolve_issue_key(self, issue_key: str) -> int:
        url = f"{self.jira_url}/rest/api/2/issue/{issue_key}?fields=id"
        response = requests.get(url, auth=self.auth, headers=self.headers)
        if response.status_code == 200:
            return int(response.json()["id"])
        raise RuntimeError(f"Failed to resolve issue key '{issue_key}': {response.status_code}")

    def _get_project_id(self) -> Optional[int]:
        if self._project_id_cache is not None:
            return self._project_id_cache
        url = f"{self.jira_url}/rest/tests/1.0/project?projectKey={self.project_key}"
        resp = requests.get(url, auth=self.auth, headers=self.headers)
        if resp.status_code == 200:
            pid = resp.json().get("id")
            if pid:
                self._project_id_cache = int(pid)
                return self._project_id_cache
        url2 = f"{self.jira_url}/rest/api/2/project/{self.project_key}"
        resp2 = requests.get(url2, auth=self.auth, headers=self.headers)
        if resp2.status_code == 200:
            self._project_id_cache = int(resp2.json().get("id", 0))
            return self._project_id_cache
        return None

    def _get_folder_id(self, folder_name: str) -> Optional[int]:
        if folder_name in self._folder_id_cache:
            return self._folder_id_cache[folder_name]
        project_id = self._get_project_id()
        if not project_id:
            return None
        url = f"{self.jira_url}/rest/tests/1.0/project/{project_id}/testcasefolders"
        resp = requests.get(url, auth=self.auth, headers=self.headers)
        if resp.status_code == 200:
            folders = resp.json() if isinstance(resp.json(), list) else resp.json().get("folders", [])
            for folder in folders:
                if isinstance(folder, dict) and folder.get("name") == folder_name:
                    fid = int(folder.get("id", 0))
                    self._folder_id_cache[folder_name] = fid
                    return fid
        self._folder_id_cache[folder_name] = None
        return None

    def verify_and_fix_issue_links(self) -> None:
        if not self.issue_link_keys or not self.created_keys:
            return
        print(f"\n--- Issue-link validation for {len(self.created_keys)} created test cases ---")
        already_linked, fixed, failed = [], [], []
        for tc_key in self.created_keys:
            get_resp = requests.get(f"{self.jira_url}/rest/atm/1.0/testcase/{tc_key}",
                                    auth=self.auth, headers=self.headers)
            if get_resp.status_code != 200:
                failed.append(tc_key)
                continue
            existing_links = get_resp.json().get("issueLinks") or []
            missing = [k for k in self.issue_link_keys if k not in existing_links]
            if not missing:
                already_linked.append(tc_key)
                continue
            merged = list(set(existing_links) | set(self.issue_link_keys))
            put_resp = requests.put(f"{self.jira_url}/rest/atm/1.0/testcase/{tc_key}",
                                    auth=self.auth, headers=self.headers, json={"issueLinks": merged})
            if put_resp.status_code == 200:
                fixed.append(tc_key)
            else:
                failed.append(tc_key)
        print(f"Issue link verification: {len(already_linked)} already linked, "
              f"{len(fixed)} fixed, {len(failed)} failed.\n")

    def create_test_case(self, test_case: TestCase) -> Dict[str, Any]:
        print(f"Processing test case: {test_case.title}")
        labels = [re.sub(r"[^\w]", "_", str(l)).lower() for l in (test_case.labels or []) if l]
        if not labels:
            labels = [self.default_label]

        folder_id = None
        epic_name = None
        if test_case.epic:
            epic_name = test_case.epic.split(".")[-1] if "." in test_case.epic else test_case.epic
            folder_name = self.epic_folder_map.get(epic_name.upper()) or self.epic_folder_map.get(epic_name)
            if folder_name:
                folder_id = self._get_folder_id(folder_name)

        project_id = self._get_project_id()
        objective = test_case.description or test_case.title
        precondition = "None"
        if test_case.fixtures:
            precondition = "Create test data with test setup helpers: " + ", ".join(test_case.fixtures)

        if test_case.steps:
            test_script = {"stepByStepScript": {"steps": [{"description": s, "testData": "", "expectedResult": "Validation successful"} for s in test_case.steps]}}
        else:
            test_script = {"plainTextScript": {"text": objective}}

        zephyr_data: Dict[str, Any] = {
            "name": test_case.title, "objective": objective,
            "precondition": precondition, "labels": labels, "testScript": test_script,
        }
        if project_id:
            zephyr_data["projectId"] = project_id
        if folder_id:
            zephyr_data["folderId"] = folder_id
        if self.component_str:
            zephyr_data["componentId"] = self.component_str
        if self.issue_links:
            zephyr_data["issueLinks"] = self.issue_links

        response = requests.post(f"{self.jira_url}/rest/tests/1.0/testcase",
                                 auth=self.auth, headers=self.headers, json=zephyr_data)
        if response.status_code in (200, 201):
            response_data = response.json()
            tc_key = response_data.get("key", "Unknown key")
            print(f"Created test case in Zephyr: {tc_key}: {test_case.title}")
            if tc_key and tc_key != "Unknown key":
                self.created_keys.append(tc_key)
            return response_data
        else:
            print(f"Failed to create test case: {test_case.title}")
            print(f"Status: {response.status_code}, Response: {response.text[:500]}")
            return {}


def main():
    parser = argparse.ArgumentParser(description="Extract test cases and export to Jira/Zephyr")
    parser.add_argument("--test-dir")
    parser.add_argument("--test-file", action="append", default=[])
    parser.add_argument("--jira-url", default=None)
    parser.add_argument("--username", default=None)
    parser.add_argument("--api-token", default=None)
    parser.add_argument("--project-key", default=None)
    parser.add_argument("--output")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--link-issue", action="append", default=[])
    parser.add_argument("--config", default=None)
    args = parser.parse_args()

    if not args.test_file and not args.test_dir:
        parser.error("Either --test-dir or --test-file must be provided")

    cfg = load_config(args.config)
    resolved_jira_url = (args.jira_url or _jira_url(cfg)).rstrip("/")
    resolved_project_key = args.project_key or _project_key(cfg)
    resolved_component = _jira_component(cfg)
    epic_folder_map = cfg.get("zephyr", {}).get("epic_folder_map", {})
    default_label = resolved_project_key.lower() if resolved_project_key else "test"

    if not resolved_jira_url:
        parser.error("--jira-url or team_config.yaml -> jira.url is required")
    if not resolved_project_key:
        parser.error("--project-key or team_config.yaml -> jira.project_key is required")

    mcp_user, mcp_token = _read_mcp_credentials()
    username = args.username or mcp_user
    api_token = args.api_token or mcp_token
    if not args.dry_run and (not username or not api_token):
        parser.error("Jira credentials not found. Set in .cursor/mcp.json or pass --username / --api-token.")

    file_pattern = cfg.get("test_framework", {}).get("file_pattern", "**/*_test.*")
    extractor = TestExtractor(args.test_dir or (os.path.dirname(args.test_file[0]) if args.test_file else "."), file_pattern)

    if args.test_file:
        test_cases = []
        for fp in args.test_file:
            test_cases.extend(extractor.extract_tests_from_file(fp))
    else:
        test_cases = extractor.extract_tests()

    print(f"Found {len(test_cases)} test cases")

    if args.output:
        with open(args.output, "w") as f:
            json.dump([vars(tc) for tc in test_cases], f, indent=2)
        print(f"Test cases saved to {args.output}")

    if args.dry_run:
        print("\n--- DRY RUN: Test cases that would be created ---")
        for tc in test_cases:
            epic_label = tc.epic or "(no epic)"
            folder = epic_folder_map.get((tc.epic or "").upper(), "(default folder)")
            print(f"  [{epic_label} -> {folder}] {tc.title}")
        print(f"\nTotal: {len(test_cases)} test cases would be created in {resolved_project_key}")
        return 0

    jira_client = JiraZephyrClient(
        jira_url=resolved_jira_url, username=username, api_token=api_token,
        project_key=resolved_project_key, epic_folder_map=epic_folder_map,
        default_label=default_label, component=resolved_component,
    )
    if args.link_issue:
        resolved_ids = [jira_client.resolve_issue_key(key) for key in args.link_issue]
        jira_client.issue_links = resolved_ids
        jira_client.issue_link_keys = list(args.link_issue)
    for test_case in test_cases:
        jira_client.create_test_case(test_case)
    if args.link_issue:
        jira_client.verify_and_fix_issue_links()
    return 0


if __name__ == "__main__":
    sys.exit(main())
