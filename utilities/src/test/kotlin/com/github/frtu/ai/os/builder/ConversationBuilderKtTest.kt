package com.github.frtu.ai.os.builder

import io.kotest.matchers.nulls.shouldNotBeNull
import io.kotest.matchers.shouldBe
import org.junit.jupiter.api.Test

import org.slf4j.LoggerFactory

class ConversationBuilderKtTest {

    @Test
    fun conversation() {
        //--------------------------------------
        // 1. Init
        //--------------------------------------
        val conversationName = "Conversation name"

        //--------------------------------------
        // 2. Execute
        //--------------------------------------
        val result = conversation(conversationName) {
            user("Hello")
        }
        logger.debug("result:$result")

        //--------------------------------------
        // 3. Validate
        //--------------------------------------
        with(result) {
            result.shouldNotBeNull()
            name shouldBe conversationName
            messages.size shouldBe 2
        }
    }

    private val logger = LoggerFactory.getLogger(this::class.java)
}