package com.github.frtu.ai.agents.os.app

import com.aallam.openai.api.chat.ChatCompletion
import com.aallam.openai.api.chat.ChatMessage
import com.aallam.openai.api.chat.ChatRole
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

    val chatMessages = mutableListOf(
        ChatMessage(
            role = ChatRole.User,
            content = "What's the weather like in Boston?"
        )
    )
    val response: ChatCompletion = openAiService.chatCompletion(chatMessages)
    println(response.choices)

    val message = response.choices.first().message
    message.functionCall?.let { functionCall ->
        val availableFunctions = mapOf("currentWeather" to ::currentWeather)
        val functionToCall = availableFunctions[functionCall.name] ?: error("Function ${functionCall.name} not found")
        val functionArgs = functionCall.argumentsAsJson()
        val functionResponse = functionToCall(
            functionArgs.getValue("location").jsonPrimitive.content,
            functionArgs["unit"]?.jsonPrimitive?.content ?: "fahrenheit"
        )

        chatMessages.add(
            ChatMessage(
                role = message.role,
                content = message.content.orEmpty(),
                functionCall = message.functionCall
            )
        )
        chatMessages.add(
            ChatMessage(
                role = ChatRole.Function,
                name = functionCall.name,
                content = functionResponse
            )
        )

        val secondResponse = openAiService.chatCompletion(chatMessages)
        println(secondResponse.choices.first().message.content)
    } ?: println(message.content)
}

fun currentWeather(location: String, unit: String): String {
    val weatherInfo = WeatherInfo(location, "72", unit, listOf("sunny", "windy"))
    return jacksonObjectMapper().writeValueAsString(weatherInfo)
}