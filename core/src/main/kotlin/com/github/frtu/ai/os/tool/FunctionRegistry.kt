package com.github.frtu.ai.os.tool

import com.aallam.openai.api.chat.ChatCompletionFunction
import com.aallam.openai.api.chat.Parameters
import com.github.frtu.ai.os.utils.SchemaGen.generateJsonSchema
import kotlin.reflect.KFunction2
import org.slf4j.LoggerFactory

/**
 * Registry for all usable functions
 */
class FunctionRegistry(
    private val registry: MutableList<ChatCompletionFunction> = mutableListOf(),
    private val availableFunctions: MutableMap<String, KFunction2<String, String, String>> = mutableMapOf(),
) {
    fun getRegistry(): List<ChatCompletionFunction> = registry
    fun getAvailableFunctions() = availableFunctions

    fun getFunction(name: String) = availableFunctions[name]
        ?: error("Function $name not found")

    fun registerFunction(
        name: String,
        description: String,
        kFunction2: KFunction2<String, String, String>,
        parameterClass: Class<*>,
    ) = registerFunction(name, description, kFunction2, generateJsonSchema(parameterClass))

    fun registerFunction(
        name: String,
        description: String,
        kFunction2: KFunction2<String, String, String>,
        jsonSchema: String
    ) {
        logger.debug("Registering new function: name=[$name] description=[$description] function:[${kFunction2.name}] jsonSchema=[$jsonSchema]")
        registry.add(
            ChatCompletionFunction(
                name, description,
                Parameters.fromJsonString(jsonSchema),
            )
        )
        availableFunctions[name] = kFunction2
    }

    private val logger = LoggerFactory.getLogger(this::class.java)
}