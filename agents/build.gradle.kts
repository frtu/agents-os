plugins {
    id("agents.operating.system.kotlin-library-conventions")
}

dependencies {
    // Serialization and Schema
    implementation(Libs.jackson_databind)
    implementation(Libs.jackson_module_kotlin)
    implementation("com.kjetland:mbknor-jackson-jsonschema_2.13:1.0.39")

    // Platform - Coroutine
    implementation(Libs.coroutines_reactor)
}
