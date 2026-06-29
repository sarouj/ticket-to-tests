# pytest examples

Copy-paste-ready test patterns for Python/pytest REST API test suites.
All examples use generic API domains (`items`, `projects`) — adapt to your service.

## Files

| File | Pattern | Concepts |
|---|---|---|
| `bva_parametrize.py` | Boundary value analysis | PARAMETRIZE, ASSERT_CONTRACT |
| `error_contract.py` | Error response validation | ASSERT_CONTRACT |
| `idempotency.py` | Idempotency probing | T3 behavioral |
| `owasp.py` | BOLA, mass assignment, security headers | OWASP API Top 10 |
| `pagination.py` | Multi-page traversal + count invariant | T3 pagination |
| `performance.py` | SLA assertion | T3 performance |
| `property_based.py` | Hypothesis property-based tests | T2 complex input spaces |

---

## Key patterns

### PARAMETRIZE (BVA)

```python
@pytest.mark.parametrize("name, expected_status, expected_code", [
    ("a",       201, None),
    ("a" * 255, 201, None),
    ("a" * 256, 400, "VALIDATION_ERROR"),
    ("",        400, "VALIDATION_ERROR"),
    ("   ",     400, "VALIDATION_ERROR"),
    (None,      400, "VALIDATION_ERROR"),
])
def test_create_item_name_boundary(self, session, project, name, expected_status, expected_code):
    _, response = create_item(session=session, projectId=project.id, name=name)
    assert_status(response, expected_status)
    if expected_code:
        assert_error(response, {"type": "API_ERROR", "code": expected_code})
```

### SETUP_SCOPE (shared vs per-test)

```python
# Read-only tests — session scope (created once)
@pytest.fixture(scope="session")
def item_for_read(session, project_session):
    data, _ = create_item(session=session, projectId=project_session.id, name="read-only-item")
    yield data

# Mutating tests — function scope (fresh per test)
@pytest.fixture
def item_for_delete(session, project_function):
    data, _ = create_item(session=session, projectId=project_function.id, name="delete-me")
    yield data
    delete_item(session=session, itemId=data.id)  # cleanup
```

### ASSERT_CONTRACT

```python
# Always assert BOTH status code AND error body for non-2xx
assert_status(response, 409)
assert_error(response, {"type": "API_ERROR", "code": "CONFLICT"})
```

### OWASP BOLA

```python
def test_cross_tenant_access_returns_403(self, session, other_session, project):
    """BOLA: second session cannot access first session's resource."""
    data, _ = create_item(session=session, projectId=project.id, name="my-item")
    _, response = get_item(session=other_session, itemId=data.id)
    assert_status(response, 403)  # or 404
    assert response.status_code not in (200, 201)
```
