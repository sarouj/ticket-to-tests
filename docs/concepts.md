# Concepts — understanding the ticket-to-tests workflow

This document explains the **why** behind the skill's design.

---

## The 7-phase workflow

```
Phase 1  Context loading          Reads ONBOARDING.md + OpenAPI spec + existing tests
Phase 2  Jira intake              Fetches AC, story, and related tickets via mcp-atlassian
Phase 3  Test case design         Generates test plan (T1 -> T2 -> T3)
Phase 3b Feature impact analysis  Checks upstream/downstream ripple effects
Phase 4  Spec validation          Cross-references test plan against OpenAPI spec
Phase 5  Test implementation      Writes code using framework adapter
Phase 5b DeepEval quality loop    AI-scores tests; fixes; re-scores until all pass
Phase 5c Test execution + triage  Runs tests; triages failures; files Jira bugs
Phase 6  Zephyr alignment         Creates Zephyr test cases (dry-run first)
Phase 7  Holistic review          Final checklist + evaluation rubric
Phase 7b AI evaluation scores     Records evaluate_test_quality.py scores
```

---

## The T1 / T2 / T3 tier system

### T1 — Happy path (required; must ship first)

One test per Jira acceptance criterion. Proves the feature works at all.

### T2 — Boundary values + error contract (required)

- **BVA**: min, max, over-max, empty, whitespace, null for each parameter
- **Error contract**: every non-2xx path asserts status code AND error body shape
- All T2 parameter sweeps use **PARAMETRIZE** (data-driven tests)

### T3 — Advanced / edge cases (recommended)

- Idempotency, state machine, pagination, OWASP (BOLA, mass assignment, security headers)
- Performance SLA assertions, property-based testing

---

## The DeepEval quality loop (Phase 5b)

```
evaluate_test_quality.py
        |
        v
  G-Eval judge reads the test file + AC text + OpenAPI spec params
        |
        v
  Scores 4 metrics (0-1):
    AC Coverage          >= 0.75
    Error Contract       >= 0.85
    BVA PARAMETRIZE      >= 0.70
    SETUP_SCOPE          >= 0.80
        |
        v
  If any metric fails -> agent auto-fixes -> re-scores (max 3 iterations)
```

---

## Language-agnostic design

All phase documents use neutral concept terms:

| Term | Means |
|---|---|
| `PARAMETRIZE` | Your framework's data-driven test mechanism |
| `SETUP_SCOPE` | Session-level vs function-level resource setup |
| `SKIP_XFAIL` | Mark a test as skipped or known-to-fail |
| `ASSERT_CONTRACT` | Your team's assertion helper for status + error body |
| `TEST_METADATA` | Annotation tags linking tests to Jira/Zephyr |

Framework-specific syntax lives exclusively in **[ADAPTERS.md](../ADAPTERS.md)**.

---

## SETUP_SCOPE rules

| Test type | Required scope |
|---|---|
| Read-only (GET, list) | Session-scope (shared) |
| Mutating (create, update, delete) | Function-scope (per-test) |

No test body should create API resources directly. All resource creation belongs in SETUP helpers.

---

## Zephyr Scale and the dry-run policy

1. Run with `--dry-run` to preview
2. Review the output
3. Confirm with: "create for real" / "yes, create them"

After creation, always check: `Issue link verification: N already linked, M fixed, 0 failed.`

---

## See also

- [ADAPTERS.md](../ADAPTERS.md) — framework syntax reference
- [docs/config-reference.md](config-reference.md) — all team_config.yaml fields
- [docs/quick-start.md](quick-start.md) — hands-on walkthrough
- [evaluation-rubric.md](../evaluation-rubric.md) — quality checklist
