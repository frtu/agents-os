package com.github.frtu.ai.os.tool.agent

import com.github.frtu.ai.agents.Agent
import com.github.frtu.ai.agents.getAction
import com.github.frtu.ai.agents.getPersona
import com.github.frtu.ai.os.utils.SchemaGen.generateJsonSchema
import kotlin.reflect.KClass
import kotlin.reflect.KFunction
import kotlin.reflect.jvm.jvmErasure

object AgentCallGenerator {
    fun generateSystemPrompt(functionToCall: KFunction<*>, owningClass: KClass<out Agent>): String = buildString {
        append(owningClass.getPersona())
        append("\n\n")
        append(functionToCall.getAction())
        append("\n\n")
        append(
            """
        The output should be formatted as a JSON instance that conforms to the JSON schema below.

        As an example, for the schema {"properties": {"foo": {"title": "Foo", "description": "a list of strings", "type": "array", "items": {"type": "string"}}}, "required": ["foo"]}
        the object {"foo": ["bar", "baz"]} is a well-formatted instance of the schema. The object {"properties": {"foo": ["bar", "baz"]}} is not well-formatted.

        Here is the output schema:
        ```
        """.trimIndent()
        )
        append(generateJsonSchema(functionToCall.returnType.jvmErasure.java))
        append(
            """
        ```
        """.trimIndent()
        )
    }
}


