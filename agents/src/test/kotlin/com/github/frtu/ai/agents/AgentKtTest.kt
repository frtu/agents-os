package com.github.frtu.ai.agents

import com.github.frtu.ai.agents.travel.TravelAgent
import com.github.frtu.ai.agents.travel.ValidationAgent
import io.kotest.assertions.throwables.shouldThrow
import io.kotest.matchers.nulls.shouldNotBeNull
import io.kotest.matchers.shouldBe
import io.kotest.matchers.string.shouldContain
import kotlin.reflect.KClass
import kotlin.reflect.KFunction
import org.junit.jupiter.api.Test
import org.slf4j.LoggerFactory

class AgentKtTest {

    @Test
    fun `getPersona for a class tagged with @Persona`() {
        //--------------------------------------
        // 1. Init
        //--------------------------------------
        val agentClass: KClass<out Agent> = TravelAgent::class

        //--------------------------------------
        // 2. Execute
        //--------------------------------------
        val result = agentClass.getPersona()
        logger.debug("result:$result")

        //--------------------------------------
        // 3. Validate
        //--------------------------------------
        with(result) {
            shouldNotBeNull()
            result shouldBe "You are a travel agent who helps users make exciting travel plans."
        }
    }

    @Test
    fun `getPersona for a class without annotation`() {
        //--------------------------------------
        // 1. Init
        //--------------------------------------
        val agentClass: KClass<out Agent> = RandomAgent::class

        //--------------------------------------
        // 2. Execute
        //--------------------------------------
        val result = shouldThrow<IllegalArgumentException> { agentClass.getPersona() }
        logger.debug("result:$result")

        //--------------------------------------
        // 3. Validate
        //--------------------------------------
        with(result) {
            shouldNotBeNull()
            result.message shouldContain agentClass.java.name
        }
    }

    @Test
    fun `getAction for a function tagged with @Action`() {
        //--------------------------------------
        // 1. Init
        //--------------------------------------
        val function = ValidationAgent::validate

        //--------------------------------------
        // 2. Execute
        //--------------------------------------
        val result = function.getAction()
        logger.debug("result:$result")

        //--------------------------------------
        // 3. Validate
        //--------------------------------------
        with(result) {
            shouldNotBeNull()
            result shouldContain "plan_is_valid"
        }
    }

    @Test
    fun `getAction for a function without annotation`() {
        //--------------------------------------
        // 1. Init
        //--------------------------------------
        val function = RandomAgent::withoutAnnotation

        //--------------------------------------
        // 2. Execute
        //--------------------------------------
        val result = shouldThrow<IllegalArgumentException> { function.getAction() }
        logger.debug("result:$result")

        //--------------------------------------
        // 3. Validate
        //--------------------------------------
        with(result) {
            shouldNotBeNull()
            result.message shouldContain function.name
        }
    }

    class RandomAgent : Agent() {
        fun withoutAnnotation(): Nothing = TODO()
    }

    private val logger = LoggerFactory.getLogger(this::class.java)
}