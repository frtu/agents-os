package com.github.frtu.ai.os.service.intent.agent

import com.github.frtu.ai.os.service.intent.agent.IntentClassifierAgent.Companion.DEFAULT_INTENT_ITEM
import com.github.frtu.ai.os.service.intent.model.Intent
import com.github.frtu.kotlin.ai.spring.builder.ChatApiConfigs

object IntentClassifierAgentMain

suspend fun main() {
    val agent = IntentClassifierAgent(
        chat = ChatApiConfigs().chatOllama(
            model = "llama3",
        ),
        intents = listOf(
            Intent(id = "Delivery status", description = "Inquiries about the current status of a delivery."),
            Intent(id = "Unblock delivery", description = "Delivery is blocked and need to call API to unblock."),
            DEFAULT_INTENT_ITEM
        ),
    )
    val answer = agent.answer("Hey my command 12345678 should be delivered by Ninja Van. Can you help to check?")
    println(answer.content)
}