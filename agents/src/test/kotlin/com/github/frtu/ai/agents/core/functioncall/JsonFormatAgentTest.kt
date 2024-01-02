package com.github.frtu.ai.agents.core.functioncall

import com.github.frtu.ai.os.llm.Chat
import com.github.frtu.ai.os.llm.openai.OpenAiCompatibleChat
import com.github.frtu.ai.os.memory.Conversation
import com.github.frtu.ai.os.tool.agent.AgentCallGenerator.generateSystemPrompt
import com.github.frtu.ai.os.utils.getInt
import com.github.frtu.ai.os.utils.getJsonObject
import com.github.frtu.ai.os.utils.getString
import io.kotest.common.runBlocking
import io.kotest.matchers.nulls.shouldNotBeNull
import io.kotest.matchers.shouldBe
import org.junit.jupiter.api.Test
import org.slf4j.LoggerFactory

class JsonFormatAgentTest {

    @Test
    fun convertToJson() {
        runBlocking {
            //--------------------------------------
            // 1. Init
            //--------------------------------------
            val chat: Chat = OpenAiCompatibleChat(
                model = "mistral-7b-instruct-v0.1.Q4_K_M.gguf",
                baseUrl = "http://127.0.0.1:5001/v1/",
                defaultEvaluator = { chatChoices -> chatChoices.first() }
            )

            //--------------------------------------
            // 2. Execute
            //--------------------------------------
            val result = with(
                Conversation(generateSystemPrompt(JsonFormatAgent::convertTextToJson, JsonFormatAgent::class))
            ) {
                chat.sendMessage(user("Get an hotel for 7 nights for 1 room"))
            }
            logger.debug("result:$result")

            //--------------------------------------
            // 3. Validate
            //--------------------------------------
            with(result) {
                shouldNotBeNull()
                invokeFunction.shouldNotBeNull()
                logger.trace("result:$invokeFunction")
                with(invokeFunction) {
                    shouldNotBeNull()
                    name shouldBe "GetHotel"
                    with(parameters) {
                        shouldNotBeNull()
                        size shouldBe 2
                        with(parameters.getJsonObject(0)) {
                            logger.trace("jsonObject[0]:$this")
                            shouldNotBeNull()
                            getString("Name") shouldBe "nights"
                            getInt("Value") shouldBe 7
                        }
                        with(parameters.getJsonObject(1)) {
                            logger.trace("jsonObject[1]:$this")
                            shouldNotBeNull()
                            getString("Name") shouldBe "rooms"
                            getInt("Value") shouldBe 1
                        }
                    }
                }
            }
        }
    }

    private val logger = LoggerFactory.getLogger(this::class.java)
}