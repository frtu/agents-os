package com.github.frtu.ai.os.utils

import io.kotest.matchers.nulls.shouldNotBeNull
import io.serverlessworkflow.api.Workflow
import io.serverlessworkflow.api.functions.FunctionDefinition
import io.serverlessworkflow.api.workflow.Functions
import org.junit.jupiter.api.Test
import org.slf4j.LoggerFactory
import samples.model.WeatherInfo

class SchemaGenTest {
    @Test
    fun generateJsonSchema() {
        //--------------------------------------
        // 1. Init
        //--------------------------------------
        val parameterClass = Workflow::class.java

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