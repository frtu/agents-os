package com.github.frtu.ai.os.utils

import com.fasterxml.jackson.module.kotlin.jacksonObjectMapper
import com.kjetland.jackson.jsonSchema.JsonSchemaConfig
import com.kjetland.jackson.jsonSchema.JsonSchemaDraft
import com.kjetland.jackson.jsonSchema.JsonSchemaGenerator
import com.kjetland.jackson.jsonSchema.SubclassesResolverImpl
import org.slf4j.LoggerFactory

/**
 * Json Schema generator
 */
object SchemaGen {
    private val objectMapper = jacksonObjectMapper()
    private val jsonSchemaGenerator: JsonSchemaGenerator

    init {
        // https://github.com/mbknor/mbknor-jackson-jsonSchema/tree/master
        val config: JsonSchemaConfig = JsonSchemaConfig.vanillaJsonSchemaDraft4()
//                .withJsonSchemaDraft(JsonSchemaDraft.DRAFT_07)
//                .withSubclassesResolver(SubclassesResolverImpl()
//                        .withPackagesToScan(listOf(
//                                "this.is.myPackage",
//                        ))
//                        .withClassesToScan(listOf(
//                                "this.is.myPackage.MyClass",
//                        ))
//                        //.withClassGraph() - or use this one to get full control..
//                )
        jsonSchemaGenerator = JsonSchemaGenerator(objectMapper, false, config)
    }


    fun generateJsonSchema(parameterClass: Class<*>): String {
        return objectMapper.writeValueAsString(jsonSchemaGenerator.generateJsonSchema(parameterClass)).also {
            logger.trace("Generate schema:[$it]")
        }
    }

    private val logger = LoggerFactory.getLogger(this::class.java)
}