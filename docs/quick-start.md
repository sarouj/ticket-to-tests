# Quick start — 15-minute walkthrough

This guide walks through the complete `ticket-to-tests` workflow using a fictional
REST API project. By the end you will have:

- Generated test cases from a Jira ticket
- Implemented them using your framework
- Evaluated their quality with the AI meta-evaluator
- Exported them to Zephyr Scale (dry-run)

> **Prerequisites**: Complete [ADOPTING.md](../ADOPTING.md) first (5 min).

---

## Scenario

**API**: `POST /items` — create an item in a project
**Jira ticket**: `MYPRJ-42 — Items API: Create Item endpoint`

```
AC1: Successful create returns 201 with the created item in the body.
AC2: Name must be unique within a project — duplicate returns 409.
AC3: Name max length is 255 characters — over-max returns 400 VALIDATION_ERROR.
AC4: Unauthenticated requests return 401 UNAUTHORIZED.
```

---

## Step 1 — Invoke the skill (2 min)

Open Cursor chat and paste:

```
Run the ticket-to-tests skill for ticket MYPRJ-42.
Target environment: QA-US
Framework: pytest
```

The agent will read `team_config.yaml`, read `context/ONBOARDING.md`, fetch MYPRJ-42 via mcp-atlassian, and read the OpenAPI spec.

---

## Step 2 — Review the generated test plan (3 min)

```
Phase 3 — Test plan for MYPRJ-42

T1 — Happy path
  [ ] test_create_item_returns_201_with_item_body
  [ ] test_create_item_response_contains_required_fields

T2 — BVA + error contract
  [ ] test_create_item_name_boundary (PARAMETRIZE x6 values)
  [ ] test_create_item_returns_409_for_duplicate_name
  [ ] test_create_item_returns_401_without_auth

T3 — Advanced
  [ ] test_create_item_response_does_not_leak_server_headers
  [ ] test_create_item_patch_ignores_undocumented_fields (mass assignment)
```

Review and confirm: "looks good, proceed" or ask to add/remove cases.

---

## Step 3 — Run the AI quality evaluation (3 min)

```bash
python ~/.agents/skills/ticket-to-tests/tools/evaluate_test_quality.py \
    --tests tests/items/create_item/create_item_test.py \
    --ac "AC1: 201 with body. AC2: Duplicate -> 409. AC3: Over-max -> 400. AC4: No auth -> 401." \
    --spec "name: string, max 255 chars, unique per project" \
    --adapter pytest \
    --model groq/llama-3.1-70b-versatile \
    --report-json deepeval_report.json
```

If any metric fails, the agent suggests targeted fixes and re-runs (up to 3 iterations).

---

## Step 4 — Run your tests (2 min)

```bash
python -m pytest tests/items/create_item/ --env QA-US -v
```

Fix any failures (see [docs/how-to/triage-failures.md](how-to/triage-failures.md)).

---

## Step 5 — Export to Zephyr (1 min)

Always dry-run first:

```bash
python ~/.agents/skills/ticket-to-tests/tools/create_tests_in_zephyr.py \
    --test-dir tests/items/create_item/ \
    --link-issue MYPRJ-42 \
    --dry-run
```

Review output, then confirm and create for real.

---

## Next steps

- [docs/concepts.md](concepts.md) — understand the 7-phase workflow deeply
- [docs/how-to/write-tests-from-ticket.md](how-to/write-tests-from-ticket.md) — advanced patterns
- [docs/how-to/customize-adapter.md](how-to/customize-adapter.md) — add your framework
- [docs/team-integration.md](team-integration.md) — embed in PR workflow and CI
