package com.github.frtu.ai.os.tool.agent

import com.github.frtu.ai.agents.travel.ValidationAgent
import com.github.frtu.ai.os.tool.agent.AgentCallGenerator.generateSystemPrompt
import io.kotest.matchers.nulls.shouldNotBeNull
import io.kotest.matchers.string.shouldContain
import io.kotest.matchers.string.shouldNotContain
import org.junit.jupiter.api.Test
import org.slf4j.LoggerFactory

class AgentCallGeneratorTest {

    @Test
    fun `test createAgentFunction with return type`() {
        //--------------------------------------
        // 1. Init
        //--------------------------------------
        val owningClass = ValidationAgent::class
        val functionToCall = ValidationAgent::validate

        //--------------------------------------
        // 2. Execute
        //--------------------------------------
        val result = generateSystemPrompt(functionToCall, owningClass)
        logger.debug("result:$result")

        //--------------------------------------
        // 3. Validate
        //--------------------------------------
        with(result) {
            shouldNotBeNull()
            result shouldContain "Here is the output schema"
        }
    }

    @Test
    fun `test createAgentFunction with no return type`() {
        //--------------------------------------
        // 1. Init
        //--------------------------------------
        val owningClass = ValidationAgent::class
        val functionToCall = ValidationAgent::proposeItinerary

        //--------------------------------------
        // 2. Execute
        //--------------------------------------
        val result = generateSystemPrompt(functionToCall, owningClass)
        logger.debug("result:$result")

        //--------------------------------------
        // 3. Validate
        //--------------------------------------
        with(result) {
            shouldNotBeNull()
            result shouldNotContain "Here is the output schema"
        }
    }

    private val logger = LoggerFactory.getLogger(this::class.java)
}