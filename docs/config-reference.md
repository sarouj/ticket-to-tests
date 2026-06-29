# Configuration reference — team_config.yaml

`team_config.yaml` is the single configuration file that wires your project into the skill.
Place it at your project root. All tools read it automatically.

---

## Field reference table

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `jira.url` | string | Yes | — | Jira base URL |
| `jira.project_key` | string | Yes | — | Jira project key (e.g. `MYPRJ`) |
| `jira.component` | string | No | `""` | Component name for Jira issue creation |
| `zephyr.epic_folder_map` | dict | No | `{}` | Maps epic labels -> Zephyr folder names |
| `test_framework.name` | string | Yes | `pytest` | Framework adapter name |
| `test_framework.runner_cmd` | string | Yes | `python -m pytest {test_path} {flags}` | Test run command template |
| `test_framework.results_format` | string | No | `junit-xml` | Results format for Zephyr |
| `test_framework.file_pattern` | string | No | `**/*_test.*` | Test file discovery glob |
| `openapi.spec_path` | string | Recommended | `docs/openapi.yaml` | OpenAPI spec path |
| `context_dir` | string | No | `context/` | Context directory path |
| `test_dir_root` | string | No | `tests/` | Test root directory path |
| `auth.description` | string | No | `""` | Human-readable auth description |
| `auth.env_vars` | list | No | `[]` | Env vars required before running tests |
| `auth.verify_cmd` | string | No | `""` | Command to verify auth works |
| `deepeval.default_model` | string | No | `groq/llama-3.1-70b-versatile` | LLM judge for AI evaluation |

---

## Discovery order

1. Path passed explicitly via `--config <path>`
2. `team_config.yaml` in the current working directory
3. `team_config.yaml` in any parent directory up to the filesystem root

---

## Examples by framework

### pytest
```yaml
test_framework:
  name: "pytest"
  runner_cmd: "python -m pytest {test_path} -v --tb=short {flags}"
  file_pattern: "**/*_test.py"
```

### Jest
```yaml
test_framework:
  name: "jest"
  runner_cmd: "npx jest {test_path} --forceExit {flags}"
  file_pattern: "**/*.spec.ts"
```

### JUnit 5
```yaml
test_framework:
  name: "junit"
  runner_cmd: "mvn test -pl {test_path} {flags}"
  file_pattern: "**/*Test.java"
```

### Go
```yaml
test_framework:
  name: "go-test"
  runner_cmd: "go test {test_path} -v {flags}"
  file_pattern: "**/*_test.go"
```

### RSpec
```yaml
test_framework:
  name: "rspec"
  runner_cmd: "bundle exec rspec {test_path} --format progress {flags}"
  file_pattern: "**/*_spec.rb"
```
