package com.github.frtu.ai.os.service.event

import com.github.frtu.ai.os.service.lib.dialogue.ConversationHandler
import com.github.frtu.ai.os.service.lib.dialogue.MessageToUser
import com.github.frtu.ai.os.service.lib.dialogue.ThreadManager
import com.slack.api.model.event.AppMentionEvent
import org.springframework.stereotype.Component

@Component
class Summarizer : ConversationHandler<AppMentionEvent> {
    override fun invoke(eventId: String, event: AppMentionEvent, threadManager: ThreadManager): MessageToUser? {
        val messages = threadManager.retrieveAllMessageNonBot()
        return MessageToUser("I see ${messages.size} previous non bot messages")
    }

    override fun getEvent() = AppMentionEvent::class
}