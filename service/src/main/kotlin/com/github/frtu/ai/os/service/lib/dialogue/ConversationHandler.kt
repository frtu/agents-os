package com.github.frtu.ai.os.service.lib.dialogue

import com.slack.api.model.event.Event

interface ConversationHandler<E : Event> {
    /**
     * Listening to a particular event.
     *
     * @param eventId unique ID allowing to deduplicate event
     * @param event received & according payload
     * @param threadManager for advanced case, when you need to pull additional info or push complex case
     * @return Optional - for simple interaction when you only need to respond to answer to that event
     */
    fun invoke(
        // Main interaction handler
        eventId: String,
        // Current event metadata (for idempotency)
        event: E,
        // Current event
        threadManager: ThreadManager,
    ): MessageToUser?
}