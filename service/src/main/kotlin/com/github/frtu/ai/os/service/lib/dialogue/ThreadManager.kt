package com.github.frtu.ai.os.service.lib.dialogue

import com.github.frtu.logs.core.RpcLogger.flow
import com.github.frtu.logs.core.RpcLogger.flowId
import com.github.frtu.logs.core.RpcLogger.kind
import com.github.frtu.logs.core.RpcLogger.requestBody
import com.github.frtu.logs.core.RpcLogger.responseBody
import com.github.frtu.logs.core.StructuredLogger
import com.github.frtu.logs.core.StructuredLogger.entry
import com.slack.api.bolt.context.builtin.EventContext
import com.slack.api.methods.request.chat.ChatPostMessageRequest
import com.slack.api.methods.response.chat.ChatPostMessageResponse
import com.slack.api.model.Message
import org.slf4j.LoggerFactory

open class ThreadManager(
    val ctx: EventContext,
    private val threadTs: String,
    private val botId: String = ctx.botUserId,
    private val channelId: String = ctx.channelId,
) {
    private val methodsClient = ctx.client()

    // Add reaction to the message
    fun addReaction(emojiName: String) = methodsClient.reactionsAdd { r ->
        logger.trace("Adding emojiName:$emojiName to channelId:$channelId")
        r.channel(channelId).timestamp(threadTs)
            .name(emojiName)
    }

    fun removeReaction(emojiName: String) = methodsClient.reactionsRemove { r ->
        logger.trace("Removing emojiName:$emojiName to channelId:$channelId")
        r.channel(channelId).timestamp(threadTs)
            .name(emojiName)
    }

    fun retrieveAllMessageNonBot(): List<Message> = retrieveAllMessage { msg ->
        val result = (msg.user != botId && msg.type == "message")
        structuredLogger.trace(
            kind(msg.type), entry("user", msg.user), entry("channel.id", channelId),
            responseBody(if (result) "keep" else "trimmed"), requestBody(msg.text),
        )
        result
    }

    fun retrieveAllMessage(filter: (Message) -> Boolean): List<Message> {
        // Retrieve the conversation thread using conversations.replies
        val repliesResponse = methodsClient.conversationsReplies { r ->
            r.channel(channelId).ts(threadTs)
        } // Pass the thread's root timestamp (message timestamp)
        return repliesResponse.messages.filter(filter)
    }

    fun respond(message: String): ChatPostMessageResponse = methodsClient.chatPostMessage(
        ChatPostMessageRequest.builder()
            .channel(channelId)
            .threadTs(threadTs) // Respond in the same thread
            .text(message)
            .build()
    )

    private val logger = LoggerFactory.getLogger(this::class.java)
    private val structuredLogger = StructuredLogger.create(logger)
}