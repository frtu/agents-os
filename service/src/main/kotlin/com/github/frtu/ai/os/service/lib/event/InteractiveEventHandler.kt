package com.github.frtu.ai.os.service.lib.event

import com.github.frtu.ai.os.service.lib.dialogue.ConversationHandler
import com.github.frtu.ai.os.service.lib.dialogue.ThreadManager
import com.github.frtu.kotlin.spring.slack.event.AbstractEventHandler
import com.github.frtu.logs.core.RpcLogger
import com.github.frtu.logs.core.RpcLogger.kind
import com.github.frtu.logs.core.RpcLogger.requestBody
import com.github.frtu.logs.core.RpcLogger.requestId
import com.github.frtu.logs.core.StructuredLogger
import com.github.frtu.logs.core.StructuredLogger.entry
import com.slack.api.bolt.context.builtin.EventContext
import com.slack.api.model.event.AppMentionEvent
import org.slf4j.LoggerFactory

/**
 * Specialisation of `AbstractEventHandler` into a simple conversation handler
 */
class InteractiveEventHandler(
    private val conversationHandler: ConversationHandler<AppMentionEvent>,
    private val emojiName: String = "eyes",
) : AbstractEventHandler<AppMentionEvent>(AppMentionEvent::class.java) {
    override fun handleEvent(event: AppMentionEvent, eventId: String, ctx: EventContext) {
        with(event) {
            logger.debug(
                kind(type), requestId(eventId), entry("event.ts", eventTs),
                entry("user", user), entry("channel.id", channel), requestBody(text)
            )
        }
        with(ThreadManager(ctx, event.threadTs.takeIf { it != null } ?: event.ts)) {
            val reactionResponse = this.addReaction(emojiName)

            val response = conversationHandler.invoke(eventId, event, this)
            response?.let { this.respond(it.message) }

            this.removeReaction(emojiName)
            if (reactionResponse.isOk) {
                ctx.ack() // Acknowledge the event
            } else {
                ctx.ackWithJson("{\"error\":\"Failed to add reaction\"}")
            }
        }
    }

    private val logger = StructuredLogger.create(LoggerFactory.getLogger(this::class.java))
}