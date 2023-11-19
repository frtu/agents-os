package com.github.frtu.ai.agents.os.app

import com.aallam.openai.api.chat.ChatCompletion
import com.aallam.openai.api.chat.ChatMessage
import com.aallam.openai.api.chat.ChatRole
import com.aallam.openai.api.chat.FunctionMode
import com.aallam.openai.api.chat.chatCompletionRequest
import com.aallam.openai.api.http.Timeout
import com.aallam.openai.api.model.ModelId
import com.aallam.openai.client.OpenAI
import com.aallam.openai.client.OpenAIConfig
import com.fasterxml.jackson.module.kotlin.jacksonObjectMapper
import com.github.frtu.ai.agents.os.app.functions.FunctionRegistry
import kotlin.time.Duration.Companion.seconds
import kotlinx.serialization.json.jsonPrimitive

suspend fun main() {
    val apiKey = "sk-xxx"
    val model = ModelId("gpt-3.5-turbo")

    val openAI = OpenAI(
        OpenAIConfig(
            token = apiKey,
            timeout = Timeout(socket = 60.seconds),
        )
    )

    val chatMessages = mutableListOf(
        ChatMessage(
            role = ChatRole.User,
            content = "What's the weather like in Boston?"
        )
    )
    val functionRegistry = FunctionRegistry()
    functionRegistry.addFunction(
        name = "currentWeather",
        description = "Get the current weather in a given location",
        parameterClass = WeatherInfo::class.java,
    )

    // https://github.com/aallam/openai-kotlin/blob/main/guides/ChatFunctionCall.md
    val chatCompletionRequest = chatCompletionRequest {
        this.model = model
        this.messages = chatMessages
        this.functions = functionRegistry.registry
        this.functionCall = FunctionMode.Auto
    }

    val response: ChatCompletion = openAI.chatCompletion(chatCompletionRequest)
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

        val secondRequest = chatCompletionRequest {
            this.model = model
            messages = chatMessages
        }

        val secondResponse = openAI.chatCompletion(secondRequest)
        println(secondResponse.choices.first().message.content)
    } ?: println(message.content)
}

fun currentWeather(location: String, unit: String): String {
    val weatherInfo = WeatherInfo(location, "72", unit, listOf("sunny", "windy"))
    return jacksonObjectMapper().writeValueAsString(weatherInfo)
}