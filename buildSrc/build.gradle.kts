plugins {
    // Support convention plugins written in Kotlin. Convention plugins are build scripts in 'src/main' that automatically become available as plugins in the main build.
    `kotlin-dsl`
    `java-gradle-plugin`
}

repositories {
    mavenLocal()
    mavenCentral()
    // Use the plugin portal to apply community plugins in convention plugins.
    gradlePluginPortal()
}

dependencies {
    compileOnly(kotlin("gradle-plugin"))
    compileOnly(kotlin("gradle-plugin-api"))
    implementation("org.jetbrains.kotlin:kotlin-gradle-plugin:1.9.20")
}

gradlePlugin {
    plugins {
        create("build-support") {
            id = "build-support"
            implementationClass = "BuildSupport"
        }
    }
}
