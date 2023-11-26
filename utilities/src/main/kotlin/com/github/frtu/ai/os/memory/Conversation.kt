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
    fun system(content: String): Conversation = append(ChatRole.System, content)

    fun user(content: String): Conversation = append(ChatRole.User, content)

    fun assistant(content: String): Conversation = append(ChatRole.Assistant, content)

    fun function(functionName: String, content: String): Conversation =
        append(ChatRole.Function, content, functionName)

    fun addResponse(message: ChatMessage) = append(
        role = message.role,
        content = message.content.orEmpty(),
        functionCall = message.functionCall,
    )

    fun getChatMessages(): List<ChatMessage> = conversation

    private fun append(
        role: ChatRole,
        content: String? = null,
        name: String? = null,
        functionCall: FunctionCall? = null,
    ): Conversation = append(
        ChatMessage(role, content, name, functionCall)
    )

    private fun append(message: ChatMessage): Conversation {
        conversation.add(message)
        return this
    }
}
