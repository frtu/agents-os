package com.github.frtu.ai.os.planning.orchestration.model

class Action(actionName: ActionName, parameters: List<String>)

enum class ActionName {
    CallFunction,
}