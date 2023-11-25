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
        function(
            name = "get_n_day_weather_forecast", description = "Get an N-day weather forecast",
            kFunction2 = ::currentWeather, parameterClass = WeatherInfoMultiple::class.java,
        )
    }
    val chat = OpenAiChat(
        apiKey = apiKey,
        model = "gpt-3.5-turbo-0613",
        functionRegistry = functionRegistry,
        defaultEvaluator = { chatChoices -> chatChoices.first() }
    )

    with(Conversation()) {
        system("Don't make assumptions about what values to plug into functions. Ask for clarification if a user request is ambiguous.")

        chat.sendMessage(user("What's the weather like in Glasgow, Scotland over the next x days?"))
        val response = chat.sendMessage(user("5 days"))
        println(response)

        val message = response.message
        message.functionCall?.let { functionCall ->
            this.addResponse(message)

            val functionToCall = functionRegistry.getFunction(functionCall.name)

            val functionArgs = functionCall.argumentsAsJson()
            val location = functionArgs.getValue("location").jsonPrimitive.content
            val unit = functionArgs["unit"]?.jsonPrimitive?.content ?: "fahrenheit"
            val numberOfDays = functionArgs.getValue("numberOfDays").jsonPrimitive.content

            val secondResponse = chat.sendMessage(
                function(
                    functionName = functionCall.name,
                    content = functionToCall(location, unit)
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