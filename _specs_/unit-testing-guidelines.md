# Unit Testing Guidelines

This document provides comprehensive guidelines for writing optimum and readable unit tests using Kotlin with Kotest assertions. These guidelines are based on analysis of existing test patterns in the codebase and industry best practices.

## Table of Contents
1. [Testing Principles](#testing-principles)
2. [Test Structure & Organization](#test-structure--organization)
3. [Test Method Naming](#test-method-naming)
4. [The 3-Phase Test Pattern](#the-3-phase-test-pattern)
5. [Kotest Assertion Best Practices](#kotest-assertion-best-practices)
6. [Using Kotlin `with()` for Readability](#using-kotlin-with-for-readability)
7. [Test Data Management](#test-data-management)
8. [Parameterized Testing](#parameterized-testing)
9. [Exception Testing](#exception-testing)
10. [Coroutine Testing](#coroutine-testing)
11. [Spring Boot Testing](#spring-boot-testing)
12. [TestContainers & Integration Testing](#testcontainers--integration-testing)
13. [Mocking Best Practices](#mocking-best-practices)
14. [Common Anti-Patterns to Avoid](#common-anti-patterns-to-avoid)

## Testing Principles

### Core Principles
- **Single Responsibility**: Each test should verify one specific behavior or scenario
- **Independence**: Tests should not depend on each other or shared state
- **Repeatability**: Tests should produce consistent results regardless of execution order
- **Fast Execution**: Unit tests should run quickly to provide rapid feedback
- **Clear Intent**: Test purpose should be obvious from naming and structure

### Test Coverage Strategy
Focus testing efforts on:
1. **Business Logic**: Core domain rules and calculations
2. **Edge Cases**: Boundary conditions and error scenarios
3. **Public APIs**: External contracts and interfaces
4. **Complex Algorithms**: Non-trivial computational logic

**Don't Over-Test**:
- Simple getters/setters without logic
- Framework code (Spring Boot auto-configuration)
- External library functionality

## Test Structure & Organization

### File Organization
```kotlin
// Test files should mirror production structure
// Production: com.airwallex.platform.shared.core.utils.TextUtil
// Test: com.airwallex.platform.shared.core.utils.TextUtilTest
```

### Test Class Structure
```kotlin
package com.airwallex.platform.shared.example

import io.kotest.matchers.shouldBe
import io.kotest.matchers.shouldNotBe
import io.kotest.matchers.nulls.shouldNotBeNull
import io.mockk.MockKExtension
import org.junit.jupiter.api.Test
import org.junit.jupiter.api.extension.ExtendWith

@ExtendWith(MockKExtension::class)
internal class ExampleServiceTest {

    // Subject under test
    private val exampleService = ExampleService()

    // Test methods grouped by functionality
    @Test
    fun `should calculate total when valid input provided`() {
        // Test implementation
    }

    @Test
    fun `should throw exception when input is null`() {
        // Test implementation
    }

    companion object {
        // Test constants and utilities
        private const val SAMPLE_VALUE = "test-value"
    }
}
```

## Test Method Naming

### Naming Convention
Use descriptive names with backticks following the pattern:
```
should {expected behavior} when {condition}
```

### Examples
```kotlin
class UserServiceTest {

    @Test
    fun `should create user when valid data provided`()

    @Test
    fun `should throw ValidationException when email is invalid`()

    @Test
    fun `should return empty list when no users match criteria`()

    @Test
    fun `should update user status when user exists and is active`()

    @Test
    fun `should ignore duplicate notifications for same event`()
}
```

### Alternative Patterns
For specific scenarios, you can use variations:
```kotlin
@Test
fun `calculate tax returns correct amount for different income brackets`()

@Test
fun `parseJson handles malformed input gracefully`()

@Test
fun `concurrent access to cache maintains data consistency`()
```

## The 3-Phase Test Pattern

### Structure Overview
Every test should follow the **Init → Execution → Validation** pattern with clear visual separation:

```kotlin
@Test
fun `should process payment when valid request provided`() {
    // --------------------------------------
    // 1. Init (Given/Arrange)
    // --------------------------------------
    val paymentRequest = PaymentRequestVO(
        amount = BigDecimal("100.00"),
        currency = "USD",
        customerId = "customer-123"
    )
    val expectedResponse = PaymentResponseVO(
        transactionId = "tx-456",
        status = PaymentStatus.COMPLETED
    )

    // --------------------------------------
    // 2. Execution (When/Act)
    // --------------------------------------
    val result = paymentService.processPayment(paymentRequest)

    // --------------------------------------
    // 3. Validation (Then/Assert)
    // --------------------------------------
    with(result) {
        shouldNotBeNull()
        transactionId shouldNotBe null
        status shouldBe PaymentStatus.COMPLETED
        amount shouldBe paymentRequest.amount
    }
}
```

### Phase Guidelines

#### 1. Init Phase
- Create test data and mock objects
- Set up preconditions
- Keep setup minimal and focused
- Use factory methods for complex objects

#### 2. Execution Phase
- Single method call (ideally)
- Capture the result for validation
- Avoid multiple assertions here

#### 3. Validation Phase
- Verify all expected outcomes
- Use descriptive assertions
- Group related assertions logically

## Kotest Assertion Best Practices

### Basic Assertions
```kotlin
// ✅ Preferred - Clear and readable
result shouldBe expected
result shouldNotBe null
user.isActive shouldBe true

// ❌ Avoid - Less descriptive
assertEquals(expected, result)
assertNotNull(result)
assertTrue(user.isActive)
```

### Null Safety Assertions
```kotlin
// ✅ Preferred - Kotest null-safety
result.shouldNotBeNull()
result.shouldBeNull()

// ✅ Also acceptable for simple cases
result shouldBe null
result shouldNotBe null
```

### Collection Assertions
```kotlin
// ✅ Collection-specific assertions
results.shouldNotBeEmpty()
results shouldHaveSize 3
results shouldContain expectedItem
results shouldContainAll listOf(item1, item2)

// ✅ Inspector functions for all elements
results.shouldForAll { item ->
    item.isValid shouldBe true
    item.timestamp shouldBeGreaterThan startTime
}

// ✅ Specific element assertions
results.shouldForAtLeastOne { it.priority == Priority.HIGH }
results.shouldForExactly(2) { it.status == Status.PENDING }
```

### String Assertions
```kotlin
// ✅ String-specific matchers
message shouldContain "error"
message shouldStartWith "ERROR:"
message shouldEndWith "failed"
message shouldMatch Regex("""\d{4}-\d{2}-\d{2}""")

// ✅ Case sensitivity
message.shouldContainIgnoringCase("ERROR")
```

### Numeric Assertions
```kotlin
// ✅ Numeric comparisons
value shouldBeGreaterThan 0
value shouldBeLessThanOrEqualTo 100
value shouldBeInRange 1..10

// ✅ Floating point comparisons
price.shouldBeWithinTolerance(expectedPrice, 0.01)
```

### Exception Assertions
```kotlin
// ✅ Exception testing with detailed validation
val exception = shouldThrow<ValidationException> {
    userService.createUser(invalidRequest)
}
exception.message shouldContain "Invalid email"
exception.errorCode shouldBe "USER_001"

// ✅ For simple exception checks
shouldThrowExactly<IllegalArgumentException> {
    calculator.divide(10, 0)
}
```

### Type Assertions
```kotlin
// ✅ Type checking with further validation
result.shouldBeInstanceOf<SuccessResponse>().apply {
    data shouldNotBe null
    timestamp shouldBeGreaterThan startTime
}

// ✅ Alternative pattern
result.shouldBeInstanceOf<SuccessResponse>().let { response ->
    response.data shouldNotBe null
    response.timestamp shouldBeGreaterThan startTime
}
```

## Using Kotlin `with()` for Readability

### Basic Usage
```kotlin
@Test
fun `should create complete user profile when all data provided`() {
    // 1. Init
    val request = CreateUserRequestVO(
        username = "john.doe",
        email = "john@example.com",
        firstName = "John",
        lastName = "Doe"
    )

    // 2. Execution
    val result = userService.createUser(request)

    // 3. Validation
    with(result) {
        shouldNotBeNull()
        id shouldNotBe null
        username shouldBe request.username
        email shouldBe request.email
        profile.shouldNotBeNull()
        with(profile) {
            firstName shouldBe request.firstName
            lastName shouldBe request.lastName
            fullName shouldBe "${request.firstName} ${request.lastName}"
        }
        createdAt shouldBeGreaterThan Instant.now().minusSeconds(1)
        isActive shouldBe true
    }
}
```

### Nested Validation
```kotlin
@Test
fun `should return complete order details with items and pricing`() {
    // 1. Init
    val orderId = "order-123"

    // 2. Execution
    val order = orderService.getOrderDetails(orderId)

    // 3. Validation
    with(order) {
        id shouldBe orderId
        status shouldBe OrderStatus.CONFIRMED

        with(customer) {
            id shouldNotBe null
            email shouldContain "@"
        }

        with(items) {
            shouldNotBeEmpty()
            size shouldBe 2

            with(this[0]) {
                productId shouldBe "prod-1"
                quantity shouldBe 2
                unitPrice shouldBe BigDecimal("10.00")
            }

            with(this[1]) {
                productId shouldBe "prod-2"
                quantity shouldBe 1
                unitPrice shouldBe BigDecimal("25.00")
            }
        }

        with(pricing) {
            subtotal shouldBe BigDecimal("45.00")
            tax shouldBe BigDecimal("4.50")
            total shouldBe BigDecimal("49.50")
        }
    }
}
```

### Complex Object Validation
```kotlin
@Test
fun `should process payment notification with complete audit trail`() {
    // 1. Init
    val notification = PaymentNotificationVO(
        transactionId = "tx-789",
        amount = BigDecimal("150.00"),
        status = PaymentStatus.COMPLETED
    )

    // 2. Execution
    val result = notificationProcessor.process(notification)

    // 3. Validation
    with(result) {
        shouldBeInstanceOf<PaymentProcessedEvent>()

        with(payload) {
            transactionId shouldBe notification.transactionId
            amount shouldBe notification.amount
            processedAt shouldBeGreaterThan Instant.now().minusSeconds(5)

            with(auditTrail) {
                shouldNotBeEmpty()
                size shouldBe 3

                shouldForAll { entry ->
                    entry.timestamp shouldNotBe null
                    entry.action shouldNotBe null
                    entry.userId shouldNotBe null
                }

                with(this[0]) {
                    action shouldBe AuditAction.RECEIVED
                }
                with(this[1]) {
                    action shouldBe AuditAction.VALIDATED
                }
                with(this[2]) {
                    action shouldBe AuditAction.PROCESSED
                }
            }
        }
    }
}
```

## Test Data Management

### Factory Methods
```kotlin
class UserServiceTest {

    @Test
    fun `should create user with default settings`() {
        // 1. Init
        val request = createValidUserRequest()

        // 2. Execution
        val result = userService.createUser(request)

        // 3. Validation
        with(result) {
            id shouldNotBe null
            isActive shouldBe true
        }
    }

    private fun createValidUserRequest(
        username: String = "testuser",
        email: String = "test@example.com",
        isActive: Boolean = true
    ) = CreateUserRequestVO(
        username = username,
        email = email,
        isActive = isActive
    )

    private fun createInvalidUserRequest() = CreateUserRequestVO(
        username = "",
        email = "invalid-email",
        isActive = true
    )
}
```

### Test Data Builders
```kotlin
class OrderBuilder {
    private var id: String = "order-${UUID.randomUUID()}"
    private var customerId: String = "customer-123"
    private var items: List<OrderItemVO> = emptyList()
    private var status: OrderStatus = OrderStatus.PENDING

    fun withId(id: String) = apply { this.id = id }
    fun withCustomerId(customerId: String) = apply { this.customerId = customerId }
    fun withItems(items: List<OrderItemVO>) = apply { this.items = items }
    fun withStatus(status: OrderStatus) = apply { this.status = status }

    fun build() = OrderVO(
        id = id,
        customerId = customerId,
        items = items,
        status = status,
        createdAt = Instant.now()
    )
}

// Usage in tests
@Test
fun `should calculate order total correctly`() {
    // 1. Init
    val order = OrderBuilder()
        .withItems(listOf(
            OrderItemVO("item1", BigDecimal("10.00"), 2),
            OrderItemVO("item2", BigDecimal("5.00"), 3)
        ))
        .build()

    // 2. Execution
    val total = orderCalculator.calculateTotal(order)

    // 3. Validation
    total shouldBe BigDecimal("35.00")
}
```

### Resource-Based Test Data
```kotlin
class JsonTestDataLoader {
    companion object {
        fun loadUserData(filename: String): UserVO {
            val resource = this::class.java.getResource("/testdata/$filename")
                ?: throw IllegalArgumentException("Test data file not found: $filename")
            return resource.readText().toJsonObj(UserVO::class.java)
        }
    }
}

@Test
fun `should process complex user data from file`() {
    // 1. Init
    val userData = JsonTestDataLoader.loadUserData("complex-user.json")

    // 2. Execution
    val result = userProcessor.processUser(userData)

    // 3. Validation
    with(result) {
        isValid shouldBe true
        errors.shouldBeEmpty()
    }
}
```

## Parameterized Testing

### Simple Parameterized Tests
```kotlin
@ParameterizedTest
@CsvSource(
    value = [
        "1, 1000000000000L",
        "1.1111, 1000000000000L",
        "1.222233334444, 1000000000000L",
        "true, false",
        "'test value', 'expected'"
    ]
)
fun `should validate different data types correctly`(
    inputValue: String,
    expectedType: String
) {
    // 1. Init
    val request = ValidationRequestVO(value = inputValue, type = expectedType)

    // 2. Execution
    val result = validator.validate(request)

    // 3. Validation
    result.isValid shouldBe true
}
```

### Complex Parameterized Tests with Custom Sources
```kotlin
@ParameterizedTest
@MethodSource("paymentTestCases")
fun `should process payments correctly for different scenarios`(testCase: PaymentTestCase) {
    // 1. Init
    val request = testCase.request

    // 2. Execution
    val result = if (testCase.shouldSucceed) {
        paymentService.processPayment(request)
    } else {
        shouldThrow<PaymentException> {
            paymentService.processPayment(request)
        }
    }

    // 3. Validation
    if (testCase.shouldSucceed) {
        with(result as PaymentResult) {
            status shouldBe testCase.expectedStatus
            amount shouldBe request.amount
        }
    } else {
        (result as PaymentException).errorCode shouldBe testCase.expectedErrorCode
    }
}

companion object {
    @JvmStatic
    fun paymentTestCases() = listOf(
        PaymentTestCase(
            name = "Valid payment",
            request = PaymentRequestVO(BigDecimal("100.00"), "USD"),
            shouldSucceed = true,
            expectedStatus = PaymentStatus.COMPLETED
        ),
        PaymentTestCase(
            name = "Invalid amount",
            request = PaymentRequestVO(BigDecimal("-10.00"), "USD"),
            shouldSucceed = false,
            expectedErrorCode = "INVALID_AMOUNT"
        )
    )
}

data class PaymentTestCase(
    val name: String,
    val request: PaymentRequestVO,
    val shouldSucceed: Boolean,
    val expectedStatus: PaymentStatus? = null,
    val expectedErrorCode: String? = null
)
```

## Exception Testing

### Basic Exception Testing
```kotlin
@Test
fun `should throw ValidationException when email is invalid`() {
    // 1. Init
    val invalidRequest = CreateUserRequestVO(
        username = "testuser",
        email = "invalid-email-format"
    )

    // 2. Execution & Validation
    val exception = shouldThrow<ValidationException> {
        userService.createUser(invalidRequest)
    }

    with(exception) {
        message shouldContain "Invalid email format"
        field shouldBe "email"
        errorCode shouldBe "USER_VALIDATION_001"
    }
}
```

### Testing Exception Chain
```kotlin
@Test
fun `should handle nested exceptions correctly`() {
    // 1. Init
    val request = CreateUserRequestVO(username = "testuser", email = "test@example.com")

    // Mock database failure
    every { userRepository.save(any()) } throws DataAccessException("Database connection failed")

    // 2. Execution & Validation
    val exception = shouldThrow<ServiceException> {
        userService.createUser(request)
    }

    with(exception) {
        message shouldContain "Failed to create user"
        cause.shouldBeInstanceOf<DataAccessException>()
        cause?.message shouldContain "Database connection failed"
    }
}
```

## Coroutine Testing

### Basic Coroutine Tests
```kotlin
@Test
fun `should process async operation successfully`() = runTest {
    // 1. Init
    val request = ProcessRequestVO(data = "test-data")

    // 2. Execution
    val result = asyncService.processAsync(request)

    // 3. Validation
    with(result) {
        shouldNotBeNull()
        status shouldBe ProcessStatus.COMPLETED
        processedData shouldBe "PROCESSED:test-data"
    }
}
```

### Testing Concurrent Operations
```kotlin
@Test
fun `should handle concurrent requests correctly`() = runTest {
    // 1. Init
    val requests = (1..10).map {
        ProcessRequestVO(data = "request-$it")
    }

    // 2. Execution
    val results = requests.map { request ->
        async { asyncService.processAsync(request) }
    }.awaitAll()

    // 3. Validation
    results.shouldNotBeEmpty()
    results shouldHaveSize 10
    results.shouldForAll { result ->
        result.status shouldBe ProcessStatus.COMPLETED
        result.processedData shouldNotBe null
    }
}
```

### Testing Timeouts and Delays
```kotlin
@Test
fun `should timeout for long running operations`() = runTest {
    // 1. Init
    val longRunningRequest = ProcessRequestVO(data = "slow-operation")

    // 2. Execution & Validation
    shouldThrow<TimeoutException> {
        withTimeout(1000) {
            asyncService.processSlowOperation(longRunningRequest)
        }
    }
}
```

## Spring Boot Testing

### Service Layer Testing
```kotlin
@ExtendWith(SpringExtension::class)
@TestInstance(TestInstance.Lifecycle.PER_CLASS)
class UserServiceSpringTest {

    @MockBean
    private lateinit var userRepository: UserRepository

    @MockBean
    private lateinit var emailService: EmailService

    @Autowired
    private lateinit var userService: UserService

    @Test
    fun `should create user and send welcome email`() {
        // 1. Init
        val request = CreateUserRequestVO(
            username = "newuser",
            email = "newuser@example.com"
        )
        val savedUser = UserEntity(
            id = UUID.randomUUID(),
            username = request.username,
            email = request.email
        )

        every { userRepository.save(any()) } returns savedUser
        every { emailService.sendWelcomeEmail(any()) } returns Unit

        // 2. Execution
        val result = userService.createUser(request)

        // 3. Validation
        with(result) {
            id shouldBe savedUser.id
            username shouldBe request.username
            email shouldBe request.email
        }

        verify { userRepository.save(any()) }
        verify { emailService.sendWelcomeEmail(savedUser.email) }
    }
}
```

### Repository Testing with TestContainers
```kotlin
@DataR2dbcTest
@Testcontainers
@TestInstance(TestInstance.Lifecycle.PER_CLASS)
class UserRepositoryTest : R2dbcSpringDynamicPropertySourceFacet, PostgresFixture() {

    @Autowired
    private lateinit var userRepository: UserRepository

    @Test
    fun `should save and retrieve user correctly`() = runBlocking {
        // 1. Init
        val user = UserEntity(
            username = "testuser",
            email = "test@example.com",
            isActive = true
        )

        // 2. Execution
        val savedUser = userRepository.save(user)
        val retrievedUser = userRepository.findByUsername("testuser")

        // 3. Validation
        with(savedUser) {
            id shouldNotBe null
            username shouldBe user.username
            email shouldBe user.email
        }

        retrievedUser shouldNotBe null
        retrievedUser?.username shouldBe user.username
    }
}
```

## TestContainers & Integration Testing

### Base Integration Test Class
```kotlin
abstract class BaseIntegrationTest : R2dbcSpringDynamicPropertySourceFacet, PostgresFixture() {

    @Autowired
    protected lateinit var webTestClient: WebTestClient

    @BeforeEach
    fun setupTestData() = runBlocking {
        // Clean and setup test data
        cleanDatabase()
        insertTestData()
    }

    protected suspend fun cleanDatabase() {
        // Cleanup logic
    }

    protected suspend fun insertTestData() {
        // Setup test data
    }
}
```

### API Integration Tests
```kotlin
@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
@Testcontainers
class UserControllerIntegrationTest : BaseIntegrationTest() {

    @Test
    fun `should create user via API endpoint`() = runBlocking {
        // 1. Init
        val request = CreateUserRequestVO(
            username = "apiuser",
            email = "apiuser@example.com"
        )

        // 2. Execution & Validation
        webTestClient.post()
            .uri("/api/v1/users")
            .contentType(MediaType.APPLICATION_JSON)
            .bodyValue(request)
            .exchange()
            .expectStatus().isCreated
            .expectBody<UserResponseVO>()
            .consumeWith { response ->
                with(response.responseBody!!) {
                    id shouldNotBe null
                    username shouldBe request.username
                    email shouldBe request.email
                    isActive shouldBe true
                    createdAt shouldNotBe null
                }
            }
    }
}
```

## Mocking Best Practices

### MockK Usage
```kotlin
@ExtendWith(MockKExtension::class)
class OrderServiceTest {

    @MockK
    private lateinit var orderRepository: OrderRepository

    @MockK
    private lateinit var paymentService: PaymentService

    @InjectMockKs
    private lateinit var orderService: OrderService

    @Test
    fun `should process order with payment successfully`() {
        // 1. Init
        val order = createTestOrder()
        val payment = createTestPayment()

        every { orderRepository.save(any()) } returns order
        every { paymentService.processPayment(any()) } returns payment

        // 2. Execution
        val result = orderService.processOrder(order)

        // 3. Validation
        with(result) {
            status shouldBe OrderStatus.CONFIRMED
            paymentId shouldBe payment.id
        }

        verify { orderRepository.save(order) }
        verify { paymentService.processPayment(any()) }
    }
}
```

### Argument Capturing
```kotlin
@Test
fun `should capture and validate method arguments`() {
    // 1. Init
    val argumentSlot = slot<CreateOrderRequestVO>()
    val order = createTestOrder()

    every { orderRepository.save(capture(argumentSlot)) } returns order

    // 2. Execution
    orderService.createOrder(createOrderRequest())

    // 3. Validation
    val capturedArgument = argumentSlot.captured
    with(capturedArgument) {
        customerId shouldBe "customer-123"
        items shouldHaveSize 2
        totalAmount shouldBe BigDecimal("150.00")
    }
}
```

## Common Anti-Patterns to Avoid

### ❌ Avoid These Patterns

#### 1. Multiple Assertions Without Context
```kotlin
// ❌ BAD: Unclear what's being tested
@Test
fun testUser() {
    val user = userService.createUser(request)
    assertNotNull(user.id)
    assertEquals("test", user.username)
    assertTrue(user.isActive)
    assertNotNull(user.createdAt)
}

// ✅ GOOD: Clear structure and intent
@Test
fun `should create active user with generated ID and timestamp`() {
    // 1. Init
    val request = CreateUserRequestVO(username = "test")

    // 2. Execution
    val user = userService.createUser(request)

    // 3. Validation
    with(user) {
        id shouldNotBe null
        username shouldBe "test"
        isActive shouldBe true
        createdAt shouldNotBe null
    }
}
```

#### 2. Testing Multiple Scenarios in One Test
```kotlin
// ❌ BAD: Multiple test cases in one method
@Test
fun `test user validation`() {
    // Testing valid user
    val validUser = userService.validateUser(validRequest)
    assertTrue(validUser.isValid)

    // Testing invalid user
    val invalidUser = userService.validateUser(invalidRequest)
    assertFalse(invalidUser.isValid)
}

// ✅ GOOD: Separate tests for each scenario
@Test
fun `should validate user successfully when all data is correct`() {
    // Single scenario test
}

@Test
fun `should reject user validation when email is missing`() {
    // Different scenario test
}
```

#### 3. Unclear Test Data
```kotlin
// ❌ BAD: Magic values without context
@Test
fun `test payment processing`() {
    val result = paymentService.process(100.50, "USD", "123")
    assertEquals("COMPLETED", result.status)
}

// ✅ GOOD: Clear, named test data
@Test
fun `should process payment successfully when valid amount provided`() {
    // 1. Init
    val paymentAmount = BigDecimal("100.50")
    val currency = "USD"
    val customerId = "customer-123"

    // 2. Execution
    val result = paymentService.process(paymentAmount, currency, customerId)

    // 3. Validation
    result.status shouldBe PaymentStatus.COMPLETED
}
```

#### 4. Over-Mocking
```kotlin
// ❌ BAD: Mocking everything, even simple objects
@MockK
private lateinit var bigDecimal: BigDecimal

// ✅ GOOD: Only mock complex dependencies
@MockK
private lateinit var externalPaymentGateway: PaymentGateway
```

#### 5. Brittle Tests with Implementation Details
```kotlin
// ❌ BAD: Testing implementation rather than behavior
@Test
fun `test user creation`() {
    userService.createUser(request)
    verify { userRepository.save(any()) }
    verify { passwordEncoder.encode(any()) }
    verify { auditLogger.log(any()) }
}

// ✅ GOOD: Focus on behavior and outcomes
@Test
fun `should create user with encrypted password and audit trail`() {
    // 1. Init
    val request = CreateUserRequestVO(username = "test", password = "plaintext")

    // 2. Execution
    val result = userService.createUser(request)

    // 3. Validation
    with(result) {
        id shouldNotBe null
        username shouldBe request.username
        // Password should not be stored in plain text
        password shouldNotBe request.password
        password.length shouldBeGreaterThan request.password.length
    }
}
```

## Summary Checklist

When writing tests, ensure you:

- [ ] Use clear, descriptive test method names with backticks
- [ ] Follow the 3-phase test pattern (Init/Execution/Validation)
- [ ] Use Kotest assertions over JUnit assertions
- [ ] Leverage `with()` for complex object validation
- [ ] Create focused tests that verify single behaviors
- [ ] Use appropriate test data management strategies
- [ ] Mock external dependencies appropriately
- [ ] Handle exceptions explicitly when expected
- [ ] Use `runTest` for coroutine testing
- [ ] Include both positive and negative test cases
- [ ] Keep tests independent and repeatable

Following these guidelines will result in a comprehensive, maintainable, and readable test suite that provides confidence in your code's correctness and helps prevent regressions.