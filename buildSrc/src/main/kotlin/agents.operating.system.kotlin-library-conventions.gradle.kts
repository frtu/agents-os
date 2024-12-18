import org.gradle.kotlin.dsl.`java-library`

plugins {
    // Apply the common convention plugin for shared build configuration between library and application projects.
    id("agents.operating.system.kotlin-common-conventions")

    // Apply the java-library plugin for API and implementation separation.
    `java-library`
}
