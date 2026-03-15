# Naming Conventions Guide

This document defines the naming conventions for all aspects of Spring Boot applications using Kotlin and Spring WebFlux. Consistent naming improves code readability, maintainability, and team collaboration.

## Package Organization

### Package Structure
```
src/main/kotlin/com/example/demo/
├── config/           # Configuration and setup classes
├── controller/       # REST API endpoints
├── model/           # Data classes, DTOs, and domain models
├── service/         # Business logic and service layer
└── DemoApplication.kt
```

### Package Naming Conventions
- **Root Package**: `com.example.demo` (or company-specific)
- **Domain Packages**: Use lowercase, singular nouns
  - ✅ `com.example.demo.user`
  - ✅ `com.example.demo.library`
  - ❌ `com.example.demo.users`
  - ❌ `com.example.demo.libraries`

### Domain-Driven Structure
- **Split by domain, not by layer** (DDD style)
- Each domain should contain its own models, services, and controllers when applicable
- Example:
  ```
  src/main/kotlin/com/example/demo/
  ├── user/
  │   ├── UserController.kt
  │   ├── UserService.kt
  │   └── UserModels.kt
  ├── library/
  │   ├── LibraryController.kt
  │   ├── LibraryService.kt
  │   └── LibraryModels.kt
  └── shared/
      ├── config/
      └── common/
  ```

### Module Package Structure
**For multi-module applications:**
- **Module packages should be prefixed with a root package that can be split into:**
  - `domain` & `model`: All business logics & modification rules
  - `persistence`: All `Repository` & `Entity` classes for data persistence
  - `service`: All exposed service for other services to consume
  - `config`: All instantiation parameters

**Value Object Storage:**
- In `domain` package, it is recommended to only suffix class with VO, annotate it @ValueObject & stored in `model`
- All `Entity` classes should only be used inside `persistence` package

## Class Naming

### Controller Classes
- **Pattern**: `{Domain}Controller`
- **Examples**:
  - ✅ `SearchController`
  - ✅ `UserController`
  - ✅ `LibraryController`
  - ❌ `SearchApi`
  - ❌ `SearchResource`
  - ❌ `SearchEndpoint`

### Service Classes
- **Pattern**: `{Domain}Service`
- **Examples**:
  - ✅ `SearchService`
  - ✅ `UserService`
  - ✅ `LibraryService`
  - ❌ `SearchManager`
  - ❌ `SearchHelper`
  - ❌ `SearchUtil`

### Configuration Classes
- **Pattern**: `{Purpose}Config`
- **Examples**:
  - ✅ `OpenApiConfig`
  - ✅ `DatabaseConfig`
  - ✅ `SecurityConfig`
  - ❌ `OpenApiConfiguration`
  - ❌ `SwaggerSetup`

### Model Classes

#### Value Object (VO) Pattern
**All domain models should use the Value Object pattern with VO suffix:**
- **Request Models**: `{Action}{Entity}VO` (e.g., `CreateUserVO`)
- **Response Models**: `{Entity}VO` (e.g., `UserDataVO`)
- **Domain Models**: `{Entity}VO` (e.g., `UserVO`)
- **Examples**:
  - ✅ `CreateUserVO`
  - ✅ `SearchRequestVO`
  - ✅ `UserVO`
  - ✅ `LibraryResultVO`
  - ❌ `SearchReq`
  - ❌ `SearchRes`
  - ❌ `LibraryDTO`

### Exception Classes
- **Pattern**: `{Specific}Exception`
- **Examples**:
  - ✅ `LibraryNotFoundException`
  - ✅ `InvalidSearchParameterException`
  - ❌ `LibraryError`
  - ❌ `SearchError`

## Method Naming

### Repository/Service/Controller Methods
Use specific action words that clearly indicate the operation:

#### Query Operations
- **Pattern**: `find{Entity}[By{Criteria}]`
- **Examples**:
  - ✅ `findLibraries()`
  - ✅ `findLibraryById()`
  - ✅ `findLibrariesByCategory()`
  - ❌ `getLibraries()`
  - ❌ `retrieveLibraries()`
  - ❌ `searchLibraries()` (unless it's a search service)

#### Create/Update Operations
- **Pattern**: `save{Entity}`
- **Examples**:
  - ✅ `saveLibrary()`
  - ✅ `saveUser()`
  - ❌ `createLibrary()`
  - ❌ `addLibrary()`
  - ❌ `insertLibrary()`

#### Delete Operations
- **Pattern**: `delete{Entity}[By{Criteria}]`
- **Examples**:
  - ✅ `deleteLibrary()`
  - ✅ `deleteLibraryById()`
  - ❌ `removeLibrary()`
  - ❌ `destroyLibrary()`

#### Search Operations (for search services)
- **Pattern**: `search{Entity}[By{Criteria}]`
- **Examples**:
  - ✅ `searchLibraries()`
  - ✅ `searchLibrariesByQuery()`

### Suspend Function Naming
- Use the same naming conventions as above
- **Examples**:
  - ✅ `suspend fun findLibraries(): List<Library>`
  - ✅ `suspend fun saveLibrary(library: Library): Library`
  - ✅ `suspend fun deleteLibraryById(id: String)`

### Boolean Methods
- **Pattern**: `is{Condition}`, `has{Property}`, `can{Action}`
- **Examples**:
  - ✅ `isValid()`
  - ✅ `hasResults()`
  - ✅ `canSearch()`
  - ❌ `valid()`
  - ❌ `results()`

## Property and Variable Naming

### Class Properties
- **Pattern**: camelCase
- **Examples**:
  - ✅ `downloadCount`
  - ✅ `lastUpdated`
  - ✅ `repositoryUrl`
  - ❌ `download_count`
  - ❌ `LastUpdated`

### Constants
- **Pattern**: UPPER_SNAKE_CASE
- **Examples**:
  - ✅ `DEFAULT_PAGE_SIZE`
  - ✅ `MAX_SEARCH_RESULTS`
  - ✅ `API_VERSION`
  - ❌ `defaultPageSize`
  - ❌ `maxSearchResults`

### Collection Variables
- **Pattern**: Plural nouns
- **Examples**:
  - ✅ `libraries`
  - ✅ `results`
  - ✅ `filters`
  - ❌ `libraryList`
  - ❌ `resultArray`

## JSON Field Naming

### JSON Convention Standard
**All JSON should adopt snake_case for consistency**. Configure using `@JsonNaming` annotation:

```kotlin
import com.fasterxml.jackson.databind.PropertyNamingStrategies
import com.fasterxml.jackson.databind.annotation.JsonNaming

@JsonNaming(PropertyNamingStrategies.SnakeCaseStrategy::class)
data class ItemVO(
    val name: String,
)
```

### Jackson Annotations
Use `@JsonProperty` when field names need to be explicit:
```kotlin
data class LibraryResultVO(
    @JsonProperty("id")
    val id: String,

    @JsonProperty("download_count")
    val downloadCount: Long
)
```

## URL and Endpoint Naming

### URL Patterns
- **Base Pattern**: `/v{version}/{resource}`
- **Versioning**: Use version numbers in URL path for major versions
- **Resources**: Use plural nouns for collections
- **Examples**:
  - ✅ `/v2/libs/search`
  - ✅ `/v1/users`
  - ✅ `/v2/libraries/{id}`
  - ❌ `/api/v1/library`
  - ❌ `/service/search`
  - ❌ `/libs/v2/search`

### HTTP Method Conventions
- **GET**: Retrieve resources
  - ✅ `GET /v2/libs/{id}`
  - ✅ `GET /v2/libs?category=web`
- **POST**: Create resources or complex operations (like search with body)
  - ✅ `POST /v2/libs`
  - ✅ `POST /v2/libs/search`
- **PUT**: Update entire resources
  - ✅ `PUT /v2/libs/{id}`
- **PATCH**: Partial updates
  - ✅ `PATCH /v2/libs/{id}`
- **DELETE**: Remove resources
  - ✅ `DELETE /v2/libs/{id}`

### Query Parameters
- **Pattern**: camelCase
- **Examples**:
  - ✅ `?pageSize=10`
  - ✅ `?sortBy=name`
  - ✅ `?includeDetails=true`
  - ❌ `?page_size=10`
  - ❌ `?sort-by=name`

### Path Parameters
- **Pattern**: camelCase for multi-word parameters, lowercase for single words
- **Examples**:
  - ✅ `/v2/libs/{id}`
  - ✅ `/v2/users/{userId}/libraries`
  - ❌ `/v2/libs/{library_id}`
  - ❌ `/v2/users/{user-id}/libraries`

## File Naming

### Kotlin Files
- **Pattern**: PascalCase matching the main class name
- **Examples**:
  - ✅ `SearchController.kt`
  - ✅ `SearchService.kt`
  - ✅ `SearchModels.kt` (for multiple related models)
  - ❌ `search_controller.kt`
  - ❌ `searchcontroller.kt`

### Configuration Files
- **Pattern**: kebab-case
- **Examples**:
  - ✅ `application.yaml`
  - ✅ `application-dev.yaml`
  - ✅ `application-prod.yaml`
  - ❌ `applicationDev.yaml`
  - ❌ `application_dev.yaml`

### Build Files
- **Pattern**: Standard naming conventions
- **Examples**:
  - ✅ `build.gradle.kts`
  - ✅ `libs.versions.toml`
  - ✅ `gradle.properties`

## Database Naming (if applicable)

### Table Names
- **Pattern**: snake_case, plural
- **Examples**:
  - ✅ `libraries`
  - ✅ `user_preferences`
  - ❌ `Library`
  - ❌ `userPreference`

### Column Names
- **Pattern**: snake_case
- **Examples**:
  - ✅ `library_id`
  - ✅ `download_count`
  - ✅ `created_at`
  - ❌ `libraryId`
  - ❌ `downloadCount`

### Database Migration Scripts Convention
- **DB scripts convention**: All db/migration approved & merged to `develop` should not change anymore
- **Versioning**: Create a new version using `ALTER TABLE` for modifications
- **Pattern**: Follow Flyway versioned migration standards

## API Request/Response Fields
- **Standard Pattern**: snake_case (configured via @JsonNaming)
- **Legacy Pattern**: camelCase (following JavaScript conventions)
- **Examples**:
  - ✅ `download_count` (with @JsonNaming)
  - ✅ `last_updated` (with @JsonNaming)
  - ✅ `repository_url` (with @JsonNaming)
  - ❌ `downloadCount` (without @JsonNaming)
  - ❌ `lastUpdated` (without @JsonNaming)

## Test Naming

### Test Class Names
- **Pattern**: `{ClassUnderTest}Test`
- **Examples**:
  - ✅ `SearchServiceTest`
  - ✅ `SearchControllerTest`
  - ❌ `SearchServiceTests`
  - ❌ `TestSearchService`

### Test Method Names
- **Pattern**: Use descriptive names with backticks for readability
- **Format**: `should {expected behavior} when {condition}` or `{action} {scenario}`
- **Examples**:
  - ✅ `fun \`should return filtered results when searching with filters\`()`
  - ✅ `fun \`should throw exception when query is empty\`()`
  - ✅ `fun \`should return empty list when no matches found\`()`
  - ✅ `fun \`should list bounced emails with pagination\`()`
  - ❌ `fun testSearchWithFilters()`
  - ❌ `fun search_with_filters_test()`

### Test Structure Pattern
- **Pattern**: Use `given/when/then` pattern with blank lines between sections
- **Example Structure**:
  ```kotlin
  @Test
  fun `should return results when valid input provided`() = runTest {
      // given
      val request = CreateUserVO(username = "testuser")

      // when
      val result = userService.createUser(request)

      // then
      result shouldNotBe null
      result.username shouldBe "testuser"
  }
  ```

## Swagger/OpenAPI Naming

### Tag Names
- **Pattern**: Proper Case with spaces
- **Examples**:
  - ✅ `"Library Search"`
  - ✅ `"User Management"`
  - ❌ `"library-search"`
  - ❌ `"LIBRARY_SEARCH"`

### Operation Summaries
- **Pattern**: Verb phrase describing the action
- **Examples**:
  - ✅ `"Search for programming libraries"`
  - ✅ `"Create a new user"`
  - ✅ `"Delete library by ID"`
  - ❌ `"Libraries search"`
  - ❌ `"New user"`

### Schema Names
- **Pattern**: Match the Kotlin class name
- **Examples**:
  - ✅ `SearchRequest`
  - ✅ `LibraryResult`
  - ✅ `SearchFilters`

## Environment and Configuration Naming

### Environment Variables
- **Pattern**: UPPER_SNAKE_CASE
- **Examples**:
  - ✅ `DATABASE_URL`
  - ✅ `API_KEY`
  - ✅ `SERVER_PORT`
  - ❌ `databaseUrl`
  - ❌ `api-key`

### YAML Configuration Properties
- **Pattern**: kebab-case for Spring Boot properties, camelCase for custom properties
- **Examples**:
  - ✅ `server.port`
  - ✅ `spring.application.name`
  - ✅ `springdoc.swagger-ui.path`
  - ✅ `app.maxSearchResults` (custom property)

### Configuration Properties Classes
- **Pattern**: Use `@ConfigurationProperties` with specific prefix patterns
- **Naming Convention**: `{Module}Properties` or `{Service}Properties`
- **Examples**:
  ```kotlin
  @ConfigurationProperties(prefix = "application.dependencies.slack")
  @ConstructorBinding
  data class SlackProperties(
      val appToken: String,
      val botToken: String,
      val signingSecret: String,
  )

  @ConfigurationProperties(prefix = "application.modules.user-module")
  data class UserModuleProperties(
      val enabled: Boolean = true
  )
  ```

## Version Catalog Naming

### Version Names
- **Pattern**: kebab-case
- **Examples**:
  - ✅ `spring-boot`
  - ✅ `springdoc-openapi`
  - ✅ `kotlin`
  - ❌ `springBoot`
  - ❌ `spring_boot`

### Library Names
- **Pattern**: kebab-case, descriptive
- **Examples**:
  - ✅ `spring-boot-starter-webflux`
  - ✅ `jackson-module-kotlin`
  - ✅ `kotlinx-coroutines-reactor`

### Bundle Names
- **Pattern**: kebab-case, descriptive of the group
- **Examples**:
  - ✅ `spring-boot-starters`
  - ✅ `kotlin-core`
  - ✅ `testing`

### Plugin Names
- **Pattern**: kebab-case, following Gradle conventions
- **Examples**:
  - ✅ `kotlin-jvm`
  - ✅ `kotlin-spring`
  - ✅ `spring-boot`

## Summary

### Quick Reference

| Element | Convention | Example |
|---------|------------|---------|
| **Packages** | lowercase, singular | `com.example.demo.library` |
| **Classes** | PascalCase | `SearchController` |
| **Methods** | camelCase with action verbs | `findLibraries()` |
| **Properties** | camelCase | `downloadCount` |
| **Constants** | UPPER_SNAKE_CASE | `MAX_RESULTS` |
| **URLs** | kebab-case, versioned | `/v2/libs/search` |
| **Files** | PascalCase for Kotlin, kebab-case for config | `SearchService.kt`, `application.yaml` |
| **Tests** | Descriptive with backticks | `should return results when valid query` |
| **JSON Fields** | camelCase | `downloadCount` |
| **Environment Variables** | UPPER_SNAKE_CASE | `DATABASE_URL` |

## Git and Repository Conventions

### Git Conventions
- **Workflow**: [GitFlow](https://www.atlassian.com/git/tutorials/comparing-workflows/gitflow-workflow)
- **Commit Messages**: [Semantic commit messages](https://www.conventionalcommits.org/en/v1.0.0/#summary)
- **Examples**:
  - ✅ `feat: add user authentication module`
  - ✅ `fix: resolve null pointer exception in search service`
  - ✅ `docs: update API documentation for user endpoints`

### Repository Pattern
- **Pattern**: Implement Repository pattern using Spring Data with Kotlin coroutines
- **Interface Extension**: Extend `org.springframework.data.repository.kotlin.CoroutineCrudRepository`
- **Naming**: `{Entity}Repository`
- **Examples**:
  - ✅ `UserRepository`
  - ✅ `LibraryRepository`
  - ❌ `UserRepo`
  - ❌ `UserDAO`

### API Design Patterns
- **Pagination Convention**: Inspire from Client API convention when possible
  - Use `has_more` to tell if there is ANOTHER page without giving a total item number that can fluctuate
  - Use `limit` and `offset` for pagination parameters

These naming conventions ensure consistency across the entire application stack, making code more readable and maintainable for development teams.