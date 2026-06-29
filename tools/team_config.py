"""
team_config.py — Configuration loader for the ticket-to-tests skill.

Reads team_config.yaml from the current working directory (project root).
All tools in this skill import this module instead of hardcoding project-specific values.

Usage:
    from team_config import load_config
    cfg = load_config()
    project_key = cfg["jira"]["project_key"]
    runner_cmd  = cfg["test_framework"]["runner_cmd"]

Discovery order:
    1. Path passed explicitly to load_config(path=...)
    2. team_config.yaml in CWD
    3. team_config.yaml in any parent directory up to the filesystem root
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional

try:
    import yaml
except ImportError:
    print(
        "ERROR: PyYAML is not installed.\nInstall it with:  pip install pyyaml",
        file=sys.stderr,
    )
    raise SystemExit(1)


class ConfigNotFoundError(FileNotFoundError):
    """Raised when team_config.yaml cannot be found."""


_DEFAULTS: Dict[str, Any] = {
    "jira": {
        "url": "",
        "project_key": "",
        "component": "",
    },
    "zephyr": {
        "epic_folder_map": {},
    },
    "test_framework": {
        "name": "pytest",
        "runner_cmd": "python -m pytest {test_path} {flags}",
        "results_format": "junit-xml",
        "file_pattern": "**/*_test.*",
    },
    "openapi": {
        "spec_path": "docs/openapi.yaml",
    },
    "context_dir": "context/",
    "test_dir_root": "tests/",
    "auth": {
        "description": "",
        "env_vars": [],
        "verify_cmd": "",
    },
    "deepeval": {
        "default_model": "groq/llama-3.1-70b-versatile",
    },
}


def _deep_merge(base: Dict, override: Dict) -> Dict:
    result = dict(base)
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def _find_config(start: Path) -> Optional[Path]:
    current = start.resolve()
    while True:
        candidate = current / "team_config.yaml"
        if candidate.is_file():
            return candidate
        parent = current.parent
        if parent == current:
            return None
        current = parent


def load_config(path: Optional[str] = None) -> Dict[str, Any]:
    if path:
        config_path = Path(path)
        if not config_path.is_file():
            raise ConfigNotFoundError(f"Config file not found at explicit path: {path}")
    else:
        config_path = _find_config(Path(os.getcwd()))
        if config_path is None:
            raise ConfigNotFoundError(
                "team_config.yaml not found in the current directory or any parent.\n\n"
                "To fix:\n"
                "  1. Copy the template:  cp ~/.agents/skills/ticket-to-tests/templates/team_config.yaml .\n"
                "  2. Fill in your Jira URL, project key, test framework, and spec path.\n"
                "  3. Re-run the tool from your project root.\n\n"
                "See ~/.agents/skills/ticket-to-tests/docs/config-reference.md for all fields."
            )

    try:
        raw = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as exc:
        print(f"ERROR: Failed to parse {config_path}:\n{exc}", file=sys.stderr)
        raise SystemExit(1) from exc

    merged = _deep_merge(_DEFAULTS, raw)
    _validate(merged, config_path)
    return merged


def _validate(cfg: Dict, path: Path) -> None:
    warnings: list[str] = []
    if not cfg["jira"]["url"] or cfg["jira"]["url"] == "https://yourorg.atlassian.net":
        warnings.append("  jira.url — still set to placeholder")
    if not cfg["jira"]["project_key"] or cfg["jira"]["project_key"] == "MYPRJ":
        warnings.append("  jira.project_key — still set to placeholder")
    if not cfg["openapi"]["spec_path"]:
        warnings.append("  openapi.spec_path — not set")
    if warnings:
        print(
            f"\nWARNING: team_config.yaml at {path} has unconfigured required fields:\n"
            + "\n".join(warnings)
            + "\n\nSee ~/.agents/skills/ticket-to-tests/docs/config-reference.md to fix.\n",
            file=sys.stderr,
        )


def jira_url(cfg: Dict) -> str:
    return cfg["jira"]["url"].rstrip("/")

def project_key(cfg: Dict) -> str:
    return cfg["jira"]["project_key"]

def jira_component(cfg: Dict) -> str:
    return cfg["jira"].get("component", "")

def epic_folder_map(cfg: Dict) -> Dict[str, str]:
    return cfg["zephyr"].get("epic_folder_map", {})

def framework_name(cfg: Dict) -> str:
    return cfg["test_framework"]["name"]

def runner_cmd(cfg: Dict) -> str:
    return cfg["test_framework"]["runner_cmd"]

def file_pattern(cfg: Dict) -> str:
    return cfg["test_framework"].get("file_pattern", "**/*_test.*")

def spec_path(cfg: Dict) -> str:
    return cfg["openapi"]["spec_path"]

def deepeval_model(cfg: Dict) -> str:
    return cfg["deepeval"]["default_model"]


if __name__ == "__main__":
    import json
    cfg_path = sys.argv[1] if len(sys.argv) > 1 else None
    try:
        cfg = load_config(cfg_path)
        print(json.dumps(cfg, indent=2))
    except ConfigNotFoundError as e:
        print(f"Config not found: {e}", file=sys.stderr)
        raise SystemExit(1)
