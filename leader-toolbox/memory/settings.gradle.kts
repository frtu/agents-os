rootProject.name = "leader-toolbox"

include(
    "memory",
)

rootProject.children.forEach {
    it.name = it.name.replace("/", "-")
}