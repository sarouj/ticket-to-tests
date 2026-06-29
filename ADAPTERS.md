# ADAPTERS.md — Framework adapter contract

> **This is the only file in the skill where language-specific syntax lives.**

## The 7 adapter slots

| Slot | Neutral concept | Purpose |
|---|---|---|
| `TEST_RUNNER_CMD` | Run a subset of tests | Filter and run specific tests via CLI |
| `TEST_METADATA` | Attach labels/tags | Tag tests with epic, feature, story, severity |
| `PARAMETRIZE` | Data-driven tests | Multiple inputs/outputs in one test function |
| `SETUP_SCOPE` | Shared vs per-test setup | Shared read-only vs per-test mutating setup |
| `SKIP_XFAIL` | Mark a known failure | Annotate as expected-to-fail without deleting |
| `ASSERT_CONTRACT` | Status + error body | Both status code AND error body assertion |
| `RESULTS_FORMAT` | Output format | Format consumed by Zephyr push tools |

---

## Adapter: pytest (Python)

**Complete reference implementation.**

### TEST_RUNNER_CMD
```bash
python -m pytest tests/path/to/feature_test.py -v
python -m pytest tests/ -k "test_create_item"
python -m pytest tests/ -m "regression"
```
```yaml
runner_cmd: "python -m pytest {test_path} {flags}"
file_pattern: "**/*_test.py"
```

### TEST_METADATA
```python
import allure, pytest

@allure.epic("ITEMS")
@allure.feature("Item CRUD")
class TestCreateItem:
    @allure.story("PROJ-123")
    @allure.title("Create item returns 201")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.regression
    def test_create_item_returns_201(self, ...):
        ...
```

### PARAMETRIZE
```python
@pytest.mark.parametrize("name, expected_status, expected_code", [
    ("valid-name",   201, None),
    ("a" * 256,      400, "VALIDATION_ERROR"),
    ("",             400, "VALIDATION_ERROR"),
    ("   ",          400, "VALIDATION_ERROR"),
    (None,           400, "VALIDATION_ERROR"),
])
def test_create_item_name_boundary(self, client, name, expected_status, expected_code):
    _, response = client.create_item(name=name)
    assert_status_code(response, expected_status)
    if expected_code:
        assert_error(response, {"type": "API_ERROR", "code": expected_code})
```

### SETUP_SCOPE
```python
# conftest.py

@pytest.fixture(scope="session")
def existing_item_session(test_session, workspace_session):
    """Session-scoped: for read-only tests."""
    data, _ = client.create_item(session=test_session, name="shared-item")
    return data

@pytest.fixture(scope="function")
def item_function(test_session, workspace_session):
    """Function-scoped: for mutating tests."""
    data, _ = client.create_item(session=test_session, name="temp-item")
    yield data
    client.delete_item(session=test_session, item_id=data.id)
```

### SKIP_XFAIL
```python
@pytest.mark.xfail(strict=True, reason="PROJ-999: returns 500 instead of 404")
def test_get_nonexistent_item_returns_404(self, ...):
    ...

@pytest.mark.skipif(api_version() < (2, 1, 0), reason="Requires API v2.1+")
def test_rate_limit_header_present(self, ...):
    ...
```

### ASSERT_CONTRACT
```python
# 2xx
assert_status_code(response=response, expected_code=201)

# Non-2xx: ALWAYS call BOTH
assert_status_code(response=response, expected_code=404)
assert_error(response=response, expected_error={"type": "API_ERROR", "code": "RESOURCE_NOT_FOUND"})
```

### RESULTS_FORMAT
```bash
python -m pytest tests/ --junit-xml=results/report.xml
```

---

## Adapter: JUnit (Java)

**Stub — complete the 7 slots for your team in < 30 minutes.**

### TEST_RUNNER_CMD
```bash
mvn test -pl module-name -Dtest=TestClassName
./gradlew test --tests "com.example.TestClassName"
```

### TEST_METADATA
```java
@Epic("ITEMS") @Feature("Item CRUD") @Tag("regression")
class CreateItemTest {
    @Story("PROJ-123") @DisplayName("Create item returns 201") @Test
    void createItemReturns201() { ... }
}
```

### PARAMETRIZE
```java
@ParameterizedTest
@CsvSource({"valid-name, 201, ", "'', 400, VALIDATION_ERROR"})
void createItemNameBoundary(String name, int status, String code) { ... }
```

### SETUP_SCOPE
```java
@BeforeAll static void createShared() { /* session scope */ }
@BeforeEach void createFresh() { /* function scope */ }
@AfterEach void deleteFresh() { /* cleanup */ }
```

### SKIP_XFAIL
```java
@Disabled("PROJ-999: known regression") @Test
void getNonexistentItemReturns404() { ... }
```

### ASSERT_CONTRACT
```java
assertThat(response.getStatus()).isEqualTo(404);
assertThat(response.getBody()).contains("RESOURCE_NOT_FOUND");
```

### RESULTS_FORMAT
`target/surefire-reports/*.xml` (Maven) or `build/test-results/` (Gradle).

---

## Adapter: Jest / Vitest (TypeScript / JavaScript)

**Stub — complete the 7 slots for your team in < 30 minutes.**

### TEST_RUNNER_CMD
```bash
npx jest path/to/feature.spec.ts --testNamePattern="create item"
npx vitest run src/__tests__/feature.spec.ts
```

### TEST_METADATA
```typescript
describe("ITEMS / Item CRUD", () => {
  describe("[PROJ-123] Create item", () => {
    test("returns 201 with item body", async () => { ... });
  });
});
```

### PARAMETRIZE
```typescript
it.each([
  ["valid-name", 201, null],
  ["",            400, "VALIDATION_ERROR"],
  [null,          400, "VALIDATION_ERROR"],
])("create item — %s expects %i", async (name, expectedStatus, expectedCode) => {
  const response = await createItem({ name });
  expect(response.status).toBe(expectedStatus);
  if (expectedCode) {
    const body = await response.json();
    expect(body.code).toBe(expectedCode);
  }
});
```

### SETUP_SCOPE
```typescript
let sharedItem: Item;
beforeAll(async () => { sharedItem = await createItem({ name: "shared" }); });
afterAll(async () => { await deleteItem(sharedItem.id); });

let freshItem: Item;
beforeEach(async () => { freshItem = await createItem({ name: "temp" }); });
afterEach(async () => { await deleteItem(freshItem.id).catch(() => {}); });
```

### SKIP_XFAIL
```typescript
test.skip("GET nonexistent returns 404 [PROJ-999]", async () => { ... });
```

### ASSERT_CONTRACT
```typescript
expect(response.status).toBe(404);
expect(response.body).toMatchObject({ type: "API_ERROR", code: "RESOURCE_NOT_FOUND" });
```

### RESULTS_FORMAT
```bash
npx jest --reporters=jest-junit
```

---

## Adapter: Go testing (Go)

**Stub — complete the 7 slots for your team in < 30 minutes.**

### TEST_RUNNER_CMD
```bash
go test ./internal/items/... -run TestCreateItem -v
```

### PARAMETRIZE
```go
func TestCreateItemNameBoundary(t *testing.T) {
    cases := []struct { name string; status int; code string }{
        {"valid", 201, ""}, {"", 400, "VALIDATION_ERROR"},
    }
    for _, tc := range cases {
        tc := tc
        t.Run(tc.name, func(t *testing.T) { t.Parallel() })
    }
}
```

### SETUP_SCOPE
```go
var sharedItem *Item
func TestMain(m *testing.M) {
    sharedItem = createTestItem("shared")
    code := m.Run()
    deleteTestItem(sharedItem.ID)
    os.Exit(code)
}

func createFreshItem(t *testing.T) *Item {
    item := createTestItem("temp")
    t.Cleanup(func() { deleteTestItem(item.ID) })
    return item
}
```

### SKIP_XFAIL
```go
func TestGetNonexistentItemReturns404(t *testing.T) {
    t.Skip("PROJ-999: known regression")
}
```

### ASSERT_CONTRACT
```go
assert.Equal(t, 404, response.StatusCode)
assert.Equal(t, "RESOURCE_NOT_FOUND", errBody["code"])
```

### RESULTS_FORMAT
```bash
gotestsum --junitfile results.xml ./...
```

---

## Adapter: RSpec (Ruby)

**Stub — complete the 7 slots for your team in < 30 minutes.**

### PARAMETRIZE
```ruby
shared_examples "name validation" do |name, status, code|
  it "#{name.inspect} -> #{status}" do
    resp = client.create_item(name: name)
    expect(resp.status).to eq(status)
    expect(resp.body["code"]).to eq(code) if code
  end
end
describe "boundaries" do
  include_examples "name validation", "valid", 201, nil
  include_examples "name validation", "",      400, "VALIDATION_ERROR"
end
```

### RESULTS_FORMAT
```bash
bundle exec rspec --format RspecJunitFormatter --out results/rspec.xml spec/
```

---

## Adapter: Mocha (JavaScript)

**Stub — complete the 7 slots for your team in < 30 minutes.**

### PARAMETRIZE
```javascript
[{ name: "valid", status: 201, code: null }, { name: "", status: 400, code: "VALIDATION_ERROR" }]
  .forEach(({ name, status, code }) => {
    it(`create item — ${JSON.stringify(name)} expects ${status}`, async () => {
      const resp = await client.createItem({ name });
      assert.strictEqual(resp.status, status);
      if (code) assert.strictEqual(resp.body.code, code);
    });
  });
```

### RESULTS_FORMAT
```bash
npx mocha test/ --reporter mocha-junit-reporter
```

---

## Adapter: [Add your framework]

Copy this stub, fill in all 7 slots, and open a PR.

```
### TEST_RUNNER_CMD
### TEST_METADATA
### PARAMETRIZE
### SETUP_SCOPE
### SKIP_XFAIL
### ASSERT_CONTRACT
### RESULTS_FORMAT
```
