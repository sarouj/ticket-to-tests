# How to customize or add a framework adapter

---

## The 7 adapter slots

| Slot | What it means |
|---|---|
| `TEST_RUNNER_CMD` | How to execute tests from the CLI |
| `TEST_METADATA` | How to annotate tests with epic, feature, story, Jira links |
| `PARAMETRIZE` | Data-driven test mechanism |
| `SETUP_SCOPE` | Session-level vs function-level setup |
| `SKIP_XFAIL` | How to skip or mark as expected-to-fail |
| `ASSERT_CONTRACT` | How to assert status code + error body |
| `RESULTS_FORMAT` | Output format for CI / Zephyr push |

---

## Step 1 — Add your adapter to ADAPTERS.md

Open `~/.agents/skills/ticket-to-tests/ADAPTERS.md` and add a new `## Adapter: <framework>` section with all 7 slots.

## Step 2 — Update team_config.yaml

```yaml
test_framework:
  name: "vitest"    # must match the adapter section name
  runner_cmd: "npx vitest run {test_path} {flags}"
  file_pattern: "**/*.spec.ts"
```

## Step 3 — Add example files

Create `examples/<framework>/README.md` with copy-paste examples for each pattern.

## Step 4 — Test with evaluate_test_quality.py

```bash
python ~/.agents/skills/ticket-to-tests/tools/evaluate_test_quality.py \
    --tests src/__tests__/items/ \
    --ac "AC1: 201 with body." \
    --adapter vitest \
    --model groq/llama-3.1-70b-versatile
```

## Step 5 — Submit (optional)

Open a PR with: updated `ADAPTERS.md`, `examples/<framework>/README.md`, `CHANGELOG.md` entry.
