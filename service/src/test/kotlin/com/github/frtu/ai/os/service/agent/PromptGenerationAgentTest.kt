package com.github.frtu.ai.os.service.agent

import com.github.frtu.kotlin.ai.spring.builder.ChatApiConfigs

object PromptGenerationAgentMain

suspend fun main() {
    val agent = PromptGenerationAgent(
        chat = ChatApiConfigs().chatOpenAI(
            apiKey = "sk-xxx"
        )
    )
    val answer = agent.answer("")
    println(answer.content)
}