package com.github.frtu.ai.os.model

import io.kotlintest.matchers.types.shouldNotBeNull
import io.kotlintest.shouldBe
import org.junit.jupiter.api.Test
import org.slf4j.LoggerFactory

class ConversationTest {

    @Test
    fun getMessages() {
        //--------------------------------------
        // 1. Init
        //--------------------------------------

        //--------------------------------------
        // 2. Execute
        //--------------------------------------
        val result = Conversation()
        result.append(userMessage("Hello"))

        logger.debug("result:$result")

        //--------------------------------------
        // 3. Validate
        //--------------------------------------
        with(result) {
            shouldNotBeNull()
            messages.size shouldBe 1
        }
    }

    private val logger = LoggerFactory.getLogger(this::class.java)
}