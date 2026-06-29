# Phase 7 — Evaluation rubric

Use this checklist for the **holistic** review (Phase 7). Phase 4 is test-design-only; this is end-to-end.

---

## 1. Traceability

- [ ] Each major AC from the Jira ticket has at least one automated test or is explicitly out of scope with reason.
- [ ] Tests reference the Jira story via TEST_METADATA tags per the project's convention (see `context/ONBOARDING.md`).

---

## 2. Correctness and coverage

- [ ] Happy path, documented errors (4xx/5xx), and relevant edge cases are covered per Phase 3 rules.
- [ ] ASSERT_CONTRACT is called consistently — status code AND error body for every non-2xx test.
  See [ADAPTERS.md](ADAPTERS.md) §ASSERT_CONTRACT.
- [ ] Response body validation is complete: every field is either asserted or explicitly excluded.
- [ ] No raw HTTP calls in test code; all API interactions use the team's SDK/client library.

### T2 — Boundary coverage

- [ ] Every non-2xx test calls ASSERT_CONTRACT — status code AND error body.
- [ ] BVA coverage exists for every string/numeric request parameter using PARAMETRIZE.
  See [ADAPTERS.md](ADAPTERS.md) §PARAMETRIZE.
- [ ] Auth-failure tests exist for every endpoint: unauthenticated (401) and at least one forbidden role (403).

### OWASP API Security coverage

- [ ] BOLA: second authenticated session attempts access to primary session's resource; response is 403 or 404.
- [ ] Mass Assignment: PATCH/POST with undocumented field is rejected or verified absent from GET response.
- [ ] Security headers: asserts `X-Powered-By`, `X-AspNet-Version` absent from 2xx responses.

### T3 — Behavioral coverage (mutable operations)

- [ ] Idempotency — DELETE called twice; second call returns 404 or 409, never 5xx.
- [ ] State-machine transitions — at least one invalid lifecycle transition tested.
- [ ] Pagination completeness — single-page, multi-page traversal, count invariant.

---

## 3. Project conventions

- [ ] Test files live under `{{config.test_dir_root}}` with the naming pattern from `team_config.yaml`.
- [ ] TEST_METADATA tags match the project's convention. See [ADAPTERS.md](ADAPTERS.md) §TEST_METADATA.
- [ ] SETUP_SCOPE helpers are used appropriately. See [ADAPTERS.md](ADAPTERS.md) §SETUP_SCOPE.

---

## 4. Zephyr / TEST_METADATA

- [ ] TEST_METADATA tags align with `team_config.yaml → zephyr.epic_folder_map`.
- [ ] If Zephyr export is planned, dry-run was reviewed and output documented.

---

## 5. Mapping and Phase B readiness

- [ ] `generate_jira_automation_mapping.py` runs successfully or gaps are listed.
- [ ] `update_api_coverage.py` exits 0 — covered endpoint count did not regress.
- [ ] Schemathesis produces zero failures on all affected paths.

---

## 6. AI evaluation scores (Phase 7b — deepeval)

```bash
python ~/.agents/skills/ticket-to-tests/tools/evaluate_test_quality.py \
    --tests <path/to/test-file-or-dir> \
    --ac "<pasted AC text>" \
    --spec "<parameter descriptions from OpenAPI>" \
    --adapter <framework-name> \
    --model <model> \
    --report-json deepeval_report.json
```

### [Feature name / ticket key]

| Metric | ID | Threshold | Actual score | Pass? | Notes |
|---|---|---|---|---|---|
| AC Coverage | `ac_coverage` | ≥ 0.75 | | | |
| Error Response Contract | `error_contract` | ≥ 0.85 | | | |
| BVA PARAMETRIZE Coverage | `bva_coverage` | ≥ 0.70 | | | |
| SETUP_SCOPE Adherence | `setup_scope` | ≥ 0.80 | | | |

---

## Verdict

| Verdict | Meaning |
|---|---|
| **Pass** | No must-fix items AND all deepeval metrics ≥ threshold. |
| **Pass with gaps** | Merge acceptable with documented follow-ups; borderline scores acceptable. |
| **Fail** | Any manual rubric must-fix OR any deepeval metric below threshold. |
