plugins {
    id("agents.operating.system.kotlin-library-conventions")
}

dependencies {
    implementation("com.aallam.openai:openai-client")

    // Serialization
    implementation(Libs.jackson_databind)
    implementation(Libs.jackson_module_kotlin)

    // Platform - Coroutine
    implementation(Libs.coroutines_reactor)
}
