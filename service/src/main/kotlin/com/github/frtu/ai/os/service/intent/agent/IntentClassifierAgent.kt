package com.github.frtu.ai.os.service.intent.agent

import com.github.frtu.kotlin.ai.os.llm.Chat
import com.github.frtu.kotlin.ai.os.llm.agent.UnstructuredBaseAgent

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
    init {
        logger.info("Creating Intent recognition with instruction:{}", instructions)
    }

    constructor(
        chat: Chat,
        intents: List<Intent>,
    ) : this(
        chat = chat,
        intentDescriptionMap = intents.associateBy({ it.id }, { it.description }),
        closingInstruction = """
            You are given an utterance and you have to classify it into an intent. 
            It's a matter of life and death, only respond with the intent in the following list
            List:[${intents.joinToString(separator = ",") { it.id }}]
        """.trimIndent(),
    )

    constructor(
        chat: Chat,
        intentDescriptionMap: Map<String, String>,
        baseInstruction: String = BASE_INSTRUCTION[0],
        prefixDescription: String = "d: ",
        prefixIntent: String = "",
        closingInstruction: String? = """
            You are given an utterance and you have to classify it into an intent. 
            Only respond with the intent using lower case & separated with space :
            u: I want a warm hot chocolate: a:warm drink
        """.trimIndent(),
    ) : this(
        chat = chat,
        instructions = buildInstruction(
            intentDescriptionMap = intentDescriptionMap,
            baseInstruction = baseInstruction,
            prefixDescription = prefixDescription,
            prefixIntent = prefixIntent,
            closingInstruction = closingInstruction,
        )
    )

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
        You are given an utterance and you have to classify it into an intent. 
        Only respond with the intent using lower case & separated with space :
        u: I want a warm hot chocolate: a:warm drink
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
