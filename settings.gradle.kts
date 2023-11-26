rootProject.name = "agents-os"

include(
    "core",
    "app",
)

rootProject.children.forEach {
    it.name = it.name.replace("/", "-")
}