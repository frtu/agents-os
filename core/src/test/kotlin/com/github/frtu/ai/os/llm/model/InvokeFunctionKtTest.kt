package com.github.frtu.ai.os.llm.model

import com.github.frtu.ai.os.utils.getInt
import com.github.frtu.ai.os.utils.getString
import com.github.frtu.ai.os.utils.getJsonObject
import io.kotest.matchers.nulls.shouldBeNull
import io.kotest.matchers.nulls.shouldNotBeNull
import io.kotest.matchers.shouldBe
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive
import org.junit.jupiter.api.Test

import org.slf4j.LoggerFactory

class InvokeFunctionKtTest {
    @Test
    fun `parseContent json array`() {
        //--------------------------------------
        // 1. Init
        //--------------------------------------
        val content = """
            [
              {
                "FunctionName": "$functionName",
                "Parameters": [
                  {
                    "Name": "nights",
                    "Value": "7"
                  },
                  {
                    "Name": "rooms",
                    "Value": "1"
                  }
                ]
              }
            ]
        """.trimIndent()

        //--------------------------------------
        // 2. Execute
        //--------------------------------------
        val result = parseContent(content)
        logger.debug("result:$result")

        //--------------------------------------
        // 3. Validate
        //--------------------------------------
        with(result) {
            shouldNotBeNull()
            name shouldBe functionName
            with(parameters) {
                shouldNotBeNull()
                size shouldBe 2
                with(parameters.getJsonObject(0)) {
                    logger.trace("jsonObject:$this")
                    shouldNotBeNull()
                    getString("Name") shouldBe "nights"
                    getInt("Value") shouldBe 7
                }
                with(parameters.getJsonObject(1)) {
                    logger.trace("jsonObject:$this")
                    shouldNotBeNull()
                    getString("Name") shouldBe "rooms"
                    getInt("Value") shouldBe 1
                }
            }
        }
    }

    @Test
    fun `parseContent unstructured text`() {
        //--------------------------------------
        // 1. Init
        //--------------------------------------
        val content = """
            Here's the JSON representation of the given input in the specified format:
            ```json
            [
              {
                "FunctionName": "$functionName",
                "Parameters": [
                  {
                    "Name": "nights",
                    "Value": "5"
                  },
                  {
                    "Name": "rooms",
                    "Value": "2"
                  }
                ]
              }
            ]
            ```
        """.trimIndent()

        //--------------------------------------
        // 2. Execute
        //--------------------------------------
        val result = parseContent(content)
        logger.debug("result:$result")

        //--------------------------------------
        // 3. Validate
        //--------------------------------------
        with(result) {
            shouldNotBeNull()
            name shouldBe functionName
            with(parameters) {
                shouldNotBeNull()
                size shouldBe 2
                with(parameters.getJsonObject(0)) {
                    logger.trace("jsonObject:$this")
                    shouldNotBeNull()
                    getString("Name") shouldBe "nights"
                    getInt("Value") shouldBe 5
                }
                with(parameters.getJsonObject(1)) {
                    logger.trace("jsonObject:$this")
                    shouldNotBeNull()
                    getString("Name") shouldBe "rooms"
                    getInt("Value") shouldBe 2
                }
            }
        }
    }

    @Test
    fun `parseContent empty`() {
        //--------------------------------------
        // 1. Init
        //--------------------------------------
        val content = "  \n \t \t"

        //--------------------------------------
        // 2. Execute
        //--------------------------------------
        val result = parseContent(content)
        logger.debug("result:$result")

        //--------------------------------------
        // 3. Validate
        //--------------------------------------
        with(result) {
            shouldBeNull()
        }
    }

    @Test
    fun `parseContent erroneous JSON`() {
        //--------------------------------------
        // 1. Init
        //--------------------------------------
        val content = """
        ```["FunctionName": "GetHotel","Parameters":[{"Name":"nights","Value":"7"},{"Name":"rooms","Value":"1"}]]```
        """.trimIndent()

        //--------------------------------------
        // 2. Execute
        //--------------------------------------
        val result = parseContent(content)
        logger.debug("result:$result")

        //--------------------------------------
        // 3. Validate
        //--------------------------------------
        with(result) {
            shouldBeNull()
        }
    }

    private val functionName = "GetHotel"

    private val logger = LoggerFactory.getLogger(this::class.java)
}