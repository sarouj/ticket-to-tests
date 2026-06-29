# Phase 3 — Generate test cases

> **Language-agnostic.** This phase describes *what* to test. For *how* to write it in your
> framework, see [ADAPTERS.md](../ADAPTERS.md) for your stack.
> All concept terms used here (PARAMETRIZE, SETUP_SCOPE, SKIP_XFAIL, ASSERT_CONTRACT) are
> defined in [SKILL.md](../SKILL.md#language-agnostic-concept-terms).

Output structured cases (Given/When/Then, operations, status codes, negatives) by following the
workflow below.

## 3a. Parse the source

Read the provided spec, API definition, or Jira issue and extract:
- Endpoints/operations (for API specs)
- Required/optional parameters, request/response schemas
- Acceptance criteria, expected behavior, error conditions (from docs or Jira)

**OpenAPI cross-reference (mandatory):** After extracting test cases, open the spec from
`team_config.yaml → openapi.spec_path` and, for each affected endpoint, list every documented
response status code. Any code in the spec that has no corresponding test is a gap — add it to the
test plan before moving to Phase 3b. This prevents "response code drift" where the API documents a
412 or 409 but no test covers it.

## 3b. Map to test categories

For each requirement or operation, plan tests across the three quality tiers defined in
[Section 3i](#3i-test-quality-tiers). Use the tier labels below to decide which tests are mandatory.

**T1 — Baseline (required for every test)**

- **Happy path**: Valid inputs, expected success response and side effects.
- **Documented errors**: Every 4xx/5xx code listed in the spec has at least one test; each must
  call ASSERT_CONTRACT — status code assertion AND error body assertion.
  > See [ADAPTERS.md](../ADAPTERS.md) §ASSERT_CONTRACT

**T2 — Boundary (required for every new endpoint or request parameter)**

- **Boundary value analysis (BVA)**: For every string/numeric parameter, test:
  minimum valid value; maximum valid value; just-over-maximum (expect 400/422);
  null/empty when required (expect 400); whitespace-only string (expect 400).
  For enum parameters, test an unknown enum value (expect 400).
  Use PARAMETRIZE to express these boundary cases in a single data-driven test.
  > See [ADAPTERS.md](../ADAPTERS.md) §PARAMETRIZE

- **Property-based testing**: For parameters with non-trivial validation rules — complex
  allowed-character sets, encoded path segments, or large numeric ranges — use property-based
  testing (e.g. Hypothesis for Python, fast-check for TypeScript, gopter for Go) to generate
  adversarial inputs automatically.

- **Negative/malformed input**: Missing required fields; wrong data type; extra/undocumented fields
  in the request body; malformed JSON body (expect 400/422 for each).
- **Auth/authorization failures**: Unauthenticated request (expect 401); request with insufficient
  role (expect 403).

**T3 — Behavioral (required for every mutable resource operation)**

- **Idempotency**: DELETE called twice must return 404 or 409 on the second call — never 5xx.
- **State-machine / lifecycle transitions**: Test invalid transitions explicitly.
- **HTTP semantics**: Unsupported HTTP method → 405. Wrong Content-Type → 415. Malformed JSON → 400.
- **Response headers**: Every 2xx test must assert `Content-Type: application/json`.
- **Pagination completeness**: Single-page, multi-page traversal, count invariant.
- **Performance SLA assertions**: Assert `elapsed_time < SLA_THRESHOLD` as a test — not a log.

**Security (OWASP API Top 10) — required for every new or modified endpoint:**

- **BOLA**: Use a second session to attempt access to another tenant's resource. Assert 403/404.
- **Mass Assignment**: Send undocumented/read-only fields. Verify they are rejected or ignored.
- **Security response headers**: Assert no `X-Powered-By`, `X-AspNet-Version` etc. in 2xx responses.

**Alternate-ID features:**
- Cross-ID isolation, caller restrictions, format validation via PARAMETRIZE, equal resource-type coverage.

**Contract/schema**: Response shape, required fields, status codes per spec.

## 3c. Align with existing project

Before writing tests:
- Check existing test layout and naming conventions (explored in Phase 1).
- Reuse SETUP_SCOPE helpers, ASSERT_CONTRACT helpers, and shared setup already in the test tree.
- Match TEST_METADATA tags (epic/feature/story/severity) and test structure to the project's convention.

## 3d. Implement tests

Write one or more test modules that:
- Have clear, spec-based test names and docstrings (name the scenario and expected outcome)
- Assert status codes, response bodies/schemas, and side effects as per the spec
- Use SETUP_SCOPE helpers rather than creating resources inline in the test body
- Use PARAMETRIZE for data-driven boundary cases
- Link to the Jira story via TEST_METADATA tags

## 3e. ASSERT_CONTRACT — error response validation

Every test that checks an API response body must use the project's HTTP assertion helpers.

**For every non-2xx test, ALWAYS call BOTH:**
1. Status code assertion
2. Error body assertion

**For 2xx tests:**
- Assert status code.
- Assert response body shape: required fields present, correct types, correct values.
- Assert `Content-Type: application/json` header on every 2xx response.

> See [ADAPTERS.md](../ADAPTERS.md) §ASSERT_CONTRACT for syntax in your framework.

## 3f. SETUP_SCOPE — test data and setup helpers

Tests **must** obtain test data from SETUP_SCOPE helpers rather than creating resources inline.

| Scope | When to use |
|---|---|
| **Shared read-only setup** | Tests that only read (GET, list, download) |
| **Per-test mutating setup** | Tests that create, update, delete, or mutate |
| **Factory helper** | Custom parameters needed per test |

**Scope selection rules:**
1. Read-only tests: use shared setup.
2. Mutating tests: use per-test setup with cleanup.
3. Never create API resources directly in the test body.
4. Always include teardown/cleanup in per-test setup.

> See [ADAPTERS.md](../ADAPTERS.md) §SETUP_SCOPE for your framework's exact syntax.

## 3g. Version gating and flakiness handling

**Version gating:** Use a conditional SKIP_XFAIL mechanism tied to API/service version.

**Flakiness quarantine rule:** Retry → quarantine directory → track via Jira → remove once fixed.

> See [ADAPTERS.md](../ADAPTERS.md) §SKIP_XFAIL for your framework's version-gate syntax.

### Source-specific guidance

**API specification (OpenAPI / YAML)**
- Derive test cases from each path + method: success (2xx), client errors (4xx), server errors (5xx).
- Validate response schema: required fields, types, nested objects.
- Test path/query/header parameters: required vs optional, enums, formats.

**Jira tickets**
- Turn acceptance criteria and "Given/When/Then" into discrete test cases.
- Reference the ticket key in test names or docstrings.

**Reference documentation**
- **Read design docs in full** — edge cases and constraints are often buried in appendices.
- **Include reviewer comments** — inline review comments clarify intent.
- Extract MUST/SHOULD/MUST NOT statements into testable requirements.

### Test case naming and structure

- **Name**: Describe the scenario and expected outcome.
- **Docstring**: One sentence tying the test to the spec or ticket.
- Prefer one logical assertion focus per test; use PARAMETRIZE for multiple inputs.

### Checklist before delivering Phase 3

- [ ] Every acceptance criterion or documented behavior has at least one test.
- [ ] Success and every documented error response (4xx/5xx) are covered.
- [ ] Tests use existing project SETUP_SCOPE helpers — no inline resource creation.
- [ ] TEST_METADATA tags (epic/feature/story/severity) are applied correctly.
- [ ] Test names and docstrings make the trace to the spec or ticket clear.
- [ ] **T2 gate**: BVA tests (min/max/over-max/null/whitespace/unknown-enum) using PARAMETRIZE.
- [ ] **T2 gate**: Every non-2xx test calls ASSERT_CONTRACT — status code AND error body.
- [ ] **T2 gate**: Every 2xx test asserts `Content-Type: application/json`.
- [ ] **T3 gate** (mutable operations only): DELETE called twice returns 404/409, not 5xx.
- [ ] **T3 gate** (mutable operations only): At least one invalid state-machine transition tested.
- [ ] **T3 gate** (list operations only): Pagination tests cover single-page, multi-page, count invariant.
- [ ] **OWASP gate**: BOLA, mass-assignment, and security-headers tests are included.

> For concrete examples of spec-to-test mapping, see [examples/](../examples/) for your framework.

## 3h. Team SDK / client library mandate

**Always use the team's SDK or client library.** Never issue raw HTTP calls directly in test code.

The team's SDK/client library is documented in `context/ONBOARDING.md`.

## 3i. Test quality tiers

| Tier | Mandatory test types | When required |
|---|---|---|
| **T1 — Baseline** | Happy path + every documented 4xx/5xx with ASSERT_CONTRACT | Every test, no exceptions |
| **T2 — Boundary** | BVA (min/max/over-max/null/whitespace/unknown-enum) using PARAMETRIZE + auth failures | Every new endpoint or request parameter |
| **T3 — Behavioral** | Idempotency + state-machine transitions + HTTP semantics + Content-Type + pagination | Every mutable resource operation |

## 3j. Server bug detection — do not assume, investigate

When a test assertion fails because the server response deviates from the published error contract,
**treat it as a potential server bug first**.

### Automation data issue checklist

| # | Check |
|---|---|
| 1 | Resource is in the expected state at call time |
| 2 | SETUP_SCOPE matches mutability |
| 3 | Precondition matches the AC being tested |
| 4 | SKIP_XFAIL markers are still justified |
| 5 | Teardown restores state |

**When a bug is confirmed:**
1. **File a Jira bug** via `mcp-atlassian` with Summary, Steps, Current/Expected Behaviour, Impact.
2. **Add the bug key** via TEST_METADATA.
3. **Mark with SKIP_XFAIL** with reason: bug key + one-line summary.

> See [ADAPTERS.md](../ADAPTERS.md) §SKIP_XFAIL for your framework's exact syntax.

---

## Phase 4 — Review test cases (narrow)

Checklist: AC coverage, negative paths, contract/schema — test design only. No code changes.

- Every AC from the Jira ticket has at least one planned test.
- T1/T2/T3 tier requirements are met for the operation type.
- OWASP security tests are planned for modified endpoints.
- SETUP_SCOPE strategy is appropriate (shared for read-only, per-test for mutating).
- PARAMETRIZE is planned for all BVA boundary cases.
