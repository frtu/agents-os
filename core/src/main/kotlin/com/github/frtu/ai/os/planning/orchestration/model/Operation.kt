package com.github.frtu.ai.os.planning.orchestration.model

class Operation(
    val name: String,
    val description: String,
    val type: OperationType,
    val inputs: List<String>,
)

enum class OperationType {
    CallMethod,
    Condition,
}