package com.github.frtu.ai.os.service.intent.agent

import com.github.frtu.kotlin.ai.os.llm.Chat
import com.github.frtu.kotlin.ai.spring.builder.ChatApiConfigs
import io.kotest.matchers.nulls.shouldNotBeNull
import io.kotest.matchers.shouldBe
import kotlinx.coroutines.runBlocking
import org.junit.jupiter.api.Test
import org.slf4j.LoggerFactory

class IntentClassifierAgentTest {
    private val chat: Chat = ChatApiConfigs().chatOllama(
        model = "llama3",
    )

    @Test
    fun `Detect intent 'Delivery status'`() = matchIntentWithQuery(
        "Delivery status", "Hey, my command 12345678 should be delivered by Ninja Van. Can you help to check?"
    )

    @Test
    fun `Detect intent 'Unblock delivery'`() = matchIntentWithQuery(
        "Unblock delivery",
        "Hi, my delivery always get rejected. For the past several times, I asked but still nothing. Please help to resolve it."
    )

    @Test
    fun `Detect intent 'Other'`() = matchIntentWithQuery(
        "Other",
        "added an integration wto this channel."
    )

    private fun matchIntentWithQuery(expectedIntent: String, userMessage: String): Unit = runBlocking {
        //--------------------------------------
        // 1. Init
        //--------------------------------------
        // Init var
        val agent = IntentClassifierAgent(
            chat = chat,
            intents = listOf(
                Intent(id = "Delivery status", description = "Inquiries about the current status of a delivery."),
                Intent(id = "Unblock delivery", description = "Delivery is blocked and need to call API to unblock."),
                Intent(id = "Other", description = "Choose this if the query doesn’t fall into any of the other intents."),
            )
        )

        //--------------------------------------
        // 2. Execute
        //--------------------------------------
        val result = agent.answer(userMessage)
        logger.debug("result:{}", result)

        //--------------------------------------
        // 3. Validate
        //--------------------------------------
        // Check metadata
        with(result) {
            shouldNotBeNull()
            // LLM may mix upper & lower case
            content!!.lowercase() shouldBe expectedIntent.lowercase()
        }
    }

    private val logger = LoggerFactory.getLogger(this::class.java)
}
