package com.github.frtu.ai.os.utils

import com.fasterxml.jackson.module.kotlin.jacksonObjectMapper
import com.kjetland.jackson.jsonSchema.JsonSchemaGenerator

/**
 * Json Schema generator
 */
object SchemaGen {
    private val objectMapper = jacksonObjectMapper()
    private val jsonSchemaGenerator = JsonSchemaGenerator(objectMapper)

    fun generateJsonSchema(parameterClass: Class<*>): String {
        return objectMapper.writeValueAsString(jsonSchemaGenerator.generateJsonSchema(parameterClass))
    }
}