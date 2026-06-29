# JUnit 5 / Java examples

Stub patterns for JUnit 5 REST API test suites.
Adapt imports and helper names to your project's HTTP client library.

---

## PARAMETRIZE (@ParameterizedTest)

```java
@ParameterizedTest
@CsvSource({
    "a,           201, '',              ",
    "a*255,        201, '',              ",
    "a*256,        400, VALIDATION_ERROR",
    "'',           400, VALIDATION_ERROR",
    "'   ',        400, VALIDATION_ERROR",
})
void testCreateItemNameBoundary(String name, int expectedStatus, String expectedCode) {
    Response response = createItem(name);
    assertThat(response.getStatus()).isEqualTo(expectedStatus);
    if (!expectedCode.isEmpty()) {
        assertThat(response.body().path("code")).isEqualTo(expectedCode);
    }
}
```

---

## SETUP_SCOPE (@BeforeAll / @BeforeEach)

```java
// Read-only — shared
@BeforeAll static void setupShared() { sharedItem = createItem("shared"); }
@AfterAll static void teardownShared() { deleteItem(sharedItem.id); }

// Mutating — per-test
@BeforeEach void setupFresh() { item = createItem("fresh"); }
@AfterEach void teardownFresh() { deleteItem(item.id); }
```

---

## ASSERT_CONTRACT

```java
assertThat(response.getStatus()).isEqualTo(409);
assertThat(response.body().path("type")).isEqualTo("API_ERROR");
assertThat(response.body().path("code")).isEqualTo("CONFLICT");
```

---

## SKIP_XFAIL

```java
@Disabled("PROJ-456 — POST /items returns 500 for emoji names (API bug)")
@Test void testCreateItemEmojiNameReturns400() { ... }
```

---

## TEST_METADATA

```java
@Tag("ITEM")
@Tag("create-item")
@DisplayName("POST item — 201 with item body")
@Test void testCreateItemReturns201WithBody() { ... }
```
