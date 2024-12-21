package com.github.frtu.ai.os.service.agent

import com.github.frtu.kotlin.ai.spring.builder.ChatApiConfigs

object IntentClassifierAgentMain

suspend fun main() {
    val agent = IntentClassifierAgent(
        chat = ChatApiConfigs().chatOpenAI(
            apiKey = "sk-xxx"
        ),
        buildInstruction(mapOf(
            "Order Status" to "Inquiries about the current status of an order, including delivery tracking and estimated arrival times.",
            "Product Information" to "Questions regarding product details, specifications, availability, or compatibility.",
            "Payments" to "Queries related to making payments, payment methods, billing issues, or transaction problems.",
            "Returns" to "Requests or questions about returning a product, including return policies and procedures.",
            "Feedback" to "User comments, reviews, or general feedback about products, services, or experiences.",
            "Other" to "Choose this if the query doesn’t fall into any of the other intents.",
        ))
    )
    val answer = agent.answer("")
    println(answer.content)
}