package com.github.frtu.ai.os.service.intent.config

import com.github.frtu.ai.os.service.intent.model.Intent
import com.github.frtu.ai.os.service.intent.agent.IntentClassifierAgent
import com.github.frtu.kotlin.ai.os.llm.Chat
import com.github.frtu.kotlin.tool.Tool
import org.springframework.beans.factory.annotation.Qualifier
import org.springframework.context.annotation.Bean
import org.springframework.context.annotation.Configuration

@Configuration
class IntentClassifierConfig {
    @Bean
    @Qualifier(IntentClassifierAgent.TOOL_NAME)
    fun intentClassifierAgent(
        chat: Chat,
        registry: List<Tool>,
    ): IntentClassifierAgent = IntentClassifierAgent(
        chat = chat,
        intents = registry.map { tool ->
            Intent(tool.id.value, tool.description)
        }.toMutableList().apply {
            this.add(IntentClassifierAgent.DEFAULT_INTENT_ITEM)
        }
    )
}