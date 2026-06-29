---
name: ticket-to-tests
description: Language- and framework-agnostic test automation skill. Works with pytest, JUnit, Jest, Go, RSpec, Mocha, or any stack.
---

> **This skill is language- and framework-agnostic.**
> All language-specific syntax lives in [ADAPTERS.md](ADAPTERS.md).

# ticket-to-tests

## Supported frameworks

| Framework | Language | Adapter status |
|---|---|---|
| pytest | Python | Complete |
| JUnit 5 | Java | Stub |
| Jest / Vitest | TypeScript / JavaScript | Stub |
| Go testing | Go | Stub |
| RSpec | Ruby | Stub |
| Mocha | JavaScript | Stub |

## When to apply

- Implement or extend automated tests from a Jira ticket or design doc
- Align tests with Zephyr Scale
- Run a structured workflow with context, Jira, and AI evaluation
- Check API test coverage or run contract tests

## Language-agnostic concept terms

| Term | Meaning |
|---|---|
| `TEST_RUNNER_CMD` | Run a subset of tests |
| `TEST_METADATA` | Attach labels / tags |
| `PARAMETRIZE` | Data-driven / table-driven tests |
| `SETUP_SCOPE` | Shared vs per-test setup |
| `SKIP_XFAIL` | Mark a known failing test |
| `ASSERT_CONTRACT` | Status + error body assertion |

See [ADAPTERS.md](ADAPTERS.md) for framework-specific syntax for each term.

## Prerequisites

1. **mcp-atlassian** configured in `.cursor/mcp.json`
2. **Auth** — test environment accessible; run `auth.verify_cmd`
3. **Test framework** installed; verify via runner_cmd --version
4. **deepeval** (Phase 5b): `pip install deepeval`; set `GROQ_API_KEY`
5. **OpenAPI spec** current at `openapi.spec_path`

## Phase reference

| Phase | File |
|---|---|
| 1 + 2 — Context + Jira intake | [phases/phase-1-2.md](phases/phase-1-2.md) |
| 3 + 4 — Design + Review | [phases/phase-3-design.md](phases/phase-3-design.md) |
| 3b — Feature impact | [phases/phase-3b-impact.md](phases/phase-3b-impact.md) |
| 5 + 5b — Implement + deepeval | [phases/phase-5-implement.md](phases/phase-5-implement.md) |
| 5c — Execute + triage | [phases/phase-5c-triage.md](phases/phase-5c-triage.md) |
| 6 + 7 — Zephyr + Holistic | [phases/phase-6-7.md](phases/phase-6-7.md) |

## Resources

- [starter-prompts.md](starter-prompts.md) — copy-paste prompts
- [subagent-prompts.md](subagent-prompts.md) — task delegation templates
- [ADAPTERS.md](ADAPTERS.md) — framework adapter contract
- [ADOPTING.md](ADOPTING.md) — installation guide
- [docs/](docs/) — full documentation
