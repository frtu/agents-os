package com.github.frtu.ai.agents.os.app.functions

import com.github.frtu.ai.agents.os.app.WeatherInfo
import io.kotest.matchers.nulls.shouldNotBeNull
import io.kotest.matchers.shouldBe
import org.junit.jupiter.api.Test
import org.slf4j.LoggerFactory

class FunctionRegistryTest {
    @Test
    fun generateJsonSchema() {
        //--------------------------------------
        // 1. Init
        //--------------------------------------
        val functionName = "currentWeather"
        val functionDescription = "Get the current weather in a given location"
        val parameterClass = WeatherInfo::class.java

        val functionRegistry = FunctionRegistry()
        //--------------------------------------
        // 2. Execute
        //--------------------------------------
        functionRegistry.addFunction(functionName, functionDescription, parameterClass)
        val result = functionRegistry.registry
        logger.debug("result:$result")

        //--------------------------------------
        // 3. Validate
        //--------------------------------------
        with(result) {
            shouldNotBeNull()
            size shouldBe 1
            with(result[0]) {
                name shouldBe functionName
                description shouldBe functionDescription
                parameters.shouldNotBeNull()
            }
        }
    }

    private val logger = LoggerFactory.getLogger(this::class.java)
}