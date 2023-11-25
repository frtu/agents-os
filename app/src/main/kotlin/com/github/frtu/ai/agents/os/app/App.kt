package com.github.frtu.ai.agents.os.app

import com.fasterxml.jackson.module.kotlin.jacksonObjectMapper
import com.github.frtu.ai.agents.os.app.functions.registry
import kotlinx.serialization.json.jsonPrimitive

suspend fun main() {
    val apiKey = "sk-xxx"

    val functionRegistry = registry {
        function(
            name = "get_current_weather", description = "Get the current weather in a given location",
            kFunction2 = ::currentWeather, parameterClass = WeatherInfo::class.java,
        )
    }
    val chat = OpenAiChat(
        apiKey = apiKey,
        model = "gpt-3.5-turbo-0613",
        functionRegistry = functionRegistry,
        defaultEvaluator = { chatChoices -> chatChoices.first() }
    )

    with(Conversation()) {
        val response = chat.sendMessage(user("What's the weather like in Boston?"))
        println(response)

        val message = response.message
        message.functionCall?.let { functionCall ->
            this.addResponse(message)

            val functionArgs = functionCall.argumentsAsJson()

            val functionToCall = functionRegistry.getFunction(functionCall.name)
            val content = functionToCall(
                functionArgs.getValue("location").jsonPrimitive.content,
                functionArgs["unit"]?.jsonPrimitive?.content ?: "fahrenheit"
            )

            val secondResponse = chat.sendMessage(
                function(
                    functionName = functionCall.name,
                    content = content
                )
            )
            println(secondResponse.message.content)
        } ?: println(message.content)
    }
}

fun currentWeather(location: String, unit: String): String {
    val weatherInfo = WeatherInfo(location, "72", unit, listOf("sunny", "windy"))
    return jacksonObjectMapper().writeValueAsString(weatherInfo)
}