package com.github.frtu.ai.agents.os.app

import com.aallam.openai.api.chat.ChatChoice
import com.aallam.openai.api.chat.ChatCompletion
import com.aallam.openai.api.chat.ChatMessage
import com.aallam.openai.api.chat.FunctionMode
import com.aallam.openai.api.chat.chatCompletionRequest
import com.aallam.openai.api.http.Timeout
import com.aallam.openai.api.model.ModelId
import com.aallam.openai.client.OpenAI
import com.aallam.openai.client.OpenAIConfig
import com.github.frtu.ai.os.memory.Conversation
import com.github.frtu.ai.os.tool.FunctionRegistry
import com.github.frtu.logs.core.RpcLogger.phase
import com.github.frtu.logs.core.RpcLogger.requestBody
import com.github.frtu.logs.core.RpcLogger.responseBody
import com.github.frtu.logs.core.StructuredLogger
import kotlin.time.Duration.Companion.seconds

class OpenAiChat(
    apiKey: String,
    private val functionRegistry: FunctionRegistry? = null,
    model: String = "gpt-3.5-turbo",
    private val defaultEvaluator: ((List<ChatChoice>) -> ChatChoice)? = null,
) {
    private val modelId = ModelId(model)
    private val openAI = OpenAI(
        OpenAIConfig(
            token = apiKey,
            timeout = Timeout(socket = 60.seconds),
        )
    )

    suspend fun sendMessage(
        conversation: Conversation,
        evaluator: ((List<ChatChoice>) -> ChatChoice)? = null,
    ): ChatChoice =
        evaluator?.let {
            evaluator.invoke(
                send(conversation).choices
            )
        } ?: defaultEvaluator?.invoke(
            send(conversation).choices
        )
        ?: throw IllegalStateException("You need to pass an `evaluator` or `defaultEvaluator` to be able to call chatEval()")

    suspend fun send(conversation: Conversation): ChatCompletion =
        send(conversation.getChatMessages())

    suspend fun send(chatMessages: List<ChatMessage>): ChatCompletion {
        // https://github.com/aallam/openai-kotlin/blob/main/guides/ChatFunctionCall.md
        val request = chatCompletionRequest {
            model = modelId
            messages = chatMessages
            functionRegistry?.let {
                functions = functionRegistry.getRegistry()
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

