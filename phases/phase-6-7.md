# Phase 6 — Zephyr alignment

**Prerequisite:** Phase 5c must have exited with a passing run before running the Zephyr export.

Run [tools/create_tests_in_zephyr.py](../tools/create_tests_in_zephyr.py) — always dry-run first.
See [zephyr-and-jira.md](../zephyr-and-jira.md) for the full commands and workflow.

**Dry-run:**
```bash
python ~/.agents/skills/ticket-to-tests/tools/create_tests_in_zephyr.py \
    --test-dir <path> --dry-run
# Reads jira.url, project_key, component, zephyr.epic_folder_map from team_config.yaml
```

Review dry-run output, then ask the user:
> "Dry-run output looks correct — N test cases ready to create. Proceed with live creation in Zephyr? (yes/no)"

**`issueLinks` caveat:** The script automatically runs `verify_and_fix_issue_links()` post-creation.
Check: `Issue link verification: N already linked, M fixed, 0 failed.`

After live creation, regenerate the Jira ↔ test mapping:
```bash
python ~/.agents/skills/ticket-to-tests/tools/generate_jira_automation_mapping.py
```

---

# Phase 7 — Evaluation (holistic)

Task `generalPurpose` (readonly) using the rubric in [evaluation-rubric.md](../evaluation-rubric.md).

Any `# DEEPEVAL GAPS` comment block left by the Phase 5b loop is a must-fix item.

Verdict: **Pass** / **Pass with gaps** / **Fail** — must-fix before merge.

---

# Phase 7b — Record deepeval scores

Paste the final `deepeval_report.json` scores into [evaluation-rubric.md](../evaluation-rubric.md) Section 6.

---

# Phase 8 (engineering)

- **B2:** Push results to Zephyr:
  ```bash
  python ~/.agents/skills/ticket-to-tests/tools/push_results_to_zephyr.py \
      --results-file <junit-xml-results-file>
  ```

- **B3 — API coverage tracking:**
  ```bash
  python ~/.agents/skills/ticket-to-tests/tools/update_api_coverage.py
  ```

- **B4 — Schemathesis contract run:**
  ```bash
  bash ~/.agents/skills/ticket-to-tests/tools/run_schemathesis.sh "<endpoint-path>"
  ```
  Zero failures required before merge.
