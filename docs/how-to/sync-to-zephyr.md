# How to sync tests to Zephyr Scale

---

## Prerequisites

`JIRA_USERNAME` and `JIRA_API_TOKEN` in `.cursor/mcp.json`; `team_config.yaml` with `zephyr.epic_folder_map`.

---

## Step 1 — Configure epic → folder mapping

```yaml
zephyr:
  epic_folder_map:
    "ITEM": "Items"
    "AUTH": "Authentication"
```

## Step 2 — Dry-run (always first)

```bash
python ~/.agents/skills/ticket-to-tests/tools/create_tests_in_zephyr.py \
    --test-dir tests/items/create_item/ \
    --link-issue MYPRJ-42 \
    --dry-run
```

## Step 3 — Live creation (after dry-run review)

```bash
python ~/.agents/skills/ticket-to-tests/tools/create_tests_in_zephyr.py \
    --test-dir tests/items/create_item/ \
    --link-issue MYPRJ-42
```

## Step 4 — Tag test functions with Zephyr keys

```bash
python ~/.agents/skills/ticket-to-tests/tools/tag_tests_with_zephyr_keys.py \
    --responses zephyr_responses.json \
    --test-file tests/items/create_item/create_item_test.py
```

## Push execution results to Zephyr

```bash
python ~/.agents/skills/ticket-to-tests/tools/push_results_to_zephyr.py \
    --results-file test-results.xml \
    --zephyr-log zephyr_responses.json \
    --cycle-name "Create Item - QA-US - $(date +%Y-%m-%d)"
```

**Policy**: Always dry-run first. Never live-create without explicit user confirmation.
