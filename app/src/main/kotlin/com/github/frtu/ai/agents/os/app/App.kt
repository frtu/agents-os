package com.github.frtu.ai.agents.os.app

import com.fasterxml.jackson.module.kotlin.jacksonObjectMapper
import com.github.frtu.ai.agents.travel.ValidationAgent
import com.github.frtu.ai.os.llm.Chat
import com.github.frtu.ai.os.memory.Conversation
import com.github.frtu.ai.os.planning.orchestration.WorkflowGenerator.createWorkflowDefinition
import com.github.frtu.ai.os.tool.agent.AgentCallGenerator.generateSystemPrompt
import com.github.frtu.ai.os.tool.registry
import com.github.frtu.ai.os.utils.FileLoader.readFileFromClasspath
import kotlinx.serialization.json.jsonPrimitive

suspend fun main() {
    val apiKey = "sk-xxx"
    val model = "gpt-3.5-turbo-0613"
    val systemDirective =
        "Don't make assumptions about what values to plug into functions. Ask for clarification if a user request is ambiguous."

    val functionRegistry = registry {
        register(function = createWorkflowDefinition(::currentWeather))
        function(
            name = "get_current_weather", description = "Get the current weather in a given location",
            kFunction2 = ::currentWeather,
            jsonSchema = readFileFromClasspath("./schema/weather-info-schema.json"),
        )
        function(
            name = "get_n_day_weather_forecast", description = "Get an N-day weather forecast",
            kFunction2 = ::currentWeather, parameterClass = WeatherInfoMultiple::class.java,
        )
    }

    val chat: Chat = OpenAiChat(
        apiKey = apiKey,
        model = model,
//        functionRegistry = functionRegistry,
        defaultEvaluator = { chatChoices -> chatChoices.first() }
    )
    val conversation = Conversation(
        generateSystemPrompt(
            ValidationAgent::validate,
            ValidationAgent::class
        )
    ) // OR calling recallConversation()

    with(conversation) {
//        val response = chat.sendMessage(user("What's the weather like in Glasgow, Scotland today?"))
        val response =
            chat.sendMessage(
                user(
                    """
                    I want to do 2 week trip from Berkeley CA to New York City.
                    I want to visit national parks and cities with good food.
                    I want use a rental car and drive for no more than 5 hours on any given day.
                    """.trimIndent()
                )
            )
        println(response)

        // Handle response
        // Sanity check for message structure (contains function call OR message)
        val message = response.message
        message.functionCall?.let { functionCall ->
            // Should check token before append OR summarizing
            this.addResponse(message)

            val functionToCall = functionRegistry.getFunction(functionCall.name)

            // Validate all required parameters are present
            val functionArgs = functionCall.argumentsAsJson()
            val location = functionArgs.getValue("location").jsonPrimitive.content
            val unit = functionArgs["unit"]?.jsonPrimitive?.content ?: "fahrenheit"
//            val numberOfDays = functionArgs.getValue("numberOfDays").jsonPrimitive.content

            val secondResponse = chat.sendMessage(
                function(
                    functionName = functionCall.name,
                    content = functionToCall.action(location, unit)
                )
            )
            println(secondResponse.message.content)
        } ?: println(message.content)
    }
}

fun currentWeather(location: String, unit: String): String {
    val weatherInfo = WeatherInfo(location, unit, "72", listOf("sunny", "windy"))
    return jacksonObjectMapper().writeValueAsString(weatherInfo)
}