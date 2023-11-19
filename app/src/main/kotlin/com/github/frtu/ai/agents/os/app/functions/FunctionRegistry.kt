package com.github.frtu.ai.agents.os.app.functions

import com.aallam.openai.api.chat.ChatCompletionFunction
import com.aallam.openai.api.chat.Parameters
import com.github.frtu.ai.agents.os.app.utils.SchemaGen.generateJsonSchema
import kotlin.reflect.KFunction2

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

    fun addFunction(
        name: String,
        description: String,
        parameterClass: Class<*>,
        kFunction2: KFunction2<String, String, String>,
    ) {
        registry.add(
            ChatCompletionFunction(
                name, description,
                Parameters.fromJsonString(generateJsonSchema(parameterClass)),
            )
        )
        availableFunctions[name] = kFunction2
    }
}