plugins {
    id("agents.operating.system.kotlin-library-conventions")
}

dependencies {
    // Serialization
    implementation(Libs.jackson_databind)
    implementation(Libs.jackson_module_kotlin)

    // Platform - Coroutine
    implementation(Libs.coroutines_reactor)
}
