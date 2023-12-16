package com.github.frtu.ai.os.planning.orchestration.model

import com.github.frtu.ai.os.utils.SchemaGen
import io.kotest.matchers.nulls.shouldNotBeNull
import org.junit.jupiter.api.Test

import org.slf4j.LoggerFactory

class WorkflowDefinitionTest {
    @Test
    fun generateJsonSchema() {
        //--------------------------------------
        // 1. Init
        //--------------------------------------
        val parameterClass = WorkflowDefinition::class.java

        //--------------------------------------
        // 2. Execute
        //--------------------------------------
        val result = SchemaGen.generateJsonSchema(parameterClass)
        logger.debug("result:$result")

        //--------------------------------------
        // 3. Validate
        //--------------------------------------
        with(result) {
            shouldNotBeNull()
        }
    }

    private val logger = LoggerFactory.getLogger(this::class.java)
}