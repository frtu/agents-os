package com.github.frtu.ai.os.service.command

import com.github.frtu.kotlin.llm.os.llm.Chat
import com.github.frtu.kotlin.llm.os.memory.Conversation
import com.github.frtu.kotlin.llm.os.tool.FunctionRegistry
import com.github.frtu.kotlin.spring.slack.command.ExecutorHandler
import com.github.frtu.kotlin.spring.slack.command.LongRunningSlashCommandHandler
import com.slack.api.bolt.context.builtin.SlashCommandContext
import com.slack.api.bolt.handler.builtin.SlashCommandHandler
import com.slack.api.bolt.request.builtin.SlashCommandRequest
import kotlinx.serialization.json.jsonPrimitive
import org.slf4j.Logger
import org.springframework.context.annotation.Bean
import org.springframework.context.annotation.Configuration

@Configuration
class ChatCommandFactory {
    @Bean
    fun ask(
        // Chat engine
        chat: Chat,
        // For execution
        functionRegistry: FunctionRegistry? = null,
    ): SlashCommandHandler = LongRunningSlashCommandHandler(
        executorHandler = object : ExecutorHandler {
            override suspend fun invoke(req: SlashCommandRequest, ctx: SlashCommandContext, logger: Logger): String? {
                val commandArgText = req.payload.text

                with(Conversation()) {
                    system("Don't make assumptions about what values to plug into functions. Ask for clarification if a user request is ambiguous.")
                    val response = chat.sendMessage(user(commandArgText))
                    logger.info(response.toString())

                    val message = response.message
                    message.functionCall?.let { functionCall ->
                        this.addResponse(message)

                        val functionToCall = functionRegistry!!.getFunction(functionCall.name).action

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
                        return secondResponse.message.content
                    } ?: run {
                        return message.content
                    }
                }
            }
        },
        errorHandler = { 400 },
        defaultStartingMessage = "Processing your request...",
        defaultErrorMessage = "Sorry, an error occurred while processing your request.",
    )
}