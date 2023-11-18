package com.github.frtu.ai.os.builder

import com.github.frtu.ai.os.model.Conversation
import com.github.frtu.ai.os.model.systemMessage
import com.github.frtu.ai.os.model.userMessage

class ConversationBuilder(
    name: String? = null,
) {
    private val conversation = Conversation(name)

    fun user(content: String) {
        conversation.append(userMessage(content))
    }

    fun system(content: String) {
        conversation.append(systemMessage(content))
    }

    fun build(): Conversation = conversation
}

@BuilderMarker
fun conversation(name: String? = null, actions: ConversationBuilder.() -> Unit): Conversation =
    ConversationBuilder(name).apply(actions).build()
