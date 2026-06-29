# How to evaluate test quality with AI

---

## Prerequisites

```bash
export GROQ_API_KEY=<your-key>   # free at console.groq.com
pip install deepeval pyyaml
```

---

## Basic usage

```bash
python ~/.agents/skills/ticket-to-tests/tools/evaluate_test_quality.py \
    --tests tests/items/create_item/create_item_test.py \
    --ac "AC1: 201 with body. AC2: Duplicate → 409. AC3: Over-max → 400."
```

---

## Full usage

```bash
python ~/.agents/skills/ticket-to-tests/tools/evaluate_test_quality.py \
    --tests tests/items/create_item/ \
    --ac "AC1: 201 with body. AC2: Duplicate → 409." \
    --spec "name: string, max 255 chars. type: enum TASK|BUG|STORY" \
    --adapter pytest \
    --model groq/llama-3.1-70b-versatile \
    --report-json deepeval_report.json
```

## Metric IDs and thresholds

| ID | Metric | Threshold |
|---|---|---|
| `ac_coverage` | AC Coverage | 0.75 |
| `error_contract` | Error Response Contract | 0.85 |
| `bva_coverage` | BVA PARAMETRIZE Coverage | 0.70 |
| `setup_scope` | SETUP_SCOPE Adherence | 0.80 |

## Common fixes

| Low metric | Typical cause | Fix |
|---|---|---|
| AC Coverage | Some ACs have no test | Add one test per missing AC |
| Error Contract | Non-2xx test only asserts status | Add error body assertion |
| BVA Coverage | Boundary cases are separate functions | Merge into one PARAMETRIZE table |
| SETUP_SCOPE | Mutating test uses session-scope | Change to function-scope setup |
