# Adopting ticket-to-tests — installation and per-project wiring

This guide explains how to install the skill **once per developer machine** and wire it into
any number of projects with just three files.

---

## Step 1 — Install once per machine

```bash
mkdir -p ~/.agents/skills
git clone https://github.com/sarouj/ticket-to-tests ~/.agents/skills/ticket-to-tests
```

**Dependencies** (install once, globally or in a project venv):

```bash
pip install deepeval pyyaml requests
```

---

## Step 2 — Wire a new project (three files)

### 2a — Copy and fill in `team_config.yaml`

```bash
cp ~/.agents/skills/ticket-to-tests/templates/team_config.yaml team_config.yaml
```

Open `team_config.yaml` and fill in: `jira.url`, `jira.project_key`, `zephyr.epic_folder_map`,
`test_framework.name`, `test_framework.runner_cmd`, `openapi.spec_path`, `deepeval.default_model`.

See [docs/config-reference.md](docs/config-reference.md) for every field with types, defaults, and examples.

### 2b — Create your domain context document

```bash
mkdir -p context
cp ~/.agents/skills/ticket-to-tests/templates/ONBOARDING.template.md context/ONBOARDING.md
```

Fill in: domain glossary, resource hierarchy, auth flow, key project directories, Jira project link.

### 2c — Copy the Cursor routing rule

```bash
mkdir -p .cursor/rules
cp ~/.agents/skills/ticket-to-tests/templates/ticket-to-tests-skill.mdc .cursor/rules/ticket-to-tests-skill.mdc
```

> **Commit these three files** so all team members share the same config:
> ```
> git add team_config.yaml context/ONBOARDING.md .cursor/rules/ticket-to-tests-skill.mdc
> git commit -m "chore: wire ticket-to-tests skill"
> ```
>
> **Never commit** `.cursor/mcp.json` — it contains API tokens.

---

## Step 3 — Configure Jira access (mcp-atlassian)

Create `.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "mcp-atlassian": {
      "command": "uvx",
      "args": ["mcp-atlassian"],
      "env": {
        "JIRA_URL": "https://yourorg.atlassian.net",
        "JIRA_USERNAME": "your.email@yourorg.com",
        "JIRA_API_TOKEN": "<your-api-token>"
      }
    }
  }
}
```

Generate your API token at [id.atlassian.net/manage-profile/security/api-tokens](https://id.atlassian.net/manage-profile/security/api-tokens).

Open Cursor → Settings → MCP panel — `mcp-atlassian` should turn green.

---

## Step 4 — Verify

```bash
python ~/.agents/skills/ticket-to-tests/tools/evaluate_test_quality.py --help
python ~/.agents/skills/ticket-to-tests/tools/team_config.py
```

---

## Step 5 — Start

Open a Cursor chat and paste:
```
I want to write tests for [PROJ-XXX]. Please start the ticket-to-tests workflow.
```

For a full 15-minute walkthrough, see [docs/quick-start.md](docs/quick-start.md).

---

## Multiple projects — same machine

Repeat Steps 2–4 for each project. All projects share the single installation at
`~/.agents/skills/ticket-to-tests/`. Each project has its own `team_config.yaml`.

---

## Troubleshooting adoption

| Symptom | Fix |
|---|---|
| `ConfigNotFoundError` when running tools | Make sure `team_config.yaml` is in your project root |
| Cursor does not invoke the skill | Check `.cursor/rules/ticket-to-tests-skill.mdc` exists with `alwaysApply: true` |
| `mcp-atlassian` shows red in Cursor | Check `JIRA_API_TOKEN` in `.cursor/mcp.json`; regenerate if expired |
| Tool outputs `WARNING: unconfigured required fields` | Open `team_config.yaml` and replace all placeholder values |
| `deepeval` not installed | Run `pip install deepeval` |
| `pyyaml` not installed | Run `pip install pyyaml` |

For more issues, see [docs/troubleshooting.md](docs/troubleshooting.md).
