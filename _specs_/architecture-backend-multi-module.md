# Backend Architecture Guidelines

This document defines the architectural patterns, principles, and standards for Spring Boot applications. This is application adopts domain-driven design principles. For naming conventions, see the [Naming Conventions Guide](./naming-conventions.md).

## Technology Stack

### Core Technologies
- **Language**: Kotlin (preferred over Java)
- **Framework**: Spring Boot 3.x with Spring WebFlux (reactive programming)
- **Build Tool**: Gradle 8.x with Kotlin DSL (`build.gradle.kts`)
- **Documentation**: Swagger UI with SpringDoc OpenAPI 3

### Dependency Management
- **Version Catalog**: Use Gradle version catalog (`gradle/libs.versions.toml`)
- **Configuration**: YAML format (`application.yml`) with environment-specific profiles
- **Serialization**: Jackson with Kotlin module

### Reactive Programming
This application uses **Kotlin coroutines with Spring WebFlux** in a specific pattern:

- **Simplified Code**: More idiomatic Kotlin code without reactive complexity
- **Suspend Functions**: For async operations in services and HTTP clients
- **Coroutines Integration**: `kotlinx-coroutines-reactor` for WebFlux integration
- **Seamless Integration**: Spring WebFlux automatically converts suspend functions to reactive types
- **Non-blocking I/O**: Throughout the application stack

**Key Benefits:**
- ✅ More readable and maintainable code
- ✅ Familiar imperative-style programming with async benefits
- ✅ Automatic backpressure handling
- ✅ Non-blocking HTTP client operations
- ✅ Simplified error handling with try-catch blocks
- ✅ Better debugging experience

## Architectural Principles

### Domain-Driven Design with Bounded Contexts
**Implementation**: Multi-module structure organized by business domains, not technical layers.

- **Split by domain, not by layer** (DDD style)
- **Bounded Contexts**: Each module represents a bounded context with clear responsibilities
- **Ubiquitous Language**: Consistent terminology
- **Module Independence**: Group related functionality together to reduce coupling but Minimal coupling between domains

### Separation of Concerns
**Pattern**: Wrapper pattern for all external system integrations.

- **Controllers**: Handle HTTP requests/responses, validation, and routing
- **Value Objects**: Request/response models with `VO` suffix for type safety
- **Services**: Implement business logic and domain operations
- **Models**: Define data structures and domain entities
- **Configuration**: Manage application setup and external integrations

## Architectural Patterns

### General Principles
- **Single Responsibility**: Functions should do one thing well. Split complex functions into smaller, focused ones
- **Reactive Programming**: Use Kotlin suspend functions for async operations with Spring WebFlux
- **Immutable Data**: Prefer data classes with val properties
- **Null Safety**: Leverage Kotlin's null safety features
- **Fail Fast**: Validate inputs early and throw meaningful exceptions

### Function Design Standards
- **Pure Functions**: Prefer functions without side effects when possible
- **Predictable Behavior**: Same input should always produce same output
- **Clear Intent**: Function names should clearly indicate what they do
- **Minimal Parameters**: Limit function parameters (max 3-4 for readability)

## Implementation Standards

### Value Object (VO) Pattern
Consistent use of Value Objects for all domain models:

```kotlin
@ValueObject
data class CreateUserVO(
    val username: String? = null,
    val email: String? = null,
) {
    init {
        require(username != null || email != null) { "Either username or email must be provided" }
    }
}
```

**Naming Convention**:
- Request models: `{Action}{Entity}VO` (e.g., `CreateUserVO`)
- Response models: `{Entity}VO` (e.g., `UserDataVO`)
- Domain models: `{Entity}VO` (e.g., `UserVO`)

### Error Handling Standards
Consistent error handling across all task invocation methods:

```kotlin
suspend fun exampleFunction(request: ExampleVO): String {
    try {
        // Validate input
        validateRequest(request)

        // Execute business logic
        return performOperation(request)
    } catch (e: IllegalArgumentException) {
        logger.warn("Invalid request: ${e.message}")
        throw e // Will result in 400 Bad Request via HTTP
    } catch (e: Exception) {
        logger.error("Unexpected error in example function", e)
        throw RuntimeException("Execution failed: ${e.message}")
    }
}
```

### Domain service

**Key Elements**:
- **Named Beans**: Use qualifier constants for multiple HTTP clients
- **External Configuration**: Inject configuration via `@Value` annotations
- **Content Negotiation**: Handle JSON serialization with proper error handling
- **Logging**: Enable HTTP request/response logging for debugging

## API Design Standards

### RESTful Design
- **Resource-Oriented**: URLs represent resources, not actions
- **HTTP Semantics**: Use appropriate HTTP methods (GET, POST, PUT, DELETE)
- **Stateless**: Each request contains all necessary information
- **Consistent Structure**: Follow consistent patterns across all endpoints

### Multi-Modal Function Execution
Tasks can be invoked through multiple channels:

#### 1. HTTP API
```http
POST /api/users
Content-Type: application/json

{
  "username": "username",
  "email": "user@company.com"
}
```

#### 2. AI Tool Calling (via MCP)
```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "create-user",
    "arguments": {
      "username": "username",
      "email": "user@company.com"
    }
  }
}
```

#### Value Object Design Standards
All data models use the Value Object pattern with `VO` suffix:

```kotlin
// Request models with validation
@Schema(description = "Search request for finding programming libraries")
@ValueObject
data class SearchRequest(
  @Schema(description = "Search query", example = "spring boot", required = true)
  val query: String? = null,

  @Schema(description = "Optional filters")
  val filters: SearchFilters? = null,

  @Schema(description = "Maximum results", example = "10", minimum = "1", maximum = "100")
  val limit: Int = 10,

  @Schema(description = "Results to skip", example = "0", minimum = "0")
  val offset: Int = 0
) {
    init {
        query?.let { require(it.isNotBlank()) { "Search query cannot be blank" } }
        require(limit > 0) { "Limit must be positive" }
        require(limit <= 100) { "Limit cannot exceed 100" }
        require(offset >= 0) { "Offset cannot be negative" }
    }
}
```

**Validation Strategy**:
- **Constructor Validation**: Use `init` blocks for essential validation
- **Fail Fast**: Validate at object creation time
- **Clear Error Messages**: Provide descriptive error messages for validation failures and how to resolve it

#### Pagination Standards
- **Consistent Parameters**: Use `limit` and `offset` for pagination
- **Response Metadata**: Include total count and pagination info in responses
- **Reasonable Defaults**: Set sensible default values for page sizes

#### External Model Handling
Separate external API models from domain value objects:

```kotlin
// Domain value object
@ValueObject
data class UserVO(
    val username: String,
    val email: String?,
)

// External API model (in model/external package)
@Serializable
data class GitlabUserResponse(
    val username: String,
    val email: String?,
) {
    fun toDomainModel(): UserVO = UserVO(
        username = username,
        email = email,
    )
}
```

## Configuration Standards

### Application Configuration Structure
The platform uses a multi-layered configuration approach with environment-specific profiles:

```yaml
# application.yml
application:
  name: application-service
  dependencies:                    # External system credentials
    slack:
      app-token: ${SLACK_APP_TOKEN}
      signing-secret: ${SLACK_SIGNING_SECRET}
    openai:
      api-key: ${OPENAI_API_KEY}
      model: ${OPENAI_MODEL:gpt-4o}

spring:
  application:
    name: ${application.name}

management:                       # Actuator configuration
  endpoints:
    web:
      exposure:
        include:
          - prometheus
          - metrics
          - health
          - info
          - loggers
  endpoint:
    health:
      show-details: when_authorized

springdoc:                        # API documentation
  swagger-ui:
    path: /swagger-ui.html
  api-docs:
    path: /v1/api-docs

mcp:                             # MCP server configuration
  port: 38081

logging:
  level:
    org.springframework.transaction: ${LOG_LEVEL_DB_TXN:TRACE}
```

### Environment-Specific Configuration
Use profile-specific configuration files:

```yaml
# application-local.yml
application:
  dependencies:
    slack:
      app-token: dummy

spring:
  flyway:
    enabled: false               # Disable database migrations locally

logging:
  level:
    root: INFO
```

### Auto-Configuration Pattern
Each module provides auto-configuration for Spring Boot integration:

```kotlin
@Configuration
@EnableConfigurationProperties(SlackProperties::class)
@ComponentScan(basePackages = ["com.domain.package"])
class SlackStarterAutoConfiguration(
    private val slackProperties: SlackProperties
) {
    @Bean
    @ConditionalOnMissingBean
    fun slackApp(): App {
        val config = AppConfig.builder()
            .singleTeamBotToken(slackProperties.botToken)
            .signingSecret(slackProperties.signingSecret)
            .build()

        return App(config)
    }
}
```

### Configuration Properties Pattern
Use type-safe configuration properties with validation:

```kotlin
@ConfigurationProperties(prefix = "application.dependencies.slack")
@ConstructorBinding
data class SlackProperties(
    val appToken: String,
    val botToken: String,
    val signingSecret: String,
) {
    init {
        require(appToken.isNotBlank()) { "Slack app token is required" }
        require(botToken.startsWith("xoxb-")) { "Invalid Slack bot token format" }
        require(signingSecret.isNotBlank()) { "Slack signing secret is required" }
    }
}
```

### Version Catalog Configuration
Centralize all dependency versions in `gradle/libs.versions.toml`:

```toml
[versions]
spring-boot = "3.4.5"
kotlin = "2.1.20"

[libraries]
# Spring Boot
spring-boot-starter-webflux = { group = "org.springframework.boot", name = "spring-boot-starter-webflux" }
spring-boot-starter-actuator = { group = "org.springframework.boot", name = "spring-boot-starter-actuator" }

[bundles]
spring-boot-starters = ["spring-boot-starter-webflux", "spring-boot-starter-actuator"]

[plugins]
spring-boot = { id = "org.springframework.boot", version.ref = "spring-boot" }
kotlin-jvm = { id = "org.jetbrains.kotlin.jvm", version.ref = "kotlin" }
kotlin-spring = { id = "org.jetbrains.kotlin.plugin.spring", version.ref = "kotlin" }
```

## Multi-Module Build Configuration

### Root Build Configuration
```kotlin
// build.gradle.kts (root)
plugins {
    jacoco
    java
    alias(libs.plugins.kotlin.jvm.plugin) apply false
    alias(libs.plugins.spring.boot) apply false
}

subprojects {
    apply {
        plugin("maven-publish")
        plugin("org.jetbrains.kotlin.jvm")
        plugin("org.jetbrains.kotlin.plugin.spring")
        plugin("org.jlleitschuh.gradle.ktlint")
        plugin("jacoco")
    }

    java {
        toolchain {
            languageVersion.set(JavaLanguageVersion.of(17))
        }
    }

    dependencies {
        // Common dependencies for all modules
        implementation(platform(libs.spring.boot.dependencies))
        implementation(libs.kotlin.stdlib)
        implementation(libs.kotlin.reflect)

        // Logging
        implementation(libs.logback.classic)

        // Testing
        testImplementation(libs.kotest.assertions.core)
        testImplementation(libs.mockk)
        testImplementation(libs.spring.boot.starter.test)
    }
}
```

### Module-Specific Build Configuration
```kotlin
// xx/service/build.gradle.kts (main application)
plugins {
    alias(libs.plugins.spring.boot)
}

dependencies {
    // Include all feature modules
    implementation(project(":other-module"))

    // Spring Boot starters
    implementation(libs.bundles.spring.boot.starters)
}

jib {
    from {
        image = "openjdk17-jre:0.1"
    }
    container {
        mainClass = "com.domain.package.ApplicationKt"
        jvmFlags = listOf(
            "-Dotel.traces.exporter=none",
            "-Dotel.metrics.exporter=none"
        )
        ports = listOf("8080", "38081")
        creationTime = "USE_CURRENT_TIMESTAMP"
    }
    extraDirectories {
        paths {
            path {
                from = file("arthas")
                into = "/arthas"
            }
        }
    }
}
```

## Testing Standards

### Testing Principles
- **Test Structure**: Use `given/when/then` pattern or descriptive method names with backticks
- **Test Coverage**: Focus on adaptor logic and business rules
- **Test Isolation**: Each test should be independent and repeatable
- **Live vs Mock Testing**: Support both mocked unit tests and live integration tests

### Test Application Pattern
Create Spring Boot test applications for manual testing and debugging:

```kotlin
// src/test/kotlin/.../ModuleTestApplication.kt
@SpringBootApplication
class ModuleTestApplication

fun main(args: Array<String>) {
    runApplication<ModuleTestApplication>(*args)
}
```

### Test Configuration
```yaml
# src/test/resources/application.yml
application:
  dependencies:
    slack:
      app-token: test-app-token
      bot-token: test-bot-token
```

### Coroutines Testing Standards
```kotlin
class DomainServiceTest {

    @Test
    fun `should list bounced emails with pagination`(): Unit = runTest {
        // given
        val request = CreateUserVO(
            TODO
        )

        // when
        val result = domainService.call(request)

        // then
        result shouldNotBe null
        result.size shouldBeLessThanOrEqual 50
    }
}
```

### Testing Dependencies
Include these testing dependencies in modules:

```kotlin
dependencies {
    // Core testing
    testImplementation(libs.kotest.assertions.core)
    testImplementation(libs.mockk)
    testImplementation(libs.junit.jupiter)

    // Spring Boot testing
    testImplementation(libs.spring.boot.starter.test) {
        exclude(group = "org.junit.vintage", module = "junit-vintage-engine")
    }

    // Coroutines testing
    testImplementation(libs.kotlinx.coroutines.test)
}
```

### Test Naming Conventions
- **Test Classes**: `{ClassUnderTest}Test`
- **Test Methods**: Use descriptive names with backticks for readability
- **Live Tests**: Mark with `@Disabled` and clear documentation

```kotlin
class DomainServiceTest {
    @Test
    @Disabled("Enable for manual verification")
    fun `manual testing if necessary`() { }
}
```

### Health Checks and Monitoring
```yaml
# application.yml - health checks
management:
  endpoints:
    web:
      exposure:
        include:
          - prometheus
          - metrics
          - health
          - info
          - loggers
  endpoint:
    health:
      show-details: when_authorized
      probes:
        enabled: true

spring:
  lifecycle:
    timeout-per-shutdown-phase: 30s  # Graceful shutdown
```

### Environment Variables
Required environment variables for deployment:

```bash
# External APIs
SLACK_APP_TOKEN=xapp-xxxxxxxxxxxxx
SLACK_BOT_TOKEN=xoxb-xxxxxxxxxxxxx

# Logging
LOG_LEVEL=INFO
```

## Security Standards

### Input Validation
- Validate all inputs at controller level
- Use Bean Validation annotations (@Valid, @NotNull, etc.)
- Sanitize inputs to prevent injection attacks
- Implement proper authorization checks

### Security Best Practices
- Use HTTPS in production environments
- Implement proper CORS configuration for web clients
- Consider rate limiting for public APIs
- Follow OWASP security guidelines

## Performance Standards

### Reactive Performance with Kotlin Coroutines
- Use non-blocking I/O operations throughout with suspend functions
- Leverage coroutines for efficient concurrent operations
- Use `async` and `await` for concurrent operations when needed
- Avoid blocking operations in suspend functions

### Optimization Guidelines
- Consider caching for frequently accessed data
- Monitor application performance with appropriate metrics via Actuator
- Use connection pooling for external resources
- Implement proper timeout configurations

## Documentation Standards

### API Documentation
- **Always include Swagger UI** for interactive API testing
- Provide comprehensive examples in OpenAPI annotations
- Include multiple request/response scenarios
- Document error cases and edge conditions
- Keep documentation in sync with code changes

### Code Documentation
- Use KDoc for public APIs and complex business logic
- Include usage examples in service and controller documentation
- Explain business rules and complex algorithms
- Document assumptions and constraints

## Deployment Standards

### Configuration Management
- Use Spring profiles for different environments (dev, prod)
- Externalize configuration values using environment variables
- Include health checks via Spring Boot Actuator
- Provide metrics endpoints for monitoring

### Required Dependencies
**Must include these key dependencies in `libs.versions.toml`:**
- `spring-boot-starter-webflux` - WebFlux reactive framework
- `kotlinx-coroutines-reactor` - Coroutines integration with WebFlux
- `jackson-module-kotlin` - JSON serialization for Kotlin
- `springdoc-openapi-starter-webflux-ui` - Swagger UI for WebFlux

## Quality Assurance Checklist

### Code Quality Standards
- [ ] Single responsibility principle followed
- [ ] Functions are small and focused
- [ ] Proper error handling implemented
- [ ] Input validation at boundaries
- [ ] No magic numbers or hardcoded strings

### Reactive Standards
- [ ] Using Kotlin suspend functions instead of Mono/Flux
- [ ] Non-blocking I/O operations throughout
- [ ] Proper coroutines integration
- [ ] No blocking calls in reactive chains

### Documentation Standards
- [ ] Swagger UI accessible and fully functional
- [ ] All endpoints documented with examples
- [ ] Request/response models have comprehensive Schema annotations
- [ ] Error scenarios documented

### Testing Standards
- [ ] Unit tests follow given/when/then pattern
- [ ] Integration tests cover critical paths
- [ ] Test methods have descriptive names
- [ ] Coroutines testing properly implemented

This comprehensive architecture guide ensures consistent, maintainable, and production-ready Spring WebFlux applications that follow modern reactive programming patterns using Kotlin coroutines and industry best practices.

## References

- [Naming Conventions Guide](./naming-conventions.md) - Comprehensive naming standards for all project elements
- [Spring WebFlux Documentation](https://docs.spring.io/spring-framework/docs/current/reference/html/web-reactive.html)
- [Kotlin Coroutines Guide](https://kotlinlang.org/docs/coroutines-guide.html)
- [Domain-Driven Design Principles](https://martinfowler.com/tags/domain%20driven%20design.html)