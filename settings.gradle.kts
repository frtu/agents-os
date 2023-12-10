rootProject.name = "agents-os"

include(
    "core",
    "agents",
    "app",
)

rootProject.children.forEach {
    it.name = it.name.replace("/", "-")
}