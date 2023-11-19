package com.github.frtu.ai.agents.os.app

import com.fasterxml.jackson.module.kotlin.jacksonObjectMapper
import com.github.frtu.ai.agents.os.app.functions.FunctionRegistry
import kotlin.reflect.KFunction
import kotlin.reflect.KFunction2
import kotlinx.serialization.json.jsonPrimitive

suspend fun main() {
    val apiKey = "sk-xxx"

    val functionRegistry = FunctionRegistry()
    functionRegistry.addFunction(
        name = "currentWeather",
        description = "Get the current weather in a given location",
        parameterClass = WeatherInfo::class.java,
        ::currentWeather,
    )
    val openAiService = OpenAiService(apiKey, functionRegistry)

    with(Conversation()) {
        val response = openAiService.chat(user("What's the weather like in Boston?"))
        println(response.choices)

        val message = response.choices.first().message
        message.functionCall?.let { functionCall ->
            this.addResponse(message)

            val functionArgs = functionCall.argumentsAsJson()

            val functionToCall = functionRegistry.getFunction(functionCall.name)
            val content = functionToCall(
                functionArgs.getValue("location").jsonPrimitive.content,
                functionArgs["unit"]?.jsonPrimitive?.content ?: "fahrenheit"
            )

            val secondResponse = openAiService.chat(
                function(
                    functionName = functionCall.name,
                    content = content
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