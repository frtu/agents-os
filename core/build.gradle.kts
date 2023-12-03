plugins {
    id("agents.operating.system.kotlin-library-conventions")
}

dependencies {
    implementation("io.serverlessworkflow:serverlessworkflow-api:4.0.5.Final")
    implementation("com.kjetland:mbknor-jackson-jsonschema_2.13:1.0.39")
    implementation("com.aallam.openai:openai-client")

    // Serialization
    implementation(Libs.jackson_databind)
    implementation(Libs.jackson_module_kotlin)

    // Platform - Coroutine
    implementation(Libs.coroutines_reactor)
}
