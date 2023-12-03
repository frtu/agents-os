package com.github.frtu.ai.os.planning.orchestration

import com.github.frtu.ai.os.planning.orchestration.model.WorkflowObject
import com.github.frtu.ai.os.tool.function
import kotlin.reflect.KFunction2

object WorkflowGenerator {
    fun createWorkflowFunction(action: KFunction2<String, String, String>) = function(
        name = "create_workflow", description = "Create a workflow using graph of states",
        action = action,
        parameterClass = WorkflowObject::class.java,
    )
}
