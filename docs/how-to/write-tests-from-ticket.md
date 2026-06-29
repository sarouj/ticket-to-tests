# How to write tests from a Jira ticket

---

## Prerequisites

- `team_config.yaml` configured at project root
- `context/ONBOARDING.md` describes your domain
- `mcp-atlassian` configured in `.cursor/mcp.json`
- Test environment accessible

---

## The starter prompt

```
Run the ticket-to-tests skill for ticket MYPRJ-123.
Target environment: QA-US
Framework: pytest
```

Optionally skip phases already done:
```
Run the ticket-to-tests skill for MYPRJ-123. Skip phases 1-2. Start at Phase 3.
```

---

## Providing additional context

If the Jira ticket lacks detailed AC, provide context inline:

```
Run the ticket-to-tests skill for MYPRJ-123.

Additional context:
- Endpoint: POST /v2/items
- name: string, max 255 chars, required, unique per project
- type: enum TASK|BUG|STORY, required
- Unauthenticated → 401 UNAUTHORIZED
- Duplicate name → 409 CONFLICT

Target environment: QA-US
```

---

## Reviewing the test plan

The agent pauses after Phase 3. Review carefully:
- **T1**: Does each AC have at least one test?
- **T2**: Are all parameters covered with BVA? All error codes covered?
- **T3**: Are idempotency, OWASP, and pagination tests appropriate?

Ask the agent to adjust: `"Add a test for 404 when the project does not exist."`

---

## Writing tests from an OpenAPI spec (no ticket)

```
Run the ticket-to-tests skill for endpoint: POST /v2/items
OpenAPI spec: docs/openapi.yaml
No Jira ticket — skip Phase 2.
Target environment: QA-US
Framework: jest
```

---

## Troubleshooting

| Problem | Fix |
|---|---|
| "no AC found in ticket" | Paste AC directly in the prompt under "Additional context" |
| Agent can't find OpenAPI spec | Check `openapi.spec_path` in `team_config.yaml` |
| Agent generates Python when you want Jest | Set `test_framework.name: jest` in `team_config.yaml` |
| Tests fail immediately | Run `auth.verify_cmd` to check auth |
