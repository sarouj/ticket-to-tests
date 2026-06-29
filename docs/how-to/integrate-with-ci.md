# How to integrate with CI/CD

---

## What belongs in CI

| Tool | When to run | Exit code |
|---|---|---|
| `evaluate_test_quality.py` | Pre-merge / PR check | 0=pass, 1=fail |
| `update_api_coverage.py` | On main branch push | 0=no regression, 1=regression |
| `run_schemathesis.sh` | Nightly / main branch | 0=pass, 1=violations |
| `push_results_to_zephyr.py` | After test run on main/release | 0=success, 1=error |

---

## GitHub Actions: full pipeline

```yaml
name: Test Quality Gate
on:
  pull_request:
    branches: [main, develop]
jobs:
  test-and-evaluate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Install dependencies
        run: pip install pyyaml deepeval requests
      - name: Run tests
        run: |
          python -m pytest tests/ \
            --env ${{ vars.TARGET_ENV }} \
            --junit-xml=test-results.xml -v
        continue-on-error: true
      - name: Evaluate test quality
        run: |
          python ~/.agents/skills/ticket-to-tests/tools/evaluate_test_quality.py \
            --tests tests/ --report-json deepeval_report.json
        env:
          GROQ_API_KEY: ${{ secrets.GROQ_API_KEY }}
      - name: Check API coverage
        run: |
          python ~/.agents/skills/ticket-to-tests/tools/update_api_coverage.py
      - name: Upload reports
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: test-reports
          path: |
            test-results.xml
            deepeval_report.json
            api_coverage_report.json
```

---

## GitLab CI

```yaml
stages: [test, quality]

test:
  stage: test
  script:
    - pip install pyyaml deepeval requests
    - python -m pytest tests/ --junit-xml=test-results.xml
  artifacts:
    reports:
      junit: test-results.xml

evaluate-quality:
  stage: quality
  script:
    - python ~/.agents/skills/ticket-to-tests/tools/evaluate_test_quality.py
        --tests tests/ --report-json deepeval_report.json
  variables:
    GROQ_API_KEY: $GROQ_API_KEY
```

---

## Required secrets

| Secret | Purpose |
|---|---|
| `GROQ_API_KEY` | DeepEval G-Eval judge |
| `AUTH_TOKEN` | Test session authentication |
| `JIRA_USERNAME` | Zephyr push |
| `JIRA_API_TOKEN` | Zephyr push |
