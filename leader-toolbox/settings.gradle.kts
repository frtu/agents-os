rootProject.name = "leader-toolbox"

include(
)

rootProject.children.forEach {
    it.name = it.name.replace("/", "-")
}