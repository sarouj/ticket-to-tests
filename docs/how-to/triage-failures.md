# How to triage test failures

---

## The triage decision tree

```
Test fails
    |
    +-- Failure in test setup (auth, missing data)? -> Fix test setup
    |
    +-- Test asserting wrong thing (spec mismatch)? -> Fix the test
    |
    +-- API returns documented error for expected condition?
    |       -> Mark SKIP_XFAIL with Jira ticket reference
    |       -> File Jira bug if no ticket exists
    |
    +-- API returns 5xx, undocumented error, or wrong data?
            -> File Jira bug + Mark SKIP_XFAIL
```

---

## Failure categories

| Category | Symptom | Action |
|---|---|---|
| Auth / setup error | 401 on every request | Fix env vars / auth |
| Test data problem | 404 on resource that should exist | Fix test setup helpers |
| API regression | 5xx; wrong response body | File Jira bug |
| Spec mismatch | API returns 422 but test expects 400 | Update test; clarify spec |
| Flaky test | Fails ~20% of the time | Mark `xfail(strict=False)` |

---

## Mark failing tests as SKIP_XFAIL

**pytest:**
```python
@pytest.mark.xfail(reason="MYPRJ-456 — known API bug", strict=True)
def test_create_item_with_emoji_name_returns_400(self, ...):
    ...
```

**Jest:**
```typescript
it.skip("POST item — emoji name returns 400 (MYPRJ-456 — known bug)", async () => { ... });
```

**JUnit:**
```java
@Disabled("MYPRJ-456 — known API bug")
@Test void testCreateItemWithEmojiNameReturns400() { ... }
```

**Go:**
```go
func TestCreateItemWithEmojiNameReturns400(t *testing.T) {
    t.Skip("MYPRJ-456 — known API bug")
}
```
