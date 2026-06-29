# Phase 5c — Test execution and bug triage

Run the automation tests against `TARGET_ENV`, verify all new tests execute correctly,
triage any failures, and gate Phase 6 on a clean or user-confirmed run.

## 5c-a. Run automation tests

Use `team_config.yaml → test_framework.runner_cmd` with `{test_path}` and `{flags}` substituted.
Verify auth first: run `team_config.yaml → auth.verify_cmd`.

> See [ADAPTERS.md](../ADAPTERS.md) §TEST_RUNNER_CMD for your framework's full command options.

## 5c-b. Verify automation changes

- All new tests from Phase 5 were collected (no collection errors, import failures).
- New tests pass in `TARGET_ENV`.
- Apply SKIP_XFAIL with a specific reason for environment-specific skips.
  > See [ADAPTERS.md](../ADAPTERS.md) §SKIP_XFAIL for syntax.

## 5c-c. Find and catch bugs

For each failed test: classify as **server bug**, **spec drift**, or **test code issue**.
Apply the §3j checklist from [phase-3-design.md](phase-3-design.md).

## 5c-d. Confirm and file bugs

For each confirmed server bug, ask the user before filing:
> "I found a potential bug: `<summary>`. Shall I create a Jira bug in `<project_key>`? (yes / no)"

If yes, create via `mcp-atlassian`. Pass `component` from `team_config.yaml → jira.component` if set.
Annotate the failing test with SKIP_XFAIL + bug key.

> See [ADAPTERS.md](../ADAPTERS.md) §SKIP_XFAIL for the exact annotation syntax.

## Gate to Phase 6

- **All new tests pass** → proceed to Phase 6 automatically.
- **Failures remain** → ask the user before proceeding. Never auto-proceed with unresolved failures.
