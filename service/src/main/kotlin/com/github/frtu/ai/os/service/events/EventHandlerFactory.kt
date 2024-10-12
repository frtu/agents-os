package com.github.frtu.ai.os.service.events

import com.github.frtu.ai.os.service.lib.dialogue.ConversationHandler
import com.github.frtu.ai.os.service.lib.dialogue.ThreadManager
import com.github.frtu.kotlin.spring.slack.event.AbstractEventHandler
import com.github.frtu.logs.core.RpcLogger.kind
import com.github.frtu.logs.core.RpcLogger.requestBody
import com.github.frtu.logs.core.RpcLogger.requestId
import com.github.frtu.logs.core.StructuredLogger
import com.github.frtu.logs.core.StructuredLogger.entry
import com.slack.api.bolt.context.builtin.EventContext
import com.slack.api.bolt.handler.BoltEventHandler
import com.slack.api.model.event.AppMentionEvent
import org.slf4j.LoggerFactory
import org.springframework.context.annotation.Bean
import org.springframework.context.annotation.Configuration

/**
 * Registry for all Event type class
 * @see <a href="https://oss.sonatype.org/service/local/repositories/releases/archive/com/slack/api/slack-api-model/1.42.0/slack-api-model-1.42.0-javadoc.jar/!/com/slack/api/model/event/Event.html">All Event types</a>
 */
@Configuration
class EventHandlerFactory(
    val conversationHandler: ConversationHandler<AppMentionEvent>,
) {
    private val emojiName: String = "eyes"

    @Bean
    fun appMentionEventHandler(): Pair<Class<AppMentionEvent>, BoltEventHandler<AppMentionEvent>> =
        object : AbstractEventHandler<AppMentionEvent>(AppMentionEvent::class.java) {
            override fun handleEvent(appMentionEvent: AppMentionEvent, eventId: String, ctx: EventContext) {
                with(appMentionEvent) {
                    logger.debug(
                        kind(type), requestId(eventId), entry("user", user),
                        entry("channel.id", channel), entry("event.ts", eventTs), requestBody(text)
                    )
                }
                with(
                    ThreadManager(ctx, appMentionEvent.threadTs
                        .takeIf { it != null } ?: appMentionEvent.ts)
                ) {
                    val reactionResponse = this.addReaction(emojiName)

                    val response = conversationHandler.invoke(eventId, appMentionEvent, this)
                    response?.let { this.respond(it.message) }

                    this.removeReaction(emojiName)
                    if (reactionResponse.isOk) {
                        ctx.ack() // Acknowledge the event
                    } else {
                        ctx.ackWithJson("{\"error\":\"Failed to add reaction\"}")
                    }
                }
            }
        }.toPair()

    private val logger = StructuredLogger.create(LoggerFactory.getLogger(this::class.java))
}