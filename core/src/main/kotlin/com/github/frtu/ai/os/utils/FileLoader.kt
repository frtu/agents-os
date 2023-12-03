package com.github.frtu.ai.os.utils

import org.slf4j.LoggerFactory

/**
 * Loading file from classpath
 */
object FileLoader {
    fun readFileFromClasspath(filePath: String) = this::class.java.getClassLoader().getResource(filePath)
        ?.readText(Charsets.UTF_8).also {
            logger.trace("Loaded fileName=[$filePath] with content=[${it?.subSequence(0, minOf(200, it.length))}]")
        }
        ?: throw IllegalArgumentException("filePath:'$filePath' doesn't exist")

    private val logger = LoggerFactory.getLogger(this::class.java)
}