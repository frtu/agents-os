package com.github.frtu.ai.agents.os.app

import com.fasterxml.jackson.module.kotlin.jacksonObjectMapper
import com.github.frtu.ai.agents.os.app.functions.FunctionRegistry
import kotlinx.serialization.json.jsonPrimitive

suspend fun main() {
    val apiKey = "sk-xxx"

    val functionRegistry = FunctionRegistry()
    functionRegistry.addFunction(
        name = "currentWeather",
        description = "Get the current weather in a given location",
        parameterClass = WeatherInfo::class.java,
    )
    val openAiService = OpenAiService(apiKey, functionRegistry)

    with(Conversation()) {
        val response = openAiService.chat(user("What's the weather like in Boston?"))
        println(response.choices)

        val message = response.choices.first().message
        message.functionCall?.let { functionCall ->
            this.addResponse(message)

            val availableFunctions = mapOf("currentWeather" to ::currentWeather)
            val functionToCall = availableFunctions[functionCall.name]
                ?: error("Function ${functionCall.name} not found")

            val functionArgs = functionCall.argumentsAsJson()
            val secondResponse = openAiService.chat(
                function(
                    functionName = functionCall.name,
                    content = functionToCall(
                        functionArgs.getValue("location").jsonPrimitive.content,
                        functionArgs["unit"]?.jsonPrimitive?.content ?: "fahrenheit"
                    )
                )
            )
            println(secondResponse.choices.first().message.content)
        } ?: println(message.content)
    }
}

fun currentWeather(location: String, unit: String): String {
    val weatherInfo = WeatherInfo(location, "72", unit, listOf("sunny", "windy"))
    return jacksonObjectMapper().writeValueAsString(weatherInfo)
}