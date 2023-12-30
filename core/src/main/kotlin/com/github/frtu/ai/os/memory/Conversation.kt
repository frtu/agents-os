package com.github.frtu.ai.os.memory

import com.aallam.openai.api.chat.ChatMessage
import com.aallam.openai.api.chat.ChatRole
import com.aallam.openai.api.chat.FunctionCall

/**
 * Message class is a base unit from a Thread
 * @author frtu
 */
data class Conversation(
    private val systemDirective: String? = null,
    private val conversation: MutableList<ChatMessage> = mutableListOf()
) {
    init {
        systemDirective?.let { system(systemDirective) }
    }

    fun system(content: String): Conversation = append(createMessage(ChatRole.System, content))

    fun user(content: String): Conversation = append(createMessage(ChatRole.User, content))

    fun assistant(content: String): Conversation = append(
        createMessage(ChatRole.Assistant, content)
    )

    fun function(functionName: String, content: String): Conversation =
        append(createMessage(ChatRole.Function, content, functionName))

    fun addResponse(message: ChatMessage) = append(
        createMessage(
            role = message.role,
            content = message.content.orEmpty(),
            functionCall = message.functionCall,
        )
    )

    fun getMessages(): List<ChatMessage> = conversation

    /**
     * Get Total message in conversation
     */
    fun countMessages(): Int = conversation.size

    /**
     * Allow to trim first messages to free some spaces
     */
    fun trimMessages(): Boolean = true

    private fun append(message: ChatMessage): Conversation {
        conversation.add(message)
        return this
    }
}

fun createMessage(
    role: ChatRole,
    content: String? = null,
    name: String? = null,
    functionCall: FunctionCall? = null,
) = ChatMessage(role, content, name, functionCall)