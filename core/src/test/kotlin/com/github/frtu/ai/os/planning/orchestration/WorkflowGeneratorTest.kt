package com.github.frtu.ai.os.planning.orchestration

import com.github.frtu.ai.os.utils.SchemaGen
import io.serverlessworkflow.api.Workflow
import org.junit.jupiter.api.Test

class WorkflowGeneratorTest {

    @Test
    fun createWorkflowFunction() {
    }
}

fun main() {
    val parameterClass = Workflow::class.java
    val result = SchemaGen.generateJsonSchema(parameterClass)
    println(result)
}