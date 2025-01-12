package com.github.frtu.ai.os.service.event

import com.github.frtu.kotlin.ai.feature.intent.agent.IntentClassifierAgent
import com.github.frtu.kotlin.ai.feature.intent.model.IntentResult
import com.github.frtu.kotlin.ai.os.llm.agent.StructuredBaseAgent
import com.github.frtu.kotlin.ai.os.llm.agent.UnstructuredBaseAgent
import com.github.frtu.kotlin.spring.slack.dialogue.ConversationHandler
import com.github.frtu.kotlin.spring.slack.dialogue.MessageFromThread
import com.github.frtu.kotlin.spring.slack.dialogue.MessageToThread
import com.github.frtu.kotlin.spring.slack.dialogue.ThreadManager
import com.github.frtu.kotlin.tool.Tool
import com.github.frtu.kotlin.tool.ToolRegistry
import com.github.frtu.logs.core.StructuredLogger
import com.slack.api.model.event.AppMentionEvent
import kotlin.reflect.KClass
import kotlinx.coroutines.runBlocking
import org.slf4j.LoggerFactory
import org.springframework.beans.factory.annotation.Qualifier
import org.springframework.stereotype.Component

@Component
class IntentClassifierCommand(
    @Qualifier(IntentClassifierAgent.TOOL_NAME)
    private val conciergeAgent: StructuredBaseAgent<String, IntentResult>,
    /** For function / tool execution */
    private val toolRegistry: ToolRegistry,
    private val registry: Map<String, UnstructuredBaseAgent>,
) : ConversationHandler<AppMentionEvent> {
    override fun invoke(
        messageFromThread: MessageFromThread<AppMentionEvent>,
        threadManager: ThreadManager,
    ): MessageToThread? {
        runBlocking {
            val request = messageFromThread.message.text
            logger.debug("Request:$request")
            val response = conciergeAgent.execute(request)
            logger.debug("Response:$response")

            val message: String = registry[response.intent]
                ?.let { tool ->
                    threadManager.respond(MessageToThread(message = "Executing intent:${response.intent}"))
                    val response: String = when (tool) {
                        is UnstructuredBaseAgent -> {
                            val answer = tool.answer(request)
                            answer.content!!
                        }

                        else -> {
                            "Running tool:[${response.intent}] reasoning:[${response.reasoning}]"
                        }
                    }
                    response
                }
                ?: "Not able to fulfill intent:[${response.intent}] reasoning:[${response.reasoning}]"

            threadManager.respond(MessageToThread(message = message))
        }
        return null
    }

    override fun getEvent(): KClass<AppMentionEvent> = AppMentionEvent::class

    private val logger = StructuredLogger.create(LoggerFactory.getLogger(this::class.java))
}