package com.github.frtu.ai.os.service.event

import com.github.frtu.ai.os.service.lib.dialogue.ConversationHandler
import com.github.frtu.ai.os.service.lib.event.InteractiveEventHandler
import com.slack.api.bolt.handler.BoltEventHandler
import com.slack.api.model.event.AppMentionEvent
import org.springframework.context.annotation.Bean
import org.springframework.context.annotation.Configuration

/**
 * Registry for all Event type class
 * @see <a href="https://oss.sonatype.org/service/local/repositories/releases/archive/com/slack/api/slack-api-model/1.42.0/slack-api-model-1.42.0-javadoc.jar/!/com/slack/api/model/event/Event.html">All Event types</a>
 */
@Configuration
class ConversationToEventHandlerFactory(
    conversationHandlerList: List<ConversationHandler<*>>,
) {
    private val conversationHandlerMap: Map<Class<*>, ConversationHandler<*>> =
        conversationHandlerList.associateBy { it.getEvent().java }

    @Bean
    fun appMentionEventHandler(): Pair<Class<AppMentionEvent>, BoltEventHandler<AppMentionEvent>> =
        InteractiveEventHandler(conversationHandlerMap[AppMentionEvent::class.java] as ConversationHandler<AppMentionEvent>)
            .toPair()
}