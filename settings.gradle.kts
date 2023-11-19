rootProject.name = "agents-os"

include(
    "app",
    "utilities",
)

rootProject.children.forEach {
    it.name = it.name.replace("/", "-")
}