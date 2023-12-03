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
    constructor(
        name: String,
        description: String,
        action: KFunction2<String, String, String>,
        parameterClass: Class<*>,
    ) : this(name, description, action, SchemaGen.generateJsonSchema(parameterClass))

    fun toChatCompletionFunction() = ChatCompletionFunction(
        name, description,
        Parameters.fromJsonString(jsonSchema),
    )
}