# Starter prompts for ticket-to-tests

Two variants:
- **[Full template](#full-template)** — use when you know all the details.
- **[Grill-me variant](#grill-me-variant)** — use when you want the agent to ask clarifying questions first.

---

## Prerequisites checklist

| # | Prerequisite | Quick verify |
|---|---|---|
| 1 | `mcp-atlassian` connected | Green indicator in Cursor → Settings → MCP panel |
| 2 | Auth valid | Run `{{config.auth.verify_cmd}}` from `team_config.yaml` |
| 3 | Test framework installed | Run `{{config.test_framework.runner_cmd}}` with `--version` |
| 4 | deepeval installed | `pip install deepeval` |
| 5 | `team_config.yaml` configured | `python ~/.agents/skills/ticket-to-tests/tools/team_config.py` — no warnings |

---

## Full template

```
Use /ticket-to-tests for the following:

**Jira ticket:** <TICKET_URL>

**Reference docs:**
- @reference/<DOC_FILE>
- {{config.openapi.spec_path}}

**Entity scope:** <entity types in scope>

**Target test directory:** {{config.test_dir_root}}<area>/<feature>/

**Phase 1 — Context:** auto

**Phase 2 — Requirement intake:**
  Jira ticket: <TICKET_URL>
  Target environment: <TARGET_ENV>

**Phase 3 — Test case generation:**
  Entity scope: <entity types>
  OpenAPI spec: {{config.openapi.spec_path}}

**Phase 3b — Feature impact analysis:**
  Run: <yes | skip — only for purely additive new endpoints>

**Phase 4 — Review test plan:**
  Approval: <auto-approve | pause and wait for my confirmation>

**Phase 5 — Implement automation:**
  Target test directory: {{config.test_dir_root}}<area>/<feature>/
  Related tests: {{config.test_dir_root}}<area>/<similar_feature>/

**Phase 5b — deepeval refinement loop:**
  Model: {{config.deepeval.default_model}}
  Max iterations: 3

**Phase 5c — Test run and bug triage:**
  Environment: <TARGET_ENV>
  Bug filing: <confirm before each Jira bug | auto-file>
  On remaining failures: <pause | mark SKIP_XFAIL>

**Phase 6 — Zephyr alignment:**
  Zephyr mode: <dry-run only | live create>
  Link tests to story: <TICKET_URL>

**Phase 7 — Holistic evaluation:**
  Mode: <auto-evaluate | pause for my review>

**Security scope:**
  BOLA: <yes | no>
  Mass-assignment probe: <yes | no>
  Security response headers: <yes | no>
```

---

## Grill-me variant

```
Use /ticket-to-tests for the following:

**Jira ticket:** <TICKET_URL>

**Reference docs:**
- @reference/<DOC_FILE>
- {{config.openapi.spec_path}}

Before writing any test code or plan, grill me with questions.

Read the Jira ticket and the reference docs. Then ask me the minimum set of
pointed questions needed to fill in every unknown before you begin Phase 3.
Cover at least:

1. Entity scope
2. Operation semantics (new vs modified)
3. Partial success handling
4. Idempotency expectation
5. Access control / role restrictions
6. Version gating
7. Target test directory
8. Phase 3b impact (adapter layer, async events, permission metadata)
9. Security scope (BOLA, alternate-ID patterns)
10. Zephyr sync mode
11. deepeval model override
12. Any known flaky patterns or environment gaps
13. Target environment for Phase 5c
14. Phase 5c bug filing mode
15. Phase 7 evaluation mode

Do NOT proceed to Phase 3 until I have answered your questions.
```
