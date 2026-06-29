# Zephyr Scale, Jira (mcp-atlassian), and Jira↔test mapping

## Jira — use mcp-atlassian only

For **issues** (read, search, comment, transition): use **`call_mcp_tool`** with **`server: mcp-atlassian`**.
Never call the Jira REST API directly from agent code.

Credentials are read from `.cursor/mcp.json` under the `mcp-atlassian` server's `env` block
(`JIRA_USERNAME`, `JIRA_API_TOKEN`). Never prompt the user to re-enter credentials configured there.

### Component on every bug/issue

If `team_config.yaml → jira.component` is set, **always** pass `components: <component>` on every
`jira_create_issue` and `jira_update_issue` call.

---

## Zephyr Scale — create test cases from your test suite

Script: [tools/create_tests_in_zephyr.py](tools/create_tests_in_zephyr.py)

- **Epic → folder mapping**: reads `team_config.yaml → zephyr.epic_folder_map`.
- Logs responses to `zephyr_responses.json` and `zephyr_responses.log`.
- Credentials are read from `.cursor/mcp.json`.

### Full creation + tagging workflow

```bash
# Step 1 — dry run
python ~/.agents/skills/ticket-to-tests/tools/create_tests_in_zephyr.py \
  --test-dir <path/to/tests> --dry-run

# Step 2 — create for real (after user confirmation)
python ~/.agents/skills/ticket-to-tests/tools/create_tests_in_zephyr.py \
  --test-dir <path/to/tests> --link-issue <PROJECT-XXXX>

# Step 3 — preview tag insertion
python ~/.agents/skills/ticket-to-tests/tools/tag_tests_with_zephyr_keys.py \
  --responses zephyr_responses.json --test-file <path> --dry-run

# Step 4 — apply tags
python ~/.agents/skills/ticket-to-tests/tools/tag_tests_with_zephyr_keys.py \
  --responses zephyr_responses.json --test-file <path>
```

**Dry-run policy:** Never create live test cases without explicit user confirmation.

---

## `issueLinks` caveat

The Zephyr Scale creation API silently drops the `issueLinks` field. The script automatically runs
`verify_and_fix_issue_links()` post-creation. Check the summary:

```
Issue link verification: N already linked, M fixed, 0 failed.
```

If `failed > 0`, fix manually via the Zephyr Scale UI.

---

## Phase B2 — Push results after test run

```bash
python ~/.agents/skills/ticket-to-tests/tools/push_results_to_zephyr.py \
  --results-file test-results.xml \
  --zephyr-log zephyr_responses.json \
  --key-range <PROJECT-Txxxx>:<PROJECT-Txxxx>
```

Use `--dry-run` to preview the payload without uploading.
