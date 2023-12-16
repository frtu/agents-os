package com.github.frtu.ai.os.planning.orchestration.model

import com.fasterxml.jackson.annotation.JsonPropertyDescription
import com.kjetland.jackson.jsonSchema.annotations.JsonSchemaDescription
import io.serverlessworkflow.api.interfaces.State
import java.util.UUID
import io.serverlessworkflow.api.Workflow as ServerlessWorkflow

@JsonSchemaDescription("Workflow definition")
data class WorkflowDefinition(
    @JsonPropertyDescription("Workflow name")
    val name: String,

    @JsonPropertyDescription("Workflow description")
    val description: String,

    @JsonPropertyDescription("List of operation that this workflow execute")
    val operationList: List<Operation>,
) {
    fun toServerlessWorkflow(version: String = "0.1.0") = ServerlessWorkflow(
        UUID.fromString(name).toString(),
        name,
        version,
        mutableListOf<State>(),
    ).withDescription(description)
}