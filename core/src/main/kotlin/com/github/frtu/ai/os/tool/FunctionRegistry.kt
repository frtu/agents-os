package com.github.frtu.ai.os.tool

import com.aallam.openai.api.chat.ChatCompletionFunction
import kotlin.reflect.KFunction2
import org.slf4j.LoggerFactory

/**
 * Registry for all usable functions
 */
class FunctionRegistry(
    private val registry: MutableList<Function> = mutableListOf(),
) {
    fun getRegistry(): List<ChatCompletionFunction> = registry.map { it.toChatCompletionFunction() }
    fun getAvailableFunctions(): Map<String, KFunction2<String, String, String>> = registry.associate { it.name to it.action }

    fun getFunction(name: String): Function = registry.first { name == it.name }
        ?: error("Function $name not found")

    fun registerFunction(
        name: String,
        description: String,
        kFunction2: KFunction2<String, String, String>,
        parameterClass: Class<*>,
    ) = registerFunction(function(name, description, kFunction2, parameterClass))

    fun registerFunction(
        name: String,
        description: String,
        kFunction2: KFunction2<String, String, String>,
        jsonSchema: String
    ) = registerFunction(function(name, description, kFunction2, jsonSchema))

    fun registerFunction(function: Function) {
        logger.debug(
            "Registering new function: name=[${function.name}] description=[${function.description}] " +
                    "function:[${function.action.name}] jsonSchema=[${function.jsonSchema}]"
        )
        registry.add(function)
    }

    private val logger = LoggerFactory.getLogger(this::class.java)
}