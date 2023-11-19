plugins {
    id("agents.operating.system.kotlin-application-conventions")
}

dependencies {
    implementation("org.apache.commons:commons-text")
    implementation(project(":utilities"))
}

application {
    // Define the main class for the application.
    mainClass.set("agents.operating.system.app.AppKt")
}
