package com.github.frtu.ai.os.service.prompt.config

import com.github.frtu.ai.os.service.prompt.config.PromptGenerationConfig.Companion.PROMPT_GENERATION_TEMPLATE
import com.github.frtu.kotlin.ai.os.llm.Chat
import com.github.frtu.kotlin.ai.os.llm.agent.UnstructuredBaseAgent
import com.github.frtu.kotlin.ai.spring.builder.ChatApiConfigs
import io.kotest.matchers.nulls.shouldNotBeNull
import io.kotest.matchers.shouldBe
import kotlinx.coroutines.runBlocking
import org.junit.jupiter.api.Test
import org.slf4j.LoggerFactory
import org.springframework.boot.test.context.runner.ApplicationContextRunner
import org.springframework.context.annotation.Bean
import org.springframework.context.annotation.Configuration

class PromptGenerationConfigTest {
    private val applicationContextRunner = ApplicationContextRunner()

    @Test
    fun promptGenerationAgent() {
        //--------------------------------------
        // 1. Init
        //--------------------------------------
        // Init var
        applicationContextRunner
            //--------------------------------------
            // 2. Execute
            //--------------------------------------
            .withUserConfiguration(
                PromptGenerationConfig::class.java,
                SampleConfig::class.java,
            )
            .run { context ->
                runBlocking {
                    //--------------------------------------
                    // 3. Validate
                    //--------------------------------------
                    // Check Agent against PromptTemplate
                    val agent = context.getBean(UnstructuredBaseAgent::class.java)
                    logger.debug("result:{}", agent)
                    with(agent) {
                        shouldNotBeNull()
                        id.value shouldBe PROMPT_GENERATION_TEMPLATE.id
                        description shouldBe PROMPT_GENERATION_TEMPLATE.description
                        instructions shouldBe PROMPT_GENERATION_TEMPLATE.template
                    }
                }
            }
    }

    private val logger = LoggerFactory.getLogger(this::class.java)
}


@Configuration
class SampleConfig {
    @Bean
    fun chat(): Chat = ChatApiConfigs().chatOllama(
        model = "llama3",
    )
}