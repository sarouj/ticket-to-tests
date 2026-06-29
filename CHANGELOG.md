# Changelog

All notable changes to the `ticket-to-tests` skill are documented here.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
Versioning follows [Semantic Versioning](https://semver.org/).

---

## [1.0.0] — 2026-06-29 — Generalized release

### Summary

First generalized release. Makes the skill language- and framework-agnostic,
enabling adoption by any team regardless of their testing stack.

### Added

- `team_config.yaml` — per-project configuration template
- `tools/team_config.py` — Python config loader used by all tools
- `ADAPTERS.md` — framework adapter contract (7 slots; pytest complete; JUnit/Jest/Go/RSpec/Mocha stubs)
- `ADOPTING.md` — step-by-step installation and per-project wiring guide
- `templates/team_config.yaml` — annotated configuration template
- `templates/ONBOARDING.template.md` — domain context template
- `templates/ticket-to-tests-skill.mdc` — Cursor routing rule template
- `examples/pytest/` — complete pytest examples (bva, error contract, owasp, etc.)
- `examples/jest/README.md`, `examples/junit/README.md`, `examples/go-test/README.md` — stubs
- `docs/` — Diátaxis documentation structure (quick-start, concepts, config-reference, how-to, reference, troubleshooting, team-integration)
- `CHANGELOG.md` — this file

### Changed

- **SKILL.md**: Added language-agnostic declaration block; removed all file-service and Python-specific references
- **All phase files**: Language-agnostic concept terms throughout; no framework names or syntax
- **All tools**: Config-driven via `team_config.yaml`; credentials from `.cursor/mcp.json`
- **evaluation-rubric.md**, **zephyr-and-jira.md**, **starter-prompts.md**, **subagent-prompts.md**: Generalized

### Removed

- Direct `fs_nautilus` SDK imports from all documentation and examples
- Hardcoded `AWS_PROFILE=fs-dev`, `jira.trimble.tools`, `TDFS`, `TC File Service`
- `examples.md` (replaced by `examples/pytest/` + framework-specific stubs)

---

## Unreleased

### Planned

- RSpec (Ruby) complete adapter implementation
- Mocha (JavaScript) complete adapter implementation
- Vitest (TypeScript) adapter
- `docs/how-to/write-tests-from-spec.md` — workflow for spec-first teams
- CI template repository with pre-configured GitHub Actions workflows
