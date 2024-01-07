package com.github.frtu.ai.os.tool.agent

import com.github.frtu.ai.agents.core.functioncall.JsonFormatAgent
import com.github.frtu.ai.agents.travel.ValidationAgent
import com.github.frtu.ai.os.llm.Chat
import com.github.frtu.ai.os.llm.openai.OpenAiCompatibleChat
import com.github.frtu.ai.os.memory.Conversation
import com.github.frtu.ai.os.tool.agent.AgentCallGenerator.generateSystemPrompt
import io.kotest.common.runBlocking
import io.kotest.matchers.nulls.shouldNotBeNull
import io.kotest.matchers.string.shouldContain
import io.kotest.matchers.string.shouldNotContain
import org.junit.jupiter.api.BeforeAll
import org.junit.jupiter.api.Test
import org.slf4j.LoggerFactory

class AgentBuilderTest {
    private lateinit var agentBuilder: AgentBuilder

    @BeforeAll
    fun setup() {
        agentBuilder = AgentBuilder(OpenAiCompatibleChat(
            model = "codellama-7b-instruct.Q4_K_M.gguf",
            baseUrl = "http://127.0.0.1:5001/v1/",
            defaultEvaluator = { chatChoices -> chatChoices.first() }
        ))
    }

    @Test
    fun `test createProxy with return type`() {
        runBlocking {
            //--------------------------------------
            // 1. Init
            //--------------------------------------
            val agent = agentBuilder.createProxy<JsonFormatAgent>()

            //--------------------------------------
            // 2. Execute
            //--------------------------------------
            val result = agent.convertTextToJson("Get an hotel for 7 nights for 1 room")
            logger.debug("== result ==\n$result")

            //--------------------------------------
            // 3. Validate
            //--------------------------------------
            with(result) {
                shouldNotBeNull()
            }
        }
    }

    private val logger = LoggerFactory.getLogger(this::class.java)
}

fun main() {
    val agentBuilder = AgentBuilder(OpenAiCompatibleChat(
        model = "mistral-7b-instruct-v0.1.Q4_K_M.gguf",
        baseUrl = "http://127.0.0.1:5001/v1/",
        defaultEvaluator = { chatChoices -> chatChoices.first() }
    ))

    val agent: JsonFormatAgent = agentBuilder.createProxy<JsonFormatAgent>()

    //--------------------------------------
    // 2. Execute
    //--------------------------------------
    val result = agent.convertTextToJson("Get an hotel for 7 nights for 1 room")
    println("== result ==\n$result")
}