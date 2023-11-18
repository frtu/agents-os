rootProject.name = "agents-os"

include(
)

rootProject.children.forEach {
    it.name = it.name.replace("/", "-")
}