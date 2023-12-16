package com.github.frtu.ai.os.planning.orchestration.model

import com.fasterxml.jackson.annotation.JsonPropertyDescription
import com.kjetland.jackson.jsonSchema.annotations.JsonSchemaDescription

@JsonSchemaDescription("Operation representing a function call to Tools")
class Operation(
    @JsonPropertyDescription("Operation name")
    val name: String,

    @JsonPropertyDescription("Operation description")
    val description: String,

    @JsonPropertyDescription("Type of this operation")
    val type: OperationType,

    @JsonPropertyDescription("Input parameters")
    val inputs: List<String>,
)

@JsonSchemaDescription("Type of operation")
enum class OperationType {
    @JsonPropertyDescription("Calling a function")
    CallFunction,

    @JsonPropertyDescription("A condition branch")
    Condition,
}