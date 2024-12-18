plugins {
    // Core
    kotlin("jvm") version "1.9.25"
    kotlin("plugin.serialization") version "1.9.25"

    // Spring
    kotlin("plugin.spring") version "1.9.25"
    id("org.springframework.boot") version "2.7.15"
    id("io.spring.dependency-management") version "1.1.6"

    // Application
    application
}

//java {
//    toolchain {
//        languageVersion = JavaLanguageVersion.of(17)
//    }
//}

repositories {
    mavenLocal()
    mavenCentral()
}

dependencies {
    // frtu libs
    implementation(libs.serdes.json)
    implementation(libs.spring.boot.tools)
    implementation(libs.spring.boot.ai.os)
    implementation(libs.spring.boot.slack)

    // OpenAI aallam libs
    implementation(libs.aallam.openai.client)
    implementation(libs.ktor.client.apache)
    implementation(libs.ktoken)

    // Commons
    implementation(libs.jsonschema.generate)
    implementation("com.fasterxml.jackson.module:jackson-module-kotlin")

    // Spring
    implementation("org.springframework.boot:spring-boot-starter-web")
    testImplementation("org.springframework.boot:spring-boot-starter-test")

    // Core
    implementation("org.jetbrains.kotlin:kotlin-reflect")
    testImplementation("org.jetbrains.kotlin:kotlin-test-junit5")
    testRuntimeOnly("org.junit.platform:junit-platform-launcher")
}

kotlin {
    compilerOptions {
        freeCompilerArgs.addAll("-Xjsr305=strict")
    }
}

tasks.withType<Test> {
    useJUnitPlatform()
}
