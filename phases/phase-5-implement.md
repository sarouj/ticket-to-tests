# Phase 5 — Implement automation

- Add or edit test files under `team_config.yaml → test_dir_root` following the project's naming conventions.
- Apply TEST_METADATA tags per your framework adapter. See [ADAPTERS.md](../ADAPTERS.md) §TEST_METADATA.
- For coding conventions (ASSERT_CONTRACT, SETUP_SCOPE, SDK/client library usage), read [phase-3-design.md](phase-3-design.md) §§3e–3h.
- After writing the initial test file, immediately enter the **Phase 5b iterative refinement loop**.

---

# Phase 5b — Iterative deepeval refinement loop

**Loop algorithm:**

```
iteration = 0
max_iterations = 3

while iteration < max_iterations:
    run deepeval → write deepeval_report.json
    if all metrics passed (exit code 0):
        break  ← proceed to Phase 6
    read deepeval_report.json
    for each metric where passed == false:
        apply the fix pattern from the table below
    iteration += 1

if any metric still failing after 3 iterations:
    document remaining gaps in a comment block at the top of the test file
    treat as "Pass with gaps" — proceed to Phase 6
```

**Run command (each iteration):**

```bash
python ~/.agents/skills/ticket-to-tests/tools/evaluate_test_quality.py \
    --tests <path-to-test-file-or-dir> \
    --ac "AC1: <text>. AC2: <text>." \
    --spec "endpoint + parameter descriptions." \
    --adapter <framework>      \  # e.g. pytest, jest, junit, go-test
    --model <model>            \  # from team_config.yaml → deepeval.default_model
    --report-json deepeval_report.json
```

**Fix patterns per failing metric:**

| Failing metric | Fix to apply |
|---|---|
| `ac_coverage` | Add one test function per uncovered AC |
| `error_contract` | Add ASSERT_CONTRACT calls after every non-2xx status assertion. See [ADAPTERS.md](../ADAPTERS.md) §ASSERT_CONTRACT |
| `bva_coverage` | Add PARAMETRIZE test covering min/max/over-max/null/whitespace/unknown-enum. See [ADAPTERS.md](../ADAPTERS.md) §PARAMETRIZE |
| `setup_scope` | Move resource creation into SETUP_SCOPE helpers. See [ADAPTERS.md](../ADAPTERS.md) §SETUP_SCOPE |

**Metrics and thresholds:**

| Metric | ID | Threshold |
|---|---|---|
| AC Coverage | `ac_coverage` | ≥ 0.75 |
| Error Response Contract | `error_contract` | ≥ 0.85 |
| BVA PARAMETRIZE Coverage | `bva_coverage` | ≥ 0.70 |
| SETUP_SCOPE Adherence | `setup_scope` | ≥ 0.80 |

**Model options** (set default in `team_config.yaml → deepeval.default_model`):

- `groq/llama-3.1-70b-versatile` — free tier; set `GROQ_API_KEY`
- `bedrock/us.anthropic.claude-haiku-4-5-20251001-v1:0` — AWS Bedrock
- `gpt-4o-mini` — OpenAI; set `OPENAI_API_KEY`
- `ollama/<model>` — **do not use for real evaluations**
