package com.github.frtu.ai.os.service.intent.config

import com.github.frtu.ai.os.service.agent.SummarizerAgent
import com.github.frtu.kotlin.ai.feature.intent.agent.IntentClassifierAgent
import com.github.frtu.kotlin.ai.os.llm.Chat
import com.github.frtu.kotlin.ai.spring.builder.ChatApiConfigs
import io.kotest.matchers.nulls.shouldNotBeNull
import io.kotest.matchers.shouldBe
import kotlinx.coroutines.runBlocking
import org.junit.jupiter.api.Test
import org.slf4j.LoggerFactory
import org.springframework.boot.test.context.runner.ApplicationContextRunner
import org.springframework.context.annotation.Bean
import org.springframework.context.annotation.ComponentScan
import org.springframework.context.annotation.Configuration

class IntentClassifierConfigTest {
    private val applicationContextRunner = ApplicationContextRunner()

    @Test
    fun intentClassifierAgent() {
        //--------------------------------------
        // 1. Init
        //--------------------------------------
        // Init var
        val userQuestion = "Can you help me to summarize this text?"
        val intentId = SummarizerAgent.TOOL_NAME

        applicationContextRunner
            //--------------------------------------
            // 2. Execute
            //--------------------------------------
            .withUserConfiguration(
                IntentClassifierConfig::class.java,
                SampleToolConfig::class.java,
            )
            .run { context ->
                runBlocking {
                    //--------------------------------------
                    // 3. Validate
                    //--------------------------------------
                    // Check precondition (ToolRegistry should be initialised correctly)
                    context.getBean(intentId).shouldNotBeNull()

                    // Check against Tool to Intent translation
                    val agent = context.getBean(IntentClassifierAgent::class.java)
                    logger.debug("result:{}", agent.intents)

                    with(agent.intents) {
                        shouldNotBeNull()
                    }

                    val result = agent.execute(userQuestion)
                    logger.debug("Intent:{}", result)
                    with(result) {
                        shouldNotBeNull()
                        intent shouldBe intentId
                    }
                }
            }
    }

    private val logger = LoggerFactory.getLogger(this::class.java)
}


@Configuration
@ComponentScan(basePackageClasses = [SummarizerAgent::class])
class SampleToolConfig {
    @Bean
    fun chat(): Chat = ChatApiConfigs().chatOllama(
        model = "llama3",
    )
}