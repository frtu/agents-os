package com.github.frtu.ai.os.service.prompt.agent

import com.github.frtu.kotlin.ai.os.llm.Chat
import com.github.frtu.kotlin.ai.spring.builder.ChatApiConfigs
import io.kotest.matchers.nulls.shouldNotBeNull
import kotlinx.coroutines.runBlocking
import org.junit.jupiter.api.Test
import org.slf4j.LoggerFactory
import org.springframework.boot.test.context.runner.ApplicationContextRunner
import org.springframework.context.annotation.Bean
import org.springframework.context.annotation.ComponentScan
import org.springframework.context.annotation.Configuration

class PromptGenerationAgentTest {
    private val applicationContextRunner = ApplicationContextRunner()

    @Test
    fun promptGenerationAgent() {
        //--------------------------------------
        // 1. Init
        //--------------------------------------
        // Init var
        val userQuestion = "Create a prompt that can help to write a 2 pages long cartoon story."

        applicationContextRunner
            //--------------------------------------
            // 2. Execute
            //--------------------------------------
            .withUserConfiguration(
                SampleToolConfig::class.java,
            )
            .run { context ->
                runBlocking {
                    //--------------------------------------
                    // 3. Validate
                    //--------------------------------------
                    // Check against Tool to Intent translation
                    val agent = context.getBean(PromptGenerationAgent::class.java)
                    logger.debug("Agent:{}", agent)

                    with(agent) {
                        shouldNotBeNull()
                    }

                    val result = agent.execute(userQuestion)
                    logger.debug("result:{}", result)
                    with(result) {
                        shouldNotBeNull()
                    }
                }
            }
    }

    private val logger = LoggerFactory.getLogger(this::class.java)
}


@Configuration
@ComponentScan(basePackageClasses = [PromptGenerationAgent::class])
class SampleToolConfig {
    @Bean
    fun chat(): Chat = ChatApiConfigs().chatOllama(
        model = "llama3",
    )
}