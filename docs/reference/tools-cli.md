# CLI reference — all tools

---

## evaluate_test_quality.py

```
python ~/.agents/skills/ticket-to-tests/tools/evaluate_test_quality.py
  --tests PATH           File or directory (required)
  --ac TEXT              AC text inline
  --ac-file FILE         AC text from file
  --spec TEXT            OpenAPI parameter descriptions
  --adapter FRAMEWORK    pytest|jest|junit|go-test|mocha|rspec
  --model MODEL          groq/...|bedrock/...|gpt-4o-mini|ollama/...
  --report-json FILE     Write JSON report
  --skip METRIC_ID       Skip metric (repeatable)
  --config FILE          Path to team_config.yaml
```

---

## create_tests_in_zephyr.py

```
python ~/.agents/skills/ticket-to-tests/tools/create_tests_in_zephyr.py
  --test-dir DIR         Directory containing test files
  --test-file FILE       Specific file(s) (repeatable)
  --link-issue KEY       Jira issue key(s) to link to (repeatable)
  --dry-run              Preview without creating
  --jira-url URL         Override team_config.yaml
  --project-key KEY      Override team_config.yaml
  --config FILE          Path to team_config.yaml
```

---

## push_results_to_zephyr.py

```
python ~/.agents/skills/ticket-to-tests/tools/push_results_to_zephyr.py
  --results-file FILE    JUnit XML results file (required)
  --zephyr-log FILE      zephyr_responses.json (required)
  --cycle-name NAME      Test cycle name
  --key-range RANGE      e.g. PROJ-T100:PROJ-T200
  --auto-create          Auto-create test cases for unmatched sources
  --dry-run              Preview without uploading
  --config FILE          Path to team_config.yaml
```

---

## tag_tests_with_zephyr_keys.py

```
python ~/.agents/skills/ticket-to-tests/tools/tag_tests_with_zephyr_keys.py
  --responses FILE       zephyr_responses.json (required)
  --test-file FILE       Test file(s) to tag (required, repeatable)
  --key-range RANGE      Only use entries in range
  --dry-run              Preview without modifying
  --config FILE          Path to team_config.yaml
```

---

## update_api_coverage.py

```
python ~/.agents/skills/ticket-to-tests/tools/update_api_coverage.py
  --spec PATH            OpenAPI spec file
  --tests DIR            Test root directory
  --output FILE          Output JSON (default: api_coverage_report.json)
  --no-regression-check  Always exit 0
  --config FILE          Path to team_config.yaml
```

---

## generate_jira_automation_mapping.py

```
python ~/.agents/skills/ticket-to-tests/tools/generate_jira_automation_mapping.py
  --tests-root DIR       Root directory for test files
  --output FILE          Output JSON (default: jira_automation_mapping.json)
  --zephyr-log FILE      Merge Zephyr keys from zephyr_responses.json
  --config FILE          Path to team_config.yaml
```

---

## run_schemathesis.sh

```
bash ~/.agents/skills/ticket-to-tests/tools/run_schemathesis.sh [path_filter]

Environment:
  BASE_URL        API base URL (required)
  API_TOKEN       Bearer token (optional)
  OPENAPI_SPEC    Path to OpenAPI spec (overrides team_config.yaml)
  AUTH_TYPE       bearer|basic|apikey (default: bearer)
  AUTH_HEADER     Custom header for API key auth
```
