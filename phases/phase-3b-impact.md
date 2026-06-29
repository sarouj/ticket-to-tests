# Phase 3b — Feature impact analysis

When a feature modifies behavior on an existing API endpoint, systematically probe related API
surfaces before finalizing test cases.

## Checklist — related API surfaces to evaluate

- **API adapter / proxy endpoint**: Does a facade, gateway, or BFF endpoint wrap the changed one?
- **Async event / message bus**: Does the changed operation emit the correct event type and payload?
- **Permission metadata field**: Does the `capabilities` field in GET responses reflect the change?
- **Permission inheritance**: If a parent entity's permissions change, do child entities reflect it?
- **Tenant / org-level access boundary**: Test cross-tenant isolation (BOLA) after the change.
- **Mixed-payload boundary**: Test each body field individually AND in combination.
- **Cross-entity scope**: Probe all entity types. Do not assume scope without testing.
- **Idempotency probing**: Repeating the operation — consistent outcome, never 5xx.
- **State-transition probing**: At least one invalid lifecycle state transition tested.
- **Pagination probing**: List endpoints reflect new state without phantom entries.
- **Secondary-ID features**: Secondary ID appears correctly in GET/PATCH response body fields.

## Exploratory test patterns

- **"Only this, not that"**: When ONE operation is unlocked, test every OTHER operation still blocked.
- **Mixed payload boundary**: Test payloads combining newly-allowed and still-blocked fields.
- **Cross-entity parity**: Write tests for all entity types; use PARAMETRIZE for identical logic.
  > See [ADAPTERS.md](../ADAPTERS.md) §PARAMETRIZE for your framework's syntax.
- **State preservation**: After the newly-allowed operation, verify entity lifecycle is unaffected.
- **Permission conflict probing**: Test revoking the actor's role mid-operation.
