package com.github.frtu.ai.os.tool

import io.kotest.matchers.nulls.shouldNotBeNull
import io.kotest.matchers.shouldBe
import org.junit.jupiter.api.Test
import org.slf4j.LoggerFactory
import samples.model.WeatherInfo
import samples.service.currentWeather

class FunctionRegistryTest {
    @Test
    fun generateJsonSchema() {
        //--------------------------------------
        // 1. Init
        //--------------------------------------
        val functionName = "currentWeather"
        val functionDescription = "Get the current weather in a given location"
        val parameterClass = WeatherInfo::class.java
        val returnClass = String::class.java

        val functionRegistry = FunctionRegistry()
        //--------------------------------------
        // 2. Execute
        //--------------------------------------
        functionRegistry.registerFunction(functionName, functionDescription, ::currentWeather, parameterClass, returnClass = returnClass)
        val result = functionRegistry.getRegistry()
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