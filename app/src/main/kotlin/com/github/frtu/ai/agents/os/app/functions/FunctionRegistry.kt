package com.github.frtu.ai.agents.os.app.functions

import com.aallam.openai.api.chat.ChatCompletionFunction
import com.aallam.openai.api.chat.Parameters
import com.github.frtu.ai.agents.os.app.utils.SchemaGen.generateJsonSchema

class FunctionRegistry(
    val registry: MutableList<ChatCompletionFunction> = mutableListOf(),
) {
    fun addFunction(
        name: String,
        description: String,
        parameterClass: Class<*>,
    ) {
        registry.add(
            ChatCompletionFunction(
                name, description,
                Parameters.fromJsonString(generateJsonSchema(parameterClass)),
            )
        )
    }
}