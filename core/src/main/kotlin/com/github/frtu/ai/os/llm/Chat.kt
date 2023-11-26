package com.github.frtu.ai.os.llm

import com.aallam.openai.api.chat.ChatChoice
import com.github.frtu.ai.os.memory.Conversation

interface Chat {
    suspend fun sendMessage(
        conversation: Conversation,
    ): ChatChoice
}