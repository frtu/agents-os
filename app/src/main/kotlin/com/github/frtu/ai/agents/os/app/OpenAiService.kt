package com.github.frtu.ai.agents.os.app

import com.aallam.openai.api.chat.ChatCompletion
import com.aallam.openai.api.chat.ChatMessage
import com.aallam.openai.api.chat.FunctionMode
import com.aallam.openai.api.chat.chatCompletionRequest
import com.aallam.openai.api.http.Timeout
import com.aallam.openai.api.model.ModelId
import com.aallam.openai.client.OpenAI
import com.aallam.openai.client.OpenAIConfig
import com.github.frtu.ai.agents.os.app.functions.FunctionRegistry
import com.github.frtu.logs.core.RpcLogger.phase
import com.github.frtu.logs.core.RpcLogger.requestBody
import com.github.frtu.logs.core.RpcLogger.responseBody
import com.github.frtu.logs.core.StructuredLogger
import kotlin.time.Duration.Companion.seconds

class OpenAiService(
    apiKey: String,
    private val functionRegistry: FunctionRegistry? = null,
    model: String = "gpt-3.5-turbo"
) {
    private val modelId = ModelId(model)
    private val openAI = OpenAI(
        OpenAIConfig(
            token = apiKey,
            timeout = Timeout(socket = 60.seconds),
        )
    )

    suspend fun chatCompletion(chatMessages: List<ChatMessage>): ChatCompletion {
        // https://github.com/aallam/openai-kotlin/blob/main/guides/ChatFunctionCall.md
        val request = chatCompletionRequest {
            model = modelId
            messages = chatMessages
            functionRegistry?.let {
                functions = functionRegistry.getAvailableFunctions()
                functionCall = FunctionMode.Auto
            }
        }
        logger.debug(phase("chatCompletion"), requestBody(request))
        return openAI.chatCompletion(request).also {
            logger.debug(phase("chatCompletion"), responseBody(it))
        }
    }

    private val logger = StructuredLogger.create(this::class.java)
}