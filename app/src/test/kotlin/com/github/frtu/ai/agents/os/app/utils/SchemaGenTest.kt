package com.github.frtu.ai.agents.os.app.utils

import com.github.frtu.ai.agents.os.app.WeatherInfo
import io.kotest.matchers.nulls.shouldNotBeNull
import org.junit.jupiter.api.Test
import org.slf4j.LoggerFactory

class SchemaGenTest {
    @Test
    fun generateJsonSchema() {
        //--------------------------------------
        // 1. Init
        //--------------------------------------
        val parameterClass = WeatherInfo::class.java

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