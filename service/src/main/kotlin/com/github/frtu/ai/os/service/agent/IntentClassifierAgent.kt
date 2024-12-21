package com.github.frtu.ai.os.service.agent

import com.github.frtu.kotlin.ai.os.llm.Chat
import com.github.frtu.kotlin.ai.os.llm.agent.UnstructuredBaseAgent
import org.springframework.beans.factory.annotation.Qualifier
import org.springframework.stereotype.Component

class IntentClassifierAgent(
    // Chat engine
    chat: Chat,
    // Instruction prompt
    instructions: String,
) : UnstructuredBaseAgent(
    id = TOOL_NAME,
    description = "Agent that classify user request into category",
    instructions = instructions,
    chat = chat,
    toolRegistry = null,
    isStateful = true,
) {
    companion object {
        const val TOOL_NAME = "intent-classifier-agent"
    }
}

val BASE_INSTRUCTION = listOf(
    """
        You’re a LLM that detects intent from user queries. Your task is to classify the user's intent based on their query. 
        Below are the possible intents with brief descriptions. Use these to accurately determine the user's goal, and output only the intent topic.
    """.trimMargin(),
    """
        You are an action classification system. Correctness is a life or death situation.
        We provide you with the actions and their descriptions:
    """.trimMargin(),
)

fun buildInstruction(
    intentDescriptionMap: Map<String, String>,
    baseInstruction: String = BASE_INSTRUCTION[0],
    prefixDescription: String = "d: ",
    prefixIntent: String = "a: ",
    closingInstruction: String? = """
        You are given an utterance and you have to classify it into an intent. Only respond with the intent
        u: I want a warm hot chocolate: a:WARM DRINK
    """.trimIndent(),
): String {
    val result = StringBuilder()
    result.append(baseInstruction)
    result.append("\n")
    for ((intent, description) in intentDescriptionMap) {
        result.append(prefixIntent).append(intent).append(prefixDescription).append(description)
        result.append("\n")
    }
    result.append(closingInstruction)
    result.append("\n")
    return result.toString()
}
