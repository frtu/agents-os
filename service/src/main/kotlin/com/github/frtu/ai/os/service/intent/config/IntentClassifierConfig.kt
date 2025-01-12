package com.github.frtu.ai.os.service.intent.config

import com.github.frtu.kotlin.ai.feature.intent.agent.IntentClassifierAgent
import com.github.frtu.kotlin.ai.feature.intent.model.Intent
import com.github.frtu.kotlin.ai.os.llm.Chat
import com.github.frtu.kotlin.ai.os.llm.agent.UnstructuredBaseAgent
import com.github.frtu.kotlin.tool.Tool
import org.slf4j.LoggerFactory
import org.springframework.beans.factory.annotation.Qualifier
import org.springframework.context.annotation.Bean
import org.springframework.context.annotation.Configuration

@Configuration
class IntentClassifierConfig {
    @Bean
    @Qualifier(IntentClassifierAgent.TOOL_NAME)
    fun intentClassifierAgent(
        chat: Chat,
        registry: List<UnstructuredBaseAgent>,
    ): IntentClassifierAgent = IntentClassifierAgent(
        chat = chat,
        intents = intents(registry)
    ).also {
        logger.info("Building IntentClassifierAgent with intents:{}", it.intents)
    }

    fun intents(
        registry: List<Tool>,
    ): List<Intent> = registry.map { tool ->
        Intent(tool.id.value, tool.description).also {
            logger.info("Creating Intents:{}", it)
        }
    }.toMutableList()

    private val logger = LoggerFactory.getLogger(this::class.java)
}