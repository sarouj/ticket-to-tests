# Troubleshooting

Common issues across all frameworks. Use Ctrl+F to find your error.

---

## Installation and setup

### `team_config.yaml not found in the current directory or any parent`

```bash
cp ~/.agents/skills/ticket-to-tests/templates/team_config.yaml team_config.yaml
cd /path/to/your/project
python ~/.agents/skills/ticket-to-tests/tools/team_config.py
```

### `WARNING: team_config.yaml has unconfigured required fields`

Open `team_config.yaml` and replace all placeholder values. See [docs/config-reference.md](config-reference.md).

### `ERROR: PyYAML is not installed` / `ERROR: deepeval is not installed`

```bash
pip install pyyaml deepeval
```

---

## Jira / mcp-atlassian

### Agent says "I cannot access Jira" or "mcp-atlassian not available"

1. Verify `.cursor/mcp.json` contains `JIRA_USERNAME` and `JIRA_API_TOKEN` under `mcp-atlassian.env`.
2. Generate a token at `https://id.atlassian.com/manage-profile/security/api-tokens`.
3. Restart Cursor after updating `mcp.json`.

---

## DeepEval / evaluate_test_quality.py

### `GROQ_API_KEY is not set`

```bash
export GROQ_API_KEY=<your-key>  # Free key at: https://console.groq.com -> API Keys
```

### Scores are always 0.0

Local Ollama 7B model gives unreliable output. Switch to Groq: `--model groq/llama-3.1-70b-versatile`.

### `rate-limited, waiting 35s before retry`

Handled automatically with 3 retries + backoff. If it continues to fail, switch to a paid model.

---

## Test failures

### All tests fail with 401

Auth token not set or expired. Run `<auth.verify_cmd from team_config.yaml>` to verify.

### `expected 400, got 422`

The API uses 422 for validation errors. Update the test to expect 422 (or whichever the spec documents).

---

## Zephyr Scale

### `WARNING: Folder 'Items' not found in Zephyr`

The folder name in `zephyr.epic_folder_map` doesn't match the exact folder in Zephyr Scale.
Copy the exact name (case-sensitive) from the Zephyr Scale UI.

### Test cases created but not linked to Jira story

Zephyr Scale API silently drops `issueLinks` on creation (known bug). The script handles it automatically.
Check: `Issue link verification: N already linked, M fixed, 0 failed.`

---

## Framework-specific

### pytest: `fixture 'xxx' not found`

The SETUP_SCOPE helper doesn't exist in `conftest.py`. Add it. See `examples/pytest/` for patterns.

### Jest: `Cannot find module '../sdk/items'`

Update the import path to match your project's SDK location.

### JUnit: `No tests found` with Maven

Ensure the test class name matches `*Test.java` or configure `<includes>` in `pom.xml`.

### Go: `undefined: createItem`

Create your team's helper package and import it. See `examples/go-test/README.md`.

---

## Debug checklist

```bash
# 1. Config loads correctly
python ~/.agents/skills/ticket-to-tests/tools/team_config.py

# 2. OpenAPI spec is accessible
ls -la <openapi.spec_path from team_config.yaml>

# 3. Auth works
<auth.verify_cmd from team_config.yaml>

# 4. Evaluate a single test file
python ~/.agents/skills/ticket-to-tests/tools/evaluate_test_quality.py \
    --tests tests/items/create_item/create_item_test.py \
    --ac "AC1: Returns 201." \
    --model groq/llama-3.1-70b-versatile
```
