package com.github.frtu.ai.os.utils

import com.github.frtu.ai.os.utils.FileLoader.readFileFromClasspath
import io.kotest.matchers.nulls.shouldNotBeNull
import io.kotest.matchers.shouldBe
import org.junit.jupiter.api.Test

import org.junit.jupiter.api.Assertions.*
import org.slf4j.LoggerFactory
import samples.model.WeatherInfo

class FileLoaderTest {
    @Test
    fun `Testing readFileFromClasspath`() {
        //--------------------------------------
        // 1. Init
        //--------------------------------------
        val filePath = "./data/file.txt"

        //--------------------------------------
        // 2. Execute
        //--------------------------------------
        val result = readFileFromClasspath(filePath)
        logger.debug("result:$result")

        //--------------------------------------
        // 3. Validate
        //--------------------------------------
        with(result) {
            shouldNotBeNull()
            result shouldBe "test"
        }
    }

    private val logger = LoggerFactory.getLogger(this::class.java)
}