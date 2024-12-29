package com.github.frtu.ai.os.service.intent.agent

import com.github.frtu.kotlin.ai.spring.builder.ChatApiConfigs

object IntentClassifierAgentMain

suspend fun main() {
    val agent = IntentClassifierAgent(
        chat = ChatApiConfigs().chatOllama(
            model = "llama3",
        ),
        buildInstruction(mapOf(
            "Delivery status" to "Inquiries about the current status of a delivery.",
            "Unblock delivery" to "Delivery is blocked and need to call API to unblock.",
            "Other" to "Choose this if the query doesn’t fall into any of the other intents.",
        ),
        baseInstruction = BASE_INSTRUCTION[1],
        prefixDescription = "",
        prefixIntent = "",
        )
    )
    val answer = agent.answer("Hey my command 12345678 should be delivered by Ninja Van. Can you help to check?")
    println(answer.content)
}