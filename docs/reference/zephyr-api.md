# Zephyr Scale API constraints

Known constraints and workarounds for the Zephyr Scale REST API.

---

## Known constraints

| Endpoint | Status | Notes |
|---|---|---|
| `POST /rest/tests/1.0/testcase` | Working | Creates individual test cases |
| `POST /rest/atm/1.0/automation/execution/{projectKey}` | Working | Bulk automation results |
| `GET /rest/atm/1.0/testcase/{key}` | Working | Read test case details |
| `PUT /rest/atm/1.0/testcase/{key}` | Working | Update test case fields |
| `issueLinks` on POST creation | **Silently dropped** | Use `verify_and_fix_issue_links()` post-creation |
| Source matching in automation API | Framework-dependent | Only matches test cases created by the automation API |
| Duplicate test names | **Causes 500** | Ensure test names are unique within a Zephyr project |
| `executionTime` field | **Causes 400** | Do not include execution time in automation JSON |
| Special characters in test names | May cause 400 | Avoid `&`, `<`, `>`, `:`, `(`, `)` in test titles |

---

## `issueLinks` workaround

The Zephyr Scale creation API silently drops `issueLinks` even when included in the request body.
`create_tests_in_zephyr.py` automatically runs `verify_and_fix_issue_links()` post-creation
using a `PUT` call to restore the links.

Always check the summary:
```
Issue link verification: N already linked, M fixed, 0 failed.
```

If `failed > 0`, fix manually via the Zephyr Scale UI (open test case → Link Issues).

---

## Two types of test cases

1. **Manually created** (via `create_tests_in_zephyr.py`): Full test cases with steps and objectives.
   Linked to Jira stories. Serve as **documentation and traceability**.

2. **Automation-created** (via `push_results_to_zephyr.py`): Named by function name, linked to
   test cycles with execution results. Serve as **execution reporting**.

Both types are legitimate. Do not confuse them.
