plugins {
    // Apply the org.jetbrains.kotlin.jvm Plugin to add support for Kotlin.
    id("org.jetbrains.kotlin.jvm")
}

repositories {
    // Use Maven Central for resolving dependencies.
    mavenCentral()
}

dependencies {
    constraints {
        // Define dependency versions as constraints
        implementation("org.apache.commons:commons-text:1.9")
    }

    // Serialization
    implementation(Libs.jackson_databind)
    implementation(Libs.jackson_module_kotlin)

    // Platform - Coroutine
    implementation(Libs.coroutines_reactor)

    // Platform - Log
    implementation(Libs.logger_core)
    implementation(Libs.log_impl)
    testImplementation(Libs.lib_utils)
    testImplementation(Libs.spring_core)

    // Test
    testImplementation(Libs.junit)
    testImplementation(Libs.kotest)
    testImplementation(Libs.kotest_json)
    testImplementation(Libs.kotest_property)
    testImplementation(Libs.awaitility)
    testImplementation(Libs.mock)
    testImplementation(Libs.assertions)
    testImplementation(kotlin("test"))

    // Platform - BOMs
    implementation(platform(Libs.bom_openai))
    implementation(platform(Libs.bom_jackson))
//    implementation(platform(Libs.bom_kotlin_base))
    implementation(platform(Libs.bom_kotlin_libs))
    implementation(platform(Libs.bom_kotest))
    implementation(platform(Libs.bom_logger))
    implementation(platform(kotlin("bom")))
    implementation(kotlin("stdlib-jdk8"))
    implementation(kotlin("reflect"))
}

tasks.named<Test>("test") {
    // Use JUnit Platform for unit tests.
    useJUnitPlatform()
}
