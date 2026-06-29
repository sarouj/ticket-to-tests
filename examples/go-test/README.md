# Go testing examples

Stub patterns for Go test suites.
Adapt imports and helper names to your project's HTTP client package.

---

## PARAMETRIZE (table-driven tests)

```go
func TestCreateItemNameBoundary(t *testing.T) {
    cases := []struct {
        name           string
        expectedStatus int
        expectedCode   string
    }{
        {"a",          201, ""},
        {strings.Repeat("a", 255), 201, ""},
        {strings.Repeat("a", 256), 400, "VALIDATION_ERROR"},
        {"",           400, "VALIDATION_ERROR"},
        {"   ",        400, "VALIDATION_ERROR"},
    }
    for _, tc := range cases {
        tc := tc
        t.Run(tc.name, func(t *testing.T) {
            resp := createItem(t, tc.name)
            assertStatus(t, resp, tc.expectedStatus)
            if tc.expectedCode != "" {
                assertErrorCode(t, resp, tc.expectedCode)
            }
        })
    }
}
```

---

## SETUP_SCOPE (TestMain / t.Cleanup)

```go
// Read-only — package-level setup (TestMain)
var sharedItem Item
func TestMain(m *testing.M) {
    sharedItem = createItem(nil, "shared")
    code := m.Run()
    deleteItem(nil, sharedItem.ID)
    os.Exit(code)
}

// Mutating — per-test (t.Cleanup)
func TestDeleteItem(t *testing.T) {
    item := createItem(t, "delete-me")
    t.Cleanup(func() { deleteItem(t, item.ID) }) // runs even if test fails
    resp := deleteItem(t, item.ID)
    assertStatus(t, resp, 200)
}
```

---

## ASSERT_CONTRACT

```go
assertStatus(t, resp, 409)
body := parseBody(t, resp)
assert.Equal(t, "API_ERROR", body["type"])
assert.Equal(t, "CONFLICT", body["code"])
```

---

## SKIP_XFAIL

```go
func TestCreateItemEmojiNameReturns400(t *testing.T) {
    t.Skip("PROJ-456 — POST /items returns 500 for emoji names (API bug)")
    ...
}
```

---

## TEST_METADATA

```go
// Use build tags for grouping
//go:build integration
// +build integration

// Use t.Log for test tracing to Jira
func TestCreateItemReturns201(t *testing.T) {
    t.Log("PROJ-42 — AC1: Successful create returns 201")
    ...
}
```
