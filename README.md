# ticket-to-tests

> **Language- and framework-agnostic test automation skill for AI coding agents.**
> From Jira ticket to production-quality test code in minutes — not hours.

---

## What it does

`ticket-to-tests` is a Cursor Agent skill that orchestrates an end-to-end workflow:

```
Jira ticket / OpenAPI spec
        │
        ▼
  [Phase 1] Load context (ONBOARDING.md + OpenAPI spec + existing tests)
        │
        ▼
  [Phase 2] Fetch Jira AC, linked stories, and related tickets
        │
        ▼
  [Phase 3] Generate test cases (T1 happy path → T2 BVA + errors → T3 advanced)
        │
        ▼
  [Phase 4] Validate against spec (endpoint coverage, OWASP checks)
        │
        ▼
  [Phase 5] Implement test code using your framework adapter
        │
        ▼
  [Phase 5b] DeepEval quality loop (AI-scored rubric → auto-fix → re-score)
        │
        ▼
  [Phase 5c] Run tests → triage failures → file Jira bugs
        │
        ▼
  [Phase 6] Sync to Zephyr Scale (dry-run → confirm → live create)
        │
        ▼
  [Phase 7] Holistic review + AI evaluation scores
```

Works with **any REST API** and **any testing stack**. All language-specific syntax lives in **[ADAPTERS.md](ADAPTERS.md)**.

---

## 3-command quick install

```bash
git clone https://github.com/sarouj/ticket-to-tests ~/.agents/skills/ticket-to-tests
cp ~/.agents/skills/ticket-to-tests/templates/team_config.yaml team_config.yaml
cp ~/.agents/skills/ticket-to-tests/templates/ONBOARDING.template.md context/ONBOARDING.md
cp ~/.agents/skills/ticket-to-tests/templates/ticket-to-tests-skill.mdc .cursor/rules/ticket-to-tests-skill.mdc
```

See [ADOPTING.md](ADOPTING.md) for the full guide.

---

## Documentation map

| Goal | Read |
|---|---|
| Install and wire a new project | [ADOPTING.md](ADOPTING.md) |
| 15-minute end-to-end walkthrough | [docs/quick-start.md](docs/quick-start.md) |
| Understand the 7-phase workflow | [docs/concepts.md](docs/concepts.md) |
| All `team_config.yaml` fields | [docs/config-reference.md](docs/config-reference.md) |
| Add your test framework | [docs/how-to/customize-adapter.md](docs/how-to/customize-adapter.md) |
| Run the AI evaluation script | [docs/how-to/evaluate-test-quality.md](docs/how-to/evaluate-test-quality.md) |
| Sync to Zephyr Scale | [docs/how-to/sync-to-zephyr.md](docs/how-to/sync-to-zephyr.md) |
| Integrate into CI/CD | [docs/how-to/integrate-with-ci.md](docs/how-to/integrate-with-ci.md) |
| Fix a broken setup | [docs/troubleshooting.md](docs/troubleshooting.md) |
| Framework syntax reference | [ADAPTERS.md](ADAPTERS.md) |

*ticket-to-tests v1.0.0 — language-agnostic generalized release*
