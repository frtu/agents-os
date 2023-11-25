package com.github.frtu.ai.agents.os.app

import com.aallam.openai.api.chat.ChatMessage
import com.aallam.openai.api.chat.ChatRole
import com.aallam.openai.api.chat.FunctionCall

class Conversation(
    private val conversation: MutableList<ChatMessage> = mutableListOf()
) {
    fun system(content: String): Conversation = addMessage(ChatRole.System, content)

    fun user(content: String): Conversation = addMessage(ChatRole.User, content)

    fun assistant(content: String): Conversation = addMessage(ChatRole.Assistant, content)

    fun function(functionName: String, content: String): Conversation =
        addMessage(ChatRole.Function, content, functionName)

    fun addResponse(message: ChatMessage) = addMessage(
        role = message.role,
        content = message.content.orEmpty(),
        functionCall = message.functionCall,
    )

    fun getChatMessages(): List<ChatMessage> = conversation

    private fun addMessage(
        role: ChatRole,
        content: String? = null,
        name: String? = null,
        functionCall: FunctionCall? = null,
    ): Conversation = addMessage(
        ChatMessage(role, content, name, functionCall)
    )

    private fun addMessage(message: ChatMessage): Conversation {
        conversation.add(message)
        return this
    }
}
