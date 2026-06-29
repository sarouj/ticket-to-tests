# Team integration guide

How to embed the `ticket-to-tests` skill into your team's daily workflow.

---

## PR workflow

### For the developer (test author)

Before opening a PR with new or modified tests:

1. **Run the AI quality evaluator** — all 4 metrics must pass:
   ```bash
   python ~/.agents/skills/ticket-to-tests/tools/evaluate_test_quality.py \
       --tests <your-test-file-or-dir> \
       --ac "<AC text from Jira>" \
       --report-json deepeval_report.json
   ```

2. **Run tests** against QA.

3. **Check API coverage** (if you added tests for a new endpoint):
   ```bash
   python ~/.agents/skills/ticket-to-tests/tools/update_api_coverage.py
   ```

4. **Include in PR description**: which Jira ticket, deepeval summary, Zephyr keys.

### For the code reviewer

- [ ] Does each AC have at least one T1 test?
- [ ] Do all non-2xx tests call ASSERT_CONTRACT (status + error body)?
- [ ] Are BVA cases PARAMETRIZE'd (not separate test functions)?
- [ ] Do mutating tests use function-scoped setup, read-only tests session-scoped?
- [ ] OWASP tests (BOLA, mass assignment) for new endpoints?
- [ ] `deepeval_report.json` attached and all metrics passing?

---

## Sprint ceremonies

### Sprint planning
- Add a sub-task: "Generate and push Zephyr test cases"
- Estimate 2–4 hours per new endpoint for full ticket-to-tests coverage

### Sprint review
Present: `api_coverage_report.json`, `deepeval_report.json`, Zephyr Scale dashboard.

### Retrospective
- Which tests caught bugs before production?
- Were there MUST-FIX items in the AI evaluation? What patterns caused them?

---

## CI/CD integration

### Required CI checks

| Check | Tool | Threshold |
|---|---|---|
| Tests pass | `test_framework.runner_cmd` | 0 failures (except xfail) |
| AI quality gate | `evaluate_test_quality.py` | All 4 metrics pass |
| API coverage no regression | `update_api_coverage.py` | Exit 0 |

### Informational checks

| Check | Tool | Notes |
|---|---|---|
| Schemathesis contract tests | `run_schemathesis.sh` | Run nightly |
| Push results to Zephyr | `push_results_to_zephyr.py` | Run on main branch |

See [docs/how-to/integrate-with-ci.md](how-to/integrate-with-ci.md) for YAML examples.

---

## Code review checklist (add to your PR template)

```markdown
## Test quality checklist

- [ ] AI evaluation passed: all 4 metrics >= threshold
- [ ] All Jira ACs have >=1 T1 test
- [ ] BVA parameters are PARAMETRIZE'd
- [ ] Non-2xx tests call ASSERT_CONTRACT (status + error body)
- [ ] Mutating tests use function-scoped setup; read-only tests use session-scoped setup
- [ ] OWASP tests present for new endpoints
- [ ] Zephyr test cases created and linked to Jira story (or N/A: explain)
```

---

## Metrics to track over time

| Metric | Tool | Frequency |
|---|---|---|
| API endpoint coverage % | `api_coverage_report.json` | Per sprint |
| AI evaluation pass rate | `deepeval_report.json` | Per PR |
| Zephyr test cases created | Zephyr Scale dashboard | Per sprint |

A healthy team should see:
- API coverage >= 80% for critical endpoints
- AI evaluation pass rate >= 95% of PRs
- All new endpoints have T3 tests within 2 sprints
