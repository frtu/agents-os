package com.github.frtu.ai.os.planning.orchestration.model

import io.serverlessworkflow.api.interfaces.State
import java.util.UUID
import io.serverlessworkflow.api.Workflow as ServerlessWorkflow

data class WorkflowObject(
    val name: String,
    val description: String,
    val operationList: List<Operation>,
) {
    fun toServerlessWorkflow(version: String = "0.1.0") = ServerlessWorkflow(
        UUID.fromString(name).toString(),
        name,
        version,
        mutableListOf<State>(),
    ).withDescription(description)
}