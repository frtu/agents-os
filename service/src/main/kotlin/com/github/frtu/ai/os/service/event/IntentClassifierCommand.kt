package com.github.frtu.ai.os.service.event

import com.github.frtu.ai.os.service.agent.IntentClassifierAgent
import com.github.frtu.kotlin.ai.os.llm.agent.UnstructuredBaseAgent
import com.github.frtu.kotlin.spring.slack.dialogue.ConversationHandler
import com.github.frtu.kotlin.spring.slack.dialogue.MessageFromThread
import com.github.frtu.kotlin.spring.slack.dialogue.MessageToThread
import com.github.frtu.kotlin.spring.slack.dialogue.ThreadManager
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
    private val agent: UnstructuredBaseAgent,
) : ConversationHandler<AppMentionEvent> {
    override fun invoke(
        messageFromThread: MessageFromThread<AppMentionEvent>,
        threadManager: ThreadManager,
    ): MessageToThread? {
        runBlocking {
            val request = messageFromThread.message.text
            logger.debug("Request:$request")
            val response = agent.execute(request)
            logger.debug("Response:$response")
            threadManager.respond(MessageToThread(response))
        }
        return null
    }

    override fun getEvent(): KClass<AppMentionEvent> = AppMentionEvent::class

    private val logger = StructuredLogger.create(LoggerFactory.getLogger(this::class.java))
}