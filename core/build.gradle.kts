plugins {
    id("agents.operating.system.kotlin-library-conventions")
}

dependencies {
    implementation(project(":agents"))

    implementation("io.serverlessworkflow:serverlessworkflow-api:4.0.5.Final")
    implementation("com.kjetland:mbknor-jackson-jsonschema_2.13:1.0.39")
    implementation("com.aallam.openai:openai-client")
    testImplementation("io.ktor:ktor-client-okhttp")


    // Serialization
    implementation(Libs.jackson_databind)
    implementation(Libs.jackson_module_kotlin)

    // Platform - Coroutine
    implementation(Libs.coroutines_reactor)
}
