# Backend Architecture Guidelines

This document defines the coding principles, standards, and architectural patterns for Spring Boot applications. For naming conventions, see the [Naming Conventions Guide](./naming-conventions.md).

## Technology Stack

### Core Technologies
- **Language**: Kotlin (preferred over Java)
- **Framework**: Spring Boot 3.x with Spring WebFlux (reactive programming)
- **Build Tool**: Gradle with Kotlin DSL (`build.gradle.kts`)
- **Documentation**: Swagger UI with SpringDoc OpenAPI 3

### Dependency Management
- **Version Catalog**: Use Gradle version catalog (`gradle/libs.versions.toml`)
- **Configuration**: YAML format (`application.yaml`) instead of properties

### Kotlin Coroutines Integration
This application uses **Kotlin coroutines with Spring WebFlux** instead of traditional Mono/Flux reactive types:

- **Modern Approach**: Use `suspend` functions for async operations
- **Seamless Integration**: Spring WebFlux automatically converts suspend functions to reactive types
- **Simplified Code**: More idiomatic Kotlin code without reactive complexity
- **Required Dependencies**: `kotlinx-coroutines-reactor` for Spring WebFlux integration

**Key Benefits:**
- ✅ More readable and maintainable code
- ✅ Familiar imperative-style programming with async benefits
- ✅ Automatic backpressure handling
- ✅ Simplified error handling with try-catch blocks
- ✅ Better debugging experience

## Architectural Principles

### Domain-Driven Design
- **Split by domain, not by layer** (DDD style)
- Each domain should contain its own models, services, and controllers when applicable
- Group related functionality together to reduce coupling

### Separation of Concerns
- **Controllers**: Handle HTTP requests/responses, validation, and routing
- **Services**: Implement business logic and domain operations
- **Models**: Define data structures and domain entities
- **Configuration**: Manage application setup and external integrations

## Backend Coding Practices

### General Principles
- **Single Responsibility**: Functions should do one thing well. Split complex functions into smaller, focused ones
- **Reactive Programming**: Use Kotlin suspend functions for async operations with Spring WebFlux
- **Immutable Data**: Prefer data classes with val properties
- **Null Safety**: Leverage Kotlin's null safety features
- **Fail Fast**: Validate inputs early and throw meaningful exceptions

### Reactive Patterns with Kotlin Coroutines
```kotlin
// Service methods use suspend functions
suspend fun findLibraries(request: SearchRequest): SearchResponse

// Use coroutines for async operations
suspend fun processData(): Result {
    delay(100) // Non-blocking delay
    return computeResult()
}

// Spring WebFlux automatically converts suspend functions to reactive types
```

### Function Design Standards
- **Pure Functions**: Prefer functions without side effects when possible
- **Predictable Behavior**: Same input should always produce same output
- **Clear Intent**: Function names should clearly indicate what they do
- **Minimal Parameters**: Limit function parameters (max 3-4 for readability)

## API Design Standards

### RESTful Design
- **Resource-Oriented**: URLs represent resources, not actions
- **HTTP Semantics**: Use appropriate HTTP methods (GET, POST, PUT, DELETE)
- **Stateless**: Each request contains all necessary information
- **Consistent Structure**: Follow consistent patterns across all endpoints

### Request/Response Design
```kotlin
// Request models with validation
@Schema(description = "Search request for finding programming libraries")
data class SearchRequest(
    @Schema(description = "Search query", example = "spring boot", required = true)
    val query: String,

    @Schema(description = "Optional filters")
    val filters: SearchFilters? = null,

    @Schema(description = "Maximum results", example = "10", minimum = "1", maximum = "100")
    val limit: Int = 10,

    @Schema(description = "Results to skip", example = "0", minimum = "0")
    val offset: Int = 0
)
```

### Pagination Standards
- **Consistent Parameters**: Use `limit` and `offset` for pagination
- **Response Metadata**: Include total count and pagination info in responses
- **Reasonable Defaults**: Set sensible default values for page sizes

## Implementation Standards

### Controller Layer
#### Reactive Controllers with Kotlin Coroutines
- Use `@RestController` with WebFlux
- Use `suspend` functions that return direct types
- Spring WebFlux automatically handles conversion to reactive types under the hood
- Avoid `ResponseEntity` unless specific HTTP control needed

#### Controller Structure
```kotlin
@RestController
@RequestMapping("/v2/libs")
@Tag(name = "Library Search", description = "API for searching programming libraries")
class SearchController(private val searchService: SearchService) {

    @PostMapping("/search")
    @Operation(summary = "Search for programming libraries")
    @ApiResponses(/* detailed responses */)
    suspend fun searchLibraries(@RequestBody request: SearchRequest): SearchResponse {
        return searchService.searchLibraries(request)
    }
}
```

### Service Layer
#### Service Implementation Standards
- Use `@Service` annotation
- Implement business logic with suspend functions for async operations
- Keep services focused on specific domains
- Encapsulate complex business rules

#### Service Pattern
```kotlin
@Service
class SearchService {
    suspend fun searchLibraries(request: SearchRequest): SearchResponse {
        // Validate input
        validateSearchRequest(request)

        // Simulate async operation
        delay(100)

        // Apply business logic
        val filteredResults = applyFilters(mockData, request)

        return SearchResponse(
            results = filteredResults,
            total = calculateTotal(),
            offset = request.offset,
            limit = request.limit
        )
    }

    private fun validateSearchRequest(request: SearchRequest) {
        require(request.query.isNotBlank()) { "Query cannot be empty" }
        require(request.limit > 0) { "Limit must be positive" }
        require(request.offset >= 0) { "Offset cannot be negative" }
    }
}
```

### Data Layer
#### Model Design Standards
- Use Kotlin data classes for immutability
- Include Jackson annotations for JSON serialization
- Add Swagger Schema annotations for API documentation
- Validate data at boundaries (controller input, external API responses)

#### Model Structure Example
```kotlin
@Schema(description = "Individual library information")
data class LibraryResult(
    @Schema(description = "Unique identifier", example = "1")
    @JsonProperty("id")
    val id: String,

    @Schema(description = "Library name", example = "spring-boot-starter-webflux")
    @JsonProperty("name")
    val name: String,

    @field:NotNull
    @field:Min(0)
    @Schema(description = "Download count", example = "15000000")
    @JsonProperty("downloadCount")
    val downloadCount: Long
)
```

## Configuration Standards

### Swagger/OpenAPI Configuration
Always include comprehensive API documentation:

```kotlin
@Configuration
class OpenApiConfig {
    @Bean
    fun customOpenAPI(): OpenAPI {
        return OpenAPI()
            .info(Info()
                .title("Library Search API")
                .description("A reactive REST API for searching programming libraries")
                .version("1.0.0")
                .contact(Contact().name("Demo Team").email("demo@example.com"))
                .license(License().name("Apache 2.0").url("https://www.apache.org/licenses/LICENSE-2.0"))
            )
            .addServersItem(Server().url("http://localhost:8080").description("Development server"))
    }
}
```

### Application Configuration Standards
- Use YAML format for better readability and structure
- Organize configuration by functional areas
- Use environment-specific profiles (dev, prod)
- Externalize sensitive values using environment variables

```yaml
spring:
  application:
    name: demo

server:
  port: 8080

springdoc:
  api-docs:
    path: /v3/api-docs
  swagger-ui:
    path: /swagger-ui.html
    operationsSorter: method
    tagsSorter: alpha

logging:
  level:
    com.example.demo: INFO
    org.springframework.web: DEBUG
```

## Build Configuration Standards

### Version Catalog Best Practices
- Centralize all dependency versions in `gradle/libs.versions.toml`
- Group related dependencies into bundles
- Use semantic versioning
- Keep dependencies up to date

### Build Script Standards
```kotlin
plugins {
    alias(libs.plugins.kotlin.jvm)
    alias(libs.plugins.kotlin.spring)
    alias(libs.plugins.spring.boot)
    alias(libs.plugins.spring.dependency.management)
}

dependencies {
    implementation(libs.bundles.spring.boot.starters)
    implementation(libs.bundles.kotlin.core)
    implementation(libs.springdoc.openapi.starter.webflux.ui)
}
```

## Testing Standards

### Testing Principles
- **Test Structure**: Use `given/when/then` pattern with blank lines between sections
- **Test Coverage**: Focus on business logic and critical paths
- **Test Isolation**: Each test should be independent and repeatable
- **Clear Test Names**: Use descriptive names that explain the scenario

### Unit Testing with Coroutines
```kotlin
class SearchServiceTest {
    @Test
    fun `should return filtered results when searching with filters`() = runTest {
        // given
        val request = SearchRequest(query = "spring", filters = SearchFilters(language = "Kotlin"))

        // when
        val result = searchService.searchLibraries(request)

        // then
        result shouldNotBe null
        result.results.size shouldBe 2
        result.results.all { it.language == "Kotlin" } shouldBe true
    }
}
```

### Integration Testing Standards
- Use `@SpringBootTest` with JUnit 5
- Test the full reactive stack including WebTestClient with coroutines support
- Use `runTest` for coroutine-based test functions
- Include `kotlinx-coroutines-test` dependency for testing suspend functions
- Use embedded databases (H2) for data tests

## Error Handling Standards

### Exception Handling with Coroutines
- Use try-catch blocks in suspend functions for error handling
- Throw appropriate exceptions that Spring WebFlux will convert to HTTP status codes
- Provide meaningful error messages
- Log errors appropriately for debugging

```kotlin
suspend fun searchLibraries(request: SearchRequest): SearchResponse {
    try {
        validateInput(request)
        delay(100) // Async operation
        return processSearch(request)
    } catch (e: IllegalArgumentException) {
        // Spring WebFlux will convert this to 400 Bad Request
        logger.warn("Invalid search request: ${e.message}")
        throw e
    } catch (e: Exception) {
        logger.error("Unexpected error during search", e)
        throw RuntimeException("Search service temporarily unavailable")
    }
}
```

### Error Response Standards
```json
{
  "error": "Bad Request",
  "message": "Query parameter cannot be empty",
  "timestamp": "2024-01-15T10:30:00Z",
  "path": "/v2/libs/search"
}
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