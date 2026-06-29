# Phase 1 — Context loading

1. **Read team context first** (see `context/ONBOARDING.md` in the project root).
   Path is set in `team_config.yaml → context_dir`.

2. **Read the OpenAPI spec** from `team_config.yaml → openapi.spec_path`.

3. **Explore the test tree** (readonly) under `team_config.yaml → test_dir_root` for patterns:
   - How SETUP_SCOPE helpers are named and structured.
   - How ASSERT_CONTRACT helpers are called.
   - How TEST_METADATA tags are applied.
   - How test files are named and organized.

   > See [ADAPTERS.md](../ADAPTERS.md) for the syntax patterns of your framework.

4. If `context/` or the ticket names additional spec paths or design documents, follow those.

---

# Phase 2 — Requirement intake (Jira)

- Use **mcp-atlassian** only: fetch the Jira issue, acceptance criteria, links, and related issues.
  Never call the Jira REST API directly from agent code.

**Target Environment intake (required):**

Before leaving Phase 2, confirm which environment tests will run against. Ask the user if not already
specified. Store as `TARGET_ENV`.

| Value | Typical meaning |
|---|---|
| `DEV` | Development — shared or local; fast feedback, least stable |
| `QA` | Quality assurance — shared, more stable |
| `QA-US` | QA in US region |
| `QA-EU` | QA in EU region |
| `STAGING` | Pre-production — matches production config |
| `PROD` | Production — **never run destructive tests here** |

If the user does not specify, default to `QA` and confirm before proceeding to Phase 3.
