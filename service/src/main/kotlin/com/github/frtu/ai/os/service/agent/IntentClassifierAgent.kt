package com.github.frtu.ai.os.service.handler

import com.github.frtu.kotlin.llm.os.llm.Chat
import com.github.frtu.kotlin.llm.os.memory.Conversation
import com.github.frtu.kotlin.llm.os.tool.FunctionRegistry
import com.github.frtu.kotlin.spring.slack.dialogue.ConversationHandler
import com.github.frtu.kotlin.spring.slack.dialogue.MessageFromThread
import com.github.frtu.kotlin.spring.slack.dialogue.MessageToThread
import com.github.frtu.kotlin.spring.slack.dialogue.ThreadManager
import com.github.frtu.logs.core.StructuredLogger
import com.slack.api.model.event.AppMentionEvent
import kotlin.reflect.KClass
import kotlinx.coroutines.runBlocking
import org.slf4j.LoggerFactory
import org.springframework.stereotype.Component

@Component
class IntentClassifierAgent(
    // Chat engine
    private val chat: Chat,
    // For execution
    private val functionRegistry: FunctionRegistry? = null,
) : ConversationHandler<AppMentionEvent> {
    companion object {
        const val classifierSystemDirective: String = """
            You’re a LLM that detects intent from user queries. Your task is to classify the user's intent based on their query. Below are the possible intents with brief descriptions. Use these to accurately determine the user's goal, and output only the intent topic.
            - Order Status: Inquiries about the current status of an order, including delivery tracking and estimated arrival times.
            - Product Information: Questions regarding product details, specifications, availability, or compatibility.
            - Payments: Queries related to making payments, payment methods, billing issues, or transaction problems.
            - Returns: Requests or questions about returning a product, including return policies and procedures.
            - Feedback: User comments, reviews, or general feedback about products, services, or experiences.
            - Other: Choose this if the query doesn’t fall into any of the other intents.
        """
    }

    override fun invoke(
        messageFromThread: MessageFromThread<AppMentionEvent>,
        threadManager: ThreadManager
    ): MessageToThread? {
        val commandArgText = messageFromThread.message.text

        runBlocking {
            with(Conversation()) {
                system(classifierSystemDirective)
                val response = chat.sendMessage(user(commandArgText))
                threadManager.respond(MessageToThread(response.message.content!!))
                logger.info(response.toString())
            }
        }
        return null
    }

    override fun getEvent(): KClass<AppMentionEvent> = AppMentionEvent::class

    private val logger = StructuredLogger.create(LoggerFactory.getLogger(this::class.java))
}