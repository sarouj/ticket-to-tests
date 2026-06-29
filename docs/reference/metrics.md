# DeepEval metric definitions

---

## Metrics overview

| Metric | ID | Threshold | What it measures |
|---|---|---|---|
| AC Coverage | `ac_coverage` | 0.75 | Each Jira AC has at least one test that exercises the described behavior |
| Error Response Contract | `error_contract` | 0.85 | Every non-2xx test calls both status assertion AND error body assertion |
| BVA PARAMETRIZE Coverage | `bva_coverage` | 0.70 | Boundary values are expressed using the framework's data-driven mechanism |
| SETUP_SCOPE Adherence | `setup_scope` | 0.80 | Read-only tests use shared setup; mutating tests use per-test setup |

---

## Score interpretation

- **>= threshold**: Pass — no action needed
- **Within 0.05 of threshold**: Borderline — review the `reason` field and use judgment
- **Below threshold**: Must-fix — fix before merging

---

## Model guide

| Model | Cost | Accuracy | Setup |
|---|---|---|---|
| `groq/llama-3.1-70b-versatile` | Free | Good | Set `GROQ_API_KEY` |
| `gpt-4o-mini` | Low | Good | Set `OPENAI_API_KEY` |
| `bedrock/us.anthropic.claude-haiku-4-5-20251001-v1:0` | Low | Very good | Set `AWS_PROFILE` + `AWS_REGION` |
| `bedrock/us.anthropic.claude-sonnet-4-6` | Medium | Excellent | Set `AWS_PROFILE` + `AWS_REGION` |
| `ollama/<model>` | Free | **Unreliable** | Local only; 7B models give all-zero/all-one scores |

**Recommendation**: Use `groq/llama-3.1-70b-versatile` for day-to-day (free, good quality).
Use `bedrock/claude-sonnet` for release gates (high accuracy).
**Never** use ollama models for real evaluations.

---

## Adjusting thresholds

After 5–10 evaluation runs, if a metric produces consistent false positives or negatives
for your feature type, adjust the threshold in `evaluate_test_quality.py`:

```python
METRICS_CONFIG = [
    {"id": "bva_coverage", "threshold": 0.65, ...},  # adjusted down for this project
]
```

Document the reason in a comment. Communicate the change to your team.
