plugins {
    id("agents.operating.system.kotlin-application-conventions")
}

dependencies {
    implementation("com.aallam.openai:openai-client")
    implementation("io.ktor:ktor-client-okhttp")

    implementation(project(":utilities"))
}

application {
    // Define the main class for the application.
    mainClass.set("agents.os.app.AppKt")
}
