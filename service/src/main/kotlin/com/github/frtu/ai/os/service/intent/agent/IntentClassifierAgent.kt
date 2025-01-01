package com.github.frtu.ai.os.service.intent.agent

import com.fasterxml.jackson.databind.JsonNode
import com.fasterxml.jackson.databind.node.NullNode
import com.github.frtu.ai.os.service.intent.model.Intent
import com.github.frtu.ai.os.service.intent.model.IntentResult
import com.github.frtu.kotlin.action.management.ActionId
import com.github.frtu.kotlin.ai.os.llm.Chat
import com.github.frtu.kotlin.ai.os.llm.agent.AgentExecuter
import com.github.frtu.kotlin.serdes.json.ext.objToJsonNode
import com.github.frtu.kotlin.serdes.json.ext.toJsonObj
import com.github.frtu.kotlin.serdes.json.schema.SchemaGen
import com.github.frtu.kotlin.tool.StructuredTool

/**
 * @see <a href="https://memo.d.foundation/playground/ai/building-llm-system/intent-classification-by-llm/">Intent classification by LLM</a>
 */
class IntentClassifierAgent(
    // Chat engine
    chat: Chat,
    // Instruction prompt
    instructions: String,
    // All Intents
    val intents: List<Intent>,
) : AgentExecuter(
    id = ActionId(TOOL_NAME),
    description = "Agent that classify user request into Intent classification",
    instructions = instructions,
    chat = chat,
    toolRegistry = null,
    parameterJsonSchema = SchemaGen.STRING_SCHEMA,
    returnJsonSchema = SchemaGen.generateJsonSchema(IntentResult::class.java),
    isStateful = true,
), StructuredTool<String, IntentResult?> {
    init {
        logger.info("Creating Intent recognition with instruction:\n{}", instructions)
    }

    constructor(
        chat: Chat,
        intents: List<Intent>,
    ) : this(
        chat = chat,
        intents = intents,
        instructions = buildInstruction(
            intentDescriptionMap = intents.associateBy({ it.id }, { it.description }),
            baseInstruction = BASE_INSTRUCTION[0],
            prefixDescription = null,
            prefixIntent = "* ",
            closingInstruction = """
                You are given an utterance and you have to classify it into an intent. 
                It's a matter of life and death, only respond with the intent in the following list
                List:[${intents.joinToString(separator = ",") { it.id }}]
                
                Response format should be a JSON with intent and reasoning explanation.
                Ex : {"intent": "$DEFAULT_INTENT_ID", "reasoning": "1. The user wants to put money into stocks, which is a form of investment. 2. They're asking about options, seeking advice on investment choices."}
            """.trimIndent(),
        ),
    )

    companion object {
        const val DEFAULT_INTENT_ID = "Other"
        val DEFAULT_INTENT_ITEM = Intent(
            id = DEFAULT_INTENT_ID,
            description = "Choose this if the intent doesn't fit into any of the above categories"
        )

        const val TOOL_NAME = "intent-classifier-agent"
    }

    override suspend fun execute(parameter: JsonNode): JsonNode {
        val request = parameter.asText()
        val sendMessage = answer(request)
        return sendMessage.content?.objToJsonNode() ?: NullNode.instance
    }

    override suspend fun execute(parameter: String): IntentResult? {
        val sendMessage = answer(parameter)
        return sendMessage.content?.toJsonObj(IntentResult::class.java)
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
    prefixDescription: String? = null,
    prefixIntent: String? = null,
    closingInstruction: String? = null,
): String {
    val result = StringBuilder()
    result.append(baseInstruction)
    result.append("\n")
    for ((intent, description) in intentDescriptionMap) {
        prefixIntent?.let { result.append(it) }
        result.append(intent).append(" -> ")
        prefixDescription?.let { result.append(it) }
        result.append(description).append("\n")
    }
    closingInstruction?.let { result.append(it) }
    result.append("\n")
    return result.toString()
}
