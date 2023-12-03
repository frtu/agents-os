package com.github.frtu.ai.agents.os.app

object SchemaLoader {
    fun readSchemaFromFile(fileName: String) = this::class.java.getClassLoader().getResource(fileName)
        ?.readText(Charsets.UTF_8)
        ?: throw IllegalArgumentException("fileName:'$fileName' doesn't exist")
}