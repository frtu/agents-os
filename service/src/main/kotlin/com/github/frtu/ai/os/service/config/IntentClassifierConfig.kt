package com.github.frtu.ai.os.service.config

import com.github.frtu.ai.os.service.agent.IntentClassifierAgent
import com.github.frtu.ai.os.service.agent.buildInstruction
import com.github.frtu.kotlin.ai.os.llm.Chat
import com.github.frtu.kotlin.tool.ToolRegistry
import org.springframework.beans.factory.annotation.Qualifier
import org.springframework.context.annotation.Bean
import org.springframework.context.annotation.Configuration

@Configuration
class IntentClassifierConfig {
    @Bean
    @Qualifier(IntentClassifierAgent.TOOL_NAME)
    fun intentClassifierAgent(
        chat: Chat,
        toolRegistry: ToolRegistry,
    ): IntentClassifierAgent = IntentClassifierAgent(
        chat,
        buildInstruction(toolRegistry.getRegistry().map { (id, tool) ->
            id.value to tool.description
        }.toMap())
    )
}