# Phase reference — inputs, outputs, exit criteria

| Phase | Input | Output | Exit criteria |
|---|---|---|---|
| Phase 1 | `context/ONBOARDING.md`, test tree, OpenAPI spec | Context summary | Domain understood; spec loaded |
| Phase 2 | Jira ticket URL | ACs, scope, TARGET_ENV | ACs extracted; TARGET_ENV confirmed |
| Phase 3 | ACs + OpenAPI spec | Numbered test plan | All ACs covered; T1/T2/T3 tier requirements met |
| Phase 3b | Phase 3 plan + feature diff | Impact checklist + additional test cases | All 11 impact areas evaluated |
| Phase 4 | Phase 3 plan | Reviewed plan | Every AC has a test; T2 gate passed |
| Phase 5 | Approved test plan | Test files | All tests implemented and collected |
| Phase 5b | Test files + AC text + spec | deepeval_report.json | All 4 metrics >= threshold (or max 3 iterations) |
| Phase 5c | Test files + TARGET_ENV | Run summary + Jira bug keys | All tests pass or xfail; user confirms |
| Phase 6 | Test files + Zephyr config | Zephyr test cases + zephyr_responses.json | Dry-run reviewed; user confirmed; links verified |
| Phase 7 | All outputs | Pass / Pass-with-gaps / Fail verdict | Manual rubric complete; deepeval scores recorded |
| Phase 7b | deepeval_report.json | evaluation-rubric.md updated | Scores pasted into rubric |
