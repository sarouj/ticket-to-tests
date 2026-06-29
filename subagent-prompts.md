# Task prompts (subagent-style)

Use the **Task** tool with these seeds. Replace `{{config.*}}` with values from your `team_config.yaml`.

---

## Phase 1 — Context (readonly explore)

Read `{{config.context_dir}}/ONBOARDING.md`. Explore `{{config.test_dir_root}}` for:
- SETUP_SCOPE helpers (how shared setup is structured)
- ASSERT_CONTRACT helpers (how HTTP assertions are called)
- TEST_METADATA tags (how epic/feature/story labels are applied)
- Test file naming conventions

> See [ADAPTERS.md](ADAPTERS.md) §`{{config.test_framework.name}}` for patterns to look for.

**Return:** Short summary of domain terms, test layout conventions, and open questions.

---

## Phase 2 — Jira requirements (mcp-atlassian only)

Fetch the Jira issue via `mcp-atlassian`. Extract AC, description, links, and any Zephyr references.
Confirm `TARGET_ENV` with the user if not already specified.

**Return:** Bullet list of ACs, scope, out-of-scope, links, and confirmed `TARGET_ENV`.

---

## Phase 3 — Test case design (readonly explore)

1. Read Jira ACs and OpenAPI spec at `{{config.openapi.spec_path}}`.
2. For each endpoint+status code, classify as T1/T2/T3 using [phases/phase-3-design.md](phases/phase-3-design.md) §3i.
3. Plan OWASP tests (BOLA, mass assignment, security headers) for every new/modified endpoint.
4. List response codes in spec with no corresponding AC as gaps.
5. **Do NOT write any test code.** Output a structured test plan only.
6. End with "Ready for Phase 4 review?" — do not auto-proceed to Phase 5.

**Return:** Numbered test plan + response-code gap list + open questions.

---

## Phase 5 — Implementation

1. Read the approved Phase 3 test plan.
2. Read shared setup module and analogous test files for structural patterns.
3. Implement each test case using the adapter for `{{config.test_framework.name}}`.
   - File naming: `{{config.test_dir_root}}<area>/<feature>/`
   - See [ADAPTERS.md](ADAPTERS.md) §`{{config.test_framework.name}}` for syntax.
4. After completing each test file, trigger the Phase 5b deepeval loop.

**Return:** Completed test file(s), then initiate Phase 5b.

---

## Phase 5b — Iterative deepeval refinement

```
iteration = 0
max_iterations = 3

while iteration < max_iterations:
    python ~/.agents/skills/ticket-to-tests/tools/evaluate_test_quality.py \
        --tests <path> --ac "<ac_text>" --spec "<spec_text>" \
        --adapter {{config.test_framework.name}} \
        --model {{config.deepeval.default_model}} \
        --report-json deepeval_report.json

    if exit_code == 0: break
    read deepeval_report.json and apply fixes
    iteration += 1

if still failing: prepend # DEEPEVAL GAPS comment block and proceed as "Pass with gaps"
```

**Return:** Final metric scores, iteration count, any gap documentation.

---

## Phase 5c — Test execution and bug triage

1. Verify auth: run `{{config.auth.verify_cmd}}`.
2. Run tests using `{{config.test_framework.runner_cmd}}` against `TARGET_ENV`.
3. For each failed test: classify as server bug / spec drift / test code issue.
4. For each confirmed server bug, ask the user before filing via `mcp-atlassian`.
5. Annotate failing tests with SKIP_XFAIL. See [ADAPTERS.md](ADAPTERS.md) §SKIP_XFAIL.
6. Gate: all pass → Phase 6. Failures remain → ask user before proceeding.

**Return:** Run summary, Jira bug keys filed, SKIP_XFAIL annotations added.

---

## Phase 7 — Evaluation (readonly generalPurpose)

Read [evaluation-rubric.md](evaluation-rubric.md) and apply every section.
Compare: Jira ACs vs implemented tests vs `context/ONBOARDING.md` alignment.

**Return:**
- **Verdict:** Pass | Pass with gaps | Fail
- **Must-fix** (blocking merge)
- **Nice-to-have**
- **Ready for merge / Zephyr export:** yes/no
