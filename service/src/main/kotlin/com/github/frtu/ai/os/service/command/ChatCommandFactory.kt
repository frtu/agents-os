package com.github.frtu.ai.os.service.command

import com.github.frtu.kotlin.ai.feature.intent.agent.IntentClassifierAgent
import com.github.frtu.kotlin.ai.feature.intent.model.IntentResult
import com.github.frtu.kotlin.ai.os.llm.agent.StructuredBaseAgent
import com.github.frtu.kotlin.spring.slack.command.ExecutorHandler
import com.github.frtu.kotlin.spring.slack.command.LongRunningSlashCommandHandler
import com.slack.api.bolt.context.builtin.SlashCommandContext
import com.slack.api.bolt.handler.builtin.SlashCommandHandler
import com.slack.api.bolt.request.builtin.SlashCommandRequest
import org.slf4j.Logger
import org.springframework.beans.factory.annotation.Qualifier
import org.springframework.context.annotation.Bean
import org.springframework.context.annotation.Configuration

@Configuration
class ChatCommandFactory(
    @Qualifier(IntentClassifierAgent.TOOL_NAME)
    private val conciergeAgent: StructuredBaseAgent<String, IntentResult>,
) {
    /**
     * Ask a private question
     */
    @Bean
    fun ask(): SlashCommandHandler = LongRunningSlashCommandHandler(
        executorHandler = object : ExecutorHandler {
            override suspend fun invoke(req: SlashCommandRequest, ctx: SlashCommandContext, logger: Logger): String? {
                val request = req.payload.text
                logger.debug("Request:$request")
                val response = conciergeAgent.execute(request)
                logger.debug("Response:$response")
                return response.intent
            }
        },
        errorHandler = { 400 },
        defaultStartingMessage = "Processing your request...",
        defaultErrorMessage = "Sorry, an error occurred while processing your request.",
    )
}