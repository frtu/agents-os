package com.github.frtu.ai.os.model

import com.github.frtu.ai.os.memory.Conversation
import io.kotest.matchers.nulls.shouldNotBeNull
import io.kotest.matchers.shouldBe
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
        result.user("Hello")

        logger.debug("result:$result")

        //--------------------------------------
        // 3. Validate
        //--------------------------------------
        with(result) {
            shouldNotBeNull()
            with(getChatMessages()) {
                size shouldBe 1
            }
        }
    }

    private val logger = LoggerFactory.getLogger(this::class.java)
}