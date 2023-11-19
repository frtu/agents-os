plugins {
    id("agents.operating.system.kotlin-application-conventions")
}

dependencies {
    // import Kotlin API client BOM
    implementation(platform("com.aallam.openai:openai-client-bom:3.5.1"))
    implementation("com.aallam.openai:openai-client")
    implementation("io.ktor:ktor-client-okhttp")

    implementation(project(":utilities"))
}

application {
    // Define the main class for the application.
    mainClass.set("agents.os.app.AppKt")
}
