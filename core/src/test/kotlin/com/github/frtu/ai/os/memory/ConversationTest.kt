package com.github.frtu.ai.os.memory

import com.aallam.openai.api.chat.ChatRole
import io.kotest.matchers.nulls.shouldNotBeNull
import io.kotest.matchers.shouldBe
import org.junit.jupiter.api.Test
import org.slf4j.LoggerFactory

class ConversationTest {

    @Test
    fun `test add & getMessages in order`() {
        //--------------------------------------
        // 1. Init
        //--------------------------------------
        val systemContent = "You're an helpful assistant"
        val userContent = "Hello"
        val assistantContent = "Assistant"
        val functionName = "functionName"
        val functionContent = "{'id': 123}"

        //--------------------------------------
        // 2. Execute
        //--------------------------------------
        val result = Conversation(systemContent)
        result.user(userContent)
        result.assistant(assistantContent)
        result.function(functionName, functionContent)

        logger.debug("result:$result")

        //--------------------------------------
        // 3. Validate
        //--------------------------------------
        with(result) {
            shouldNotBeNull()
            with(getMessages()) {
                size shouldBe 4
                with(this[0]) {
                    role shouldBe ChatRole.System
                    content shouldBe systemContent
                }
                with(this[1]) {
                    role shouldBe ChatRole.User
                    content shouldBe userContent
                }
                with(this[2]) {
                    role shouldBe ChatRole.Assistant
                    content shouldBe assistantContent
                }
                with(this[3]) {
                    role shouldBe ChatRole.Function
                    name shouldBe functionName
                    content shouldBe functionContent
                }
            }
        }
    }

    private val logger = LoggerFactory.getLogger(this::class.java)
}