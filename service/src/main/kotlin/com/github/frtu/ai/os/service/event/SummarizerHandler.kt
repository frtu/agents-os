package com.github.frtu.ai.os.service.event

import com.github.frtu.ai.os.service.agent.SummarizerAgent
import com.github.frtu.kotlin.ai.os.llm.agent.UnstructuredBaseAgent
import com.github.frtu.kotlin.spring.slack.dialogue.ConversationHandler
import com.github.frtu.kotlin.spring.slack.dialogue.MessageFromThread
import com.github.frtu.kotlin.spring.slack.dialogue.MessageToThread
import com.github.frtu.kotlin.spring.slack.dialogue.ThreadManager
import com.slack.api.model.event.AppMentionEvent
import kotlinx.coroutines.runBlocking
import org.slf4j.LoggerFactory
import org.springframework.beans.factory.annotation.Qualifier
import org.springframework.stereotype.Component

//@Component
class SummarizerHandler(
    @Qualifier(SummarizerAgent.TOOL_NAME)
    private val agent: UnstructuredBaseAgent,
) : ConversationHandler<AppMentionEvent> {
    override fun invoke(messageFromThread: MessageFromThread<AppMentionEvent>, threadManager: ThreadManager): MessageToThread? =
        runBlocking {
            val commandArgText = messageFromThread.message.text

            val messages = threadManager.retrieveAllMessagesNonBot()
            val allMessageFromThread = messages.mapNotNull {
                val result = it?.text?.trim()
                result
            }.joinToString("\n")
            logger.debug("allMessageFromThread:$allMessageFromThread")

            var responseToUser: String = agent.execute(allMessageFromThread)
            return@runBlocking MessageToThread("Here is the summary of the previous ${messages.size} non bot messages. $responseToUser")
        }

    override fun getEvent() = AppMentionEvent::class

    private val logger = LoggerFactory.getLogger(this::class.java)
}