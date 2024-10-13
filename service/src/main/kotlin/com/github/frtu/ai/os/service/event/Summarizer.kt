package com.github.frtu.ai.os.service.event

import com.github.frtu.kotlin.llm.os.llm.Chat
import com.github.frtu.kotlin.llm.os.memory.Conversation
import com.github.frtu.kotlin.llm.os.tool.FunctionRegistry
import com.github.frtu.kotlin.spring.slack.dialogue.ConversationHandler
import com.github.frtu.kotlin.spring.slack.dialogue.MessageFromThread
import com.github.frtu.kotlin.spring.slack.dialogue.MessageToThread
import com.github.frtu.kotlin.spring.slack.dialogue.ThreadManager
import com.github.frtu.logs.core.StructuredLogger
import com.slack.api.model.event.AppMentionEvent
import kotlinx.coroutines.runBlocking
import kotlinx.serialization.json.jsonPrimitive
import org.slf4j.LoggerFactory
import org.springframework.stereotype.Component

@Component
class Summarizer(
    // Chat engine
    private val chat: Chat,
    // For execution
    private val functionRegistry: FunctionRegistry? = null,
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

            var responseToUser: String = ""
            with(Conversation()) {
                system("Help to summarize the thread:$allMessageFromThread")
                val response = chat.sendMessage(user(allMessageFromThread))
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
                    responseToUser = secondResponse.message.content!!
                } ?: run {
                    responseToUser = message.content!!
                }
            }
            return@runBlocking MessageToThread("Here is the summary of the previous ${messages.size} non bot messages. $responseToUser")
        }

    override fun getEvent() = AppMentionEvent::class

    private val logger = StructuredLogger.create(LoggerFactory.getLogger(this::class.java))
}