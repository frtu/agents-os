# Smart & Lean Build

## How to choose gradle JAR import scope

When importing libraries, the application host will get impacted by lib import dependencies. Here are a few best practices that trie to make the import smoother.

### Logger import

Don't import your logger lib but only rely on `org.slf4j:slf4j-api` for your import as direct dependencies using `implementation`.

For testing, you can import your favorite lib `org.apache.logging.log4j:log4j-slf4j-impl` or `ch.qos.logback:logback-classic` using only `testImplementation`.

### Spring boot auto resolution

Spring boot come with its own Dependency Management plugin that help to fill all the version automatically. It means that any **gradle lib import** can use `implementation` and version will automatically matches the version of the Spring Boot host.

Some lib GroupIds that applies are :
- `org.springframework`
- `org.springframework.boot`
- `com.fasterxml.jackson.*`
- `...`

# Dev conventions
Don't forget to setup code format and call ktlint before commit.

## Proposed project structure & policies
A `module` generate a JAR that you can import using

ex: `implementation(project(":domain-module"))`

A `module` package should be prefixed with a root package that can be split into
- `domain` & `model` : all business logics & modification rules
- `persistence` : all `Repository` & `Entity` classes for data persistence
- `service` : all exposed service for other services to consume
- `config` : all instantiation parameters

In `domain` package, it is recommended to only suffix class with VO, annotate it @ValueObject & stored in `model`.

If you need to manage ID at the application level, use IdGenerator to generate keys using unique set of of parameters (composite key).

All `Entity` classes should only be used inside `persistence` package.

For local in-memory store to retrieve beans at runtime, you can recreate a Registry class that return the list of all beans of a certain type.

### POJO & Serdes (Serialization/Deserialization)
#### Default constructor
In Kotlin, classes constraints ( ex: [non-nullable type](https://kotlinlang.org/docs/null-safety.html#nullable-types-and-non-null-types "https://kotlinlang.org/docs/null-safety.html#nullable-types-and-non-null-types")) need to be satisfied at construction time.

Unfortunately some serdes libraries deserialize in 2 steps :
1. construct
2. set fields
   => which break the first rule.

To resolve this, [noarg kotlin plugin](https://kotlinlang.org/docs/no-arg-plugin.html "https://kotlinlang.org/docs/no-arg-plugin.html") allows to generate empty constructor at compile time to satisfy deserialization mechanism, WHILE keep the business requirement clean when constructing POJO manually.

Import and declare in `build.gradle.kts` :
```kotlin
plugins {
    var kotlin = "1.9.25"

    // Core
    kotlin("jvm") version kotlin
    kotlin("plugin.noarg") version kotlin
}
   
noArg {
    // Apply this magic constructor generation to any class with this annotation
    annotation("com.github.frtu.kotlin.utils.data.ValueObject")
}
```

If you import [lib-utils](https://github.com/frtu/lib-toolbox/tree/master/kotlin/lib-utils) you can directly import :

Annotate any classes with `@ValueObject` :
```kotlin
@ValueObject
data class EventInput(
    val eventId: String?,
)
```

To combine data classes with Jackson & Serialization :
```kotlin
@ValueObject
// Critical: Don't crash on new/unexpected fields
@JsonIgnoreProperties(ignoreUnknown = true)
data class RawInput(
    @JsonProperty("event_id")
    val eventId: String?,
) : Serializable {
    companion object {
        private const val serialVersionUID = 1L
    }
}
```
#### JSON convention

All JSON should be adopting snake case. It can be configured using annotation `@JsonNaming` :
```kotlin
import com.fasterxml.jackson.databind.PropertyNamingStrategies
import com.fasterxml.jackson.databind.annotation.JsonNaming

@JsonNaming(PropertyNamingStrategies.SnakeCaseStrategy::class)
data class ItemVO(
    val name: String,
)
```

#### Spring and All Open

Spring (and other frameworks) allows to "inject code" by extending your class with more functionalities. Contrary to Java, all classes in Kotlin are `final` and need explicit `open` keyword to allow extension.

When starting up, if you encounter your class is `final` your project may miss the [Spring or all open Kotlin plugin](https://kotlinlang.org/docs/all-open-plugin.html#command-line-compiler "https://kotlinlang.org/docs/all-open-plugin.html#command-line-compiler")

#### JSR-380 Bean Validation

Annotate kotlin classes with @annotation [https://www.baeldung.com/kotlin/valid-spring-annotation](https://www.baeldung.com/kotlin/valid-spring-annotation "https://www.baeldung.com/kotlin/valid-spring-annotation")

```kotlin
data class UserVO(
    @field:NotBlank(message = "Name must not be blank")
    val name: String,
    @field:Min(value = 18, message = "Age must be at least 18")
    val age: Int,
    @field:Valid val address: Address
)
```

## Connectivity

### Database & repository classes

#### DB scripts convention
All db/migration approved & merged to `develop` should not change anymore. A new version has to be created using `ALTER TABLE` :

- [Flyway - Versioned migration](https://flywaydb.org/documentation/concepts/migrations#versioned-migrations "https://flywaydb.org/documentation/concepts/migrations#versioned-migrations")


#### Coroutine CRUD

By extending `org.springframework.data.repository.kotlin.CoroutineCrudRepository`, you can implement `Repository`pattern using Spring : [Going Reactive with Spring, Coroutines and Kotlin Flow](https://spring.io/blog/2019/04/12/going-reactive-with-spring-coroutines-and-kotlin-flow#webflux-with-coroutines-api-in-kotlin)

```kotlin
class UserRepository(private val client: DatabaseClient) {
    suspend fun count(): Long =
        client.execute().sql("SELECT COUNT(*) FROM users")
            .asType<Long>().fetch().awaitOne()
    fun findAll(): Flow<User> =
        client.select().from("users").asType<User>().fetch().flow()
    ...
}
```
#### API design & pagination
Should inspire from Client API convention when possible :
- `has_more` to tell if there is ANOTHER page without giving a total item number that can fluctuate.

## Exceptional cases & Logging

### Using Monad
We are using [michaelbull's kotlin-result](https://github.com/michaelbull/kotlin-result#introduction "https://github.com/michaelbull/kotlin-result#introduction") that provide a library to implement monad in kotlin way.
```kotlin
fun checkPrivileges(user: User, command: Command): Result<Command, CommandError> {
    return if (user.rank >= command.mininimumRank) {
        Ok(command)
    } else {
        Err(CommandError.InsufficientRank(command.name))
    }
}
```

The power of it is when you [chain](https://github.com/michaelbull/kotlin-result#chaining "https://github.com/michaelbull/kotlin-result#chaining") multiple function call with monad with `andThen` or `mapError` to transform errors.

### Thrown Exception handling with Error Result Monads

Our services primarily use `Result` Monads for handling errors, instead of relying on thrown exceptions. However, as many stdlib / library / framework functions throw exceptions, it's important to catch these exceptions and map them to `Result` Monads. This reduces the cognitive complexity of our code, as we only need to think about one type of error handling.

A few best practices related to this:

1. `runCatching`, a convenient method for catching Exceptions and mapping to Result, should be used as close as possible to the thrown Exception, so that our core classes don't get cluttered with `runCatching`. For example:

```kotlin
// BAD - runCatching used at call site
fun mapFromGrpcToInternal(grpcObject: GRPCObject): InternalObject {
  // Mapping that might throw an exception
}
// GRPC Implementation Class
class FooServiceRPCImpl {
  fun grpcEndpoint1(grpcObject: GRPCObject) { 
      // RunCatching needs to be used, which increases code complexity
      // and can be easily forgotten, potentially causing issues 
      val internalEntityResult = runCatching { mapFromGrpcToInternal(grpcObject) }
  }
}
// GOOD - runCatching used at point the thrown Exception is introduced to the system
fun mapFromGrpcToInternal(grpcObject: GRPCObject): Result<InternalObject, Error> {
    runCatching {
      // Mapping that might throw an exception    
    }
}
// GRPC Implementation Class
class FooServiceRPCImpl {
    fun grpcEndpoint1(grpcObject: GRPCObject) {
        // RunCatching is already handled
        val internalEntityResult = mapFromGrpcToInternal(grpcObject)
    }
}
```

2. This method of using `runCatching` further encourages us to extract external calls that may throw Exceptions to separate packages that can catch the Exceptions and map them to the appropriate internal Exception type and to the Result Monad.

3. **The Result Monad doesn't always work nicely with framework code that expects Exceptions.** This can cause significant issues if not handled properly. In this case, it's necessary to throw the Exception contained in the Result.

    1. For example, the `@Transactional` Spring Annotation won't abort a transaction if the method returns a Result Monad with an error. So if you convert all Exceptions to `Result` in a Transactional method, a transaction may be committed that shouldn't have been, leading to dirty data.

### Logging
Logging is using slf4j in order to abstract log implementation (current provider is log4j2) :
- Use `error` for technical issues that require **service owner intervention**. It is very recommend to add a stacktrace to spot the line of code that has issues.
- Use `warn` for business validation exception like 4xx http that **capture a call with wrong parameters**. Mostly doesn't require service owner direct intervention, but in case need to troubleshoot with caller.
- Use `info` for marking **important steps or retrieval**. A business call should have **limited but >2 logs** like received input, marking service boundary calls to external resources.
- Use `debug` for verbose steps that you would usually see with debugger. It can be turned off until troubleshooting need to happen.
- Use `trace` for internal logic steps. Only used for **local env** validation during development.

```kotlin
private val logger = LoggerFactory.getLogger(this::class.java)

logger.error("service errors that should be handled by owner", exception)
logger.warn("calling errors happened", exception)
logger.info("important logs")
logger.debug("verbose log used for troubleshooting")
logger.trace("something on how internal works, but not for prod env")
```

#### Logging stage
All logs are important, but at different moments !
- **During development** => Add all the needed logs at `debug` level & only few at `info` level

- **After releasing to prod & feature is stable** => Please bump the level to INFO that you don't use, but we can turn it on anytime on case by case.

#### How to be log efficient
The company want to be log savvy in storage
- DO keep the **important logs** (we need at least **1 per execution with business id** to ack we received this call)

- Be specific on Error logs,
    - we start with `catch(e : Exception)` to catch everything logging the max info (stacktrace)

    - as we get mature on what can happen, we can **specialise the** `catch`to say specifically **how** to resolve the issue & also reduce the need for verbosity


# SDLC - Software lifecycle

## Git conventions
- [GitFlow](https://www.atlassian.com/git/tutorials/comparing-workflows/gitflow-workflow "https://www.atlassian.com/git/tutorials/comparing-workflows/gitflow-workflow")
- [semantic commit messages](https://www.conventionalcommits.org/en/v1.0.0/#summary "https://www.conventionalcommits.org/en/v1.0.0/#summary")

## Testing & Quality

Testing strategy by scope :

1. **Unit test** (automated) : code limited to one single module / JAR (ex: `workflow-management-management-workflow-store`)
2. **Integration test** (automated) : when code across multiple modules or projects
3. **Regression test** (cicd & manual) : when code across multiple modules or projects
4. **End to end test** (cicd & manual) : when change across multiple projects & teams
5. **Performance test** (manual) : needed for latency sensitive requirements OR when load changes
6. **Smoke test** (manual) : when release to prod environments (making sure config & feature are fully deployed)

### Coding principles

- **Test Structure**: Use `given/when/then` pattern with blank lines between sections
- **Test Coverage**: Focus on business logic and critical paths
- **Test Isolation**: Each test should be independent and repeatable
- **Clear Test Names**: Use descriptive names that explain the scenario

### Unit Testing

=> Let's use JUnit 5 ! (don't use docs that reference JUnit 4, please)
- [MockK](https://notwoods.github.io/mockk-guidebook/ "https://notwoods.github.io/mockk-guidebook/") written in Kotlin, cover idiomatic syntax & [coroutine](https://notwoods.github.io/mockk-guidebook/docs/mocking/coroutines/ "https://notwoods.github.io/mockk-guidebook/docs/mocking/coroutines/")
- [kotest](https://kotest.io/docs/assertions/assertions.html "https://kotest.io/docs/assertions/assertions.html")

**Important**: Don't use `kotlin.test.assert*` syntax but use more idiomatic syntax `shouldBe` from kotest. This provides better readability and more descriptive error messages.

```kotlin
// positive test
name shouldBe "sam"
user.name.shouldNotBeNull()

mylist.forExactly(3) {
    it.city shouldBe "Chicago"
}

// Exception tests
val exception = shouldThrow<IllegalAccessException> {
    // code in here that you expect to throw an IllegalAccessException
}
```

Use [kotest-property](https://kotest.io/docs/proptest/property-based-testing.html "https://kotest.io/docs/proptest/property-based-testing.html") [generators](https://kotest.io/docs/proptest/property-test-generators.html "https://kotest.io/docs/proptest/property-test-generators.html")

```kotlin
val statusArb = Arb.enum<WorkflowDefinitionActivationStatus>()
status = statusArb.next()
Exhaustive.enum<WorkflowDefinitionActivationStatus>().checkAll {
    status = it
}
val transactionArb = Arb.bind<Transaction>(
    mapOf(
        UUID::class to Arb.uuid(allowNilValue = false),
        Instant::class to Arb.localDateTime(minYear = 2022, maxYear = 2023).map { it.toInstant(ZoneOffset.UTC) }
    )
)
val arb = Arb.bind(
    listOf(
        Arb.uuid(allowNilValue = false),
        Arb.enum<CurrencyCode>(),
        Arb.enum<CurrencyMappingStatus>(),
        Arb.localDateTime().orNull().map { it.toInstant(ZoneOffset.UTC) },
        Arb.string().orNull(),
        Arb.string().orNull(),
    )
) { params ->
    CurrencyMapping::class.primaryConstructor!!.call(*params.toTypedArray())
}
```
### Regression

Requirements :
- Black box testing against API & contract
- Ability to automatically run validation before each release candidate on `staging` (optionally manually on local)
- POTENTIALLY evaluate if generative AI can help to generate scenario (ex: using [gherkin](https://cucumber.io/docs/gherkin/reference/ "https://cucumber.io/docs/gherkin/reference/"))

## Maintainability
Though code readability and maintainability is NOT always the highest priority (take longer time to create value), we still want to create **lean & coding practice** that can keep our code maintainable.

Please share your ideas to keep the code fit, but only focus on **really useful practices** _(something that make sense & important to us, rather than copy pasting others)_

### Conciseness balance
Kotlin allows us to keep the syntax short for readability, but it’s good to have `1 line of code, one concerns`.

`"${simple.logic.of.conversion.to.string()}" => OK "${complex.logic.that.can.raise.exception()}" => Not recommended val text = complex.logic.that.can.raise.exception() "concatenate.$text.with.other" => OK`

## Releasing

### UT Coverage
- Sonar

## Documentation

### Write technical docs
- If your page is >1 page long, you need at least one diagram to gather / focus your idea
