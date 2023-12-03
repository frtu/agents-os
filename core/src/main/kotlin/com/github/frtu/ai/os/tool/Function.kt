package com.github.frtu.ai.os.tool

import com.aallam.openai.api.chat.ChatCompletionFunction
import com.aallam.openai.api.chat.Parameters
import com.github.frtu.ai.os.utils.SchemaGen
import kotlin.reflect.KFunction2

/**
 * Base class for callable function
 */
class Function(
    val name: String,
    val description: String? = null,
    val action: KFunction2<String, String, String>,
    val jsonSchema: String,
) {
    fun toChatCompletionFunction() = ChatCompletionFunction(
        name, description,
        Parameters.fromJsonString(jsonSchema),
    )
}

fun function(
    name: String,
    description: String? = null,
    action: KFunction2<String, String, String>,
    jsonSchema: String
) = Function(name, description, action, jsonSchema)

fun function(
    name: String,
    description: String? = null,
    action: KFunction2<String, String, String>,
    parameterClass: Class<*>,
) = Function(name, description, action, SchemaGen.generateJsonSchema(parameterClass))