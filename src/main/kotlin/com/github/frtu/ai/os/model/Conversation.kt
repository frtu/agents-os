package com.github.frtu.ai.os.model

/**
 * Message class is a base unit from a Thread
 * @author frtu
 */
data class Conversation(
    val name: String? = null,
    val messages: MutableList<Message> = mutableListOf(),
) {
    fun append(message: Message) {
        messages.add(message)
    }
}
