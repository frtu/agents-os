plugins {
    // Core
    kotlin("jvm") version "1.9.25"
    kotlin("plugin.serialization") version "1.9.25"

    // Spring
    kotlin("plugin.spring") version "1.9.25"
    id("org.springframework.boot") version "3.4.1"
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
    implementation(libs.spring.boot.ai.os)
    implementation(libs.spring.boot.slack)
    implementation(libs.spring.boot.tools)
//    implementation(libs.test.tools.sample)
    implementation(libs.test.ai.os.agents)

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
    testImplementation(libs.assertj)

    // Core & test
    implementation("org.jetbrains.kotlin:kotlin-reflect")
    testImplementation("org.junit.jupiter:junit-jupiter:5.8.1")
    testRuntimeOnly("org.junit.platform:junit-platform-launcher")
    testImplementation(libs.kotest.runner)
    testImplementation(libs.kotest.assertions)
}

kotlin {
    compilerOptions {
        freeCompilerArgs.addAll("-Xjsr305=strict")
    }
}

tasks.withType<Test> {
    useJUnitPlatform()
}
