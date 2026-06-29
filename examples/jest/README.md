# Jest / TypeScript examples

Stub patterns for Jest/TypeScript REST API test suites.
Adapt imports and helper names to your project's SDK.

---

## PARAMETRIZE (it.each)

```typescript
it.each([
  ["a",            201, null],
  ["a".repeat(255), 201, null],
  ["a".repeat(256), 400, "VALIDATION_ERROR"],
  ["",              400, "VALIDATION_ERROR"],
  ["   ",           400, "VALIDATION_ERROR"],
])("POST item — name boundary: %s", async (name, expectedStatus, expectedCode) => {
  const response = await createItem({ name });
  expect(response.status).toBe(expectedStatus);
  if (expectedCode) {
    const body = await response.json();
    expect(body.code).toBe(expectedCode);
  }
});
```

---

## SETUP_SCOPE

```typescript
// Read-only — shared (beforeAll)
let sharedItem: Item;
beforeAll(async () => { sharedItem = await createItem({ name: "shared" }); });
afterAll(async () => { await deleteItem(sharedItem.id); });

// Mutating — per-test (beforeEach)
let item: Item;
beforeEach(async () => { item = await createItem({ name: "fresh" }); });
afterEach(async () => { await deleteItem(item.id).catch(() => {}); });
```

---

## ASSERT_CONTRACT

```typescript
expect(response.status).toBe(409);
const body = await response.json();
expect(body.type).toBe("API_ERROR");
expect(body.code).toBe("CONFLICT");
```

---

## SKIP_XFAIL

```typescript
it.skip("POST item — emoji name returns 400 (PROJ-456 — known bug)", async () => {
  // ...
});
```

---

## TEST_METADATA

```typescript
// Use describe() grouping for epic/feature
describe("ITEM — Create Item", () => {
  it("POST item — 201 with item body", async () => { ... });
});
```
