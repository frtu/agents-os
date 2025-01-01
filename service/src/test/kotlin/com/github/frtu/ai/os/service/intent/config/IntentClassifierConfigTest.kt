package com.github.frtu.ai.os.service.intent.config

import com.github.frtu.ai.os.service.intent.agent.IntentClassifierAgent
import com.github.frtu.ai.os.service.intent.agent.IntentClassifierAgentTest
import com.github.frtu.kotlin.ai.os.llm.Chat
import com.github.frtu.kotlin.ai.spring.builder.ChatApiConfigs
import com.github.frtu.kotlin.tool.Tool
import com.github.frtu.kotlin.tool.ToolRegistry
import io.kotest.matchers.nulls.shouldNotBeNull
import io.kotest.matchers.shouldBe
import io.kotest.matchers.string.shouldNotBeEmpty
import kotlinx.coroutines.runBlocking
import org.junit.jupiter.api.Test
import org.slf4j.LoggerFactory
import org.springframework.boot.test.context.runner.ApplicationContextRunner
import org.springframework.context.annotation.Bean
import org.springframework.context.annotation.ComponentScan
import org.springframework.context.annotation.Configuration
import sample.tool.CurrentWeatherTool
import sample.tool.IdentityTool
import sample.tool.function.CurrentWeatherFunction
import sample.tool.function.WeatherForecastFunction
import sample.tool.model.WeatherForecastInputParameter

class IntentClassifierConfigTest {
    private val applicationContextRunner = ApplicationContextRunner()

    @Test
    fun intentClassifierAgent() {
        //--------------------------------------
        // 1. Init
        //--------------------------------------
        // Init var
        val userQuestion = "What is the weather tomorrow?"
        val intentId = WeatherForecastFunction.TOOL_NAME

        applicationContextRunner
            //--------------------------------------
            // 2. Execute
            //--------------------------------------
            .withUserConfiguration(
                IntentClassifierConfig::class.java,
                SampleToolConfig::class.java
            )
            .run { context ->
                runBlocking {
                    //--------------------------------------
                    // 3. Validate
                    //--------------------------------------
                    // Check precondition (ToolRegistry should be initialised correctly)
                    val toolRegistry = context.getBean(ToolRegistry::class.java)
                    toolRegistry[IdentityTool.TOOL_NAME].shouldNotBeNull()
                    // Each Tool should match an Intent except for the current agent
                    val numberOfToolWithoutCurrentAgent = toolRegistry.getAll().size - 1

                    // Check against Tool to Intent translation
                    val agent = context.getBean(IntentClassifierAgent::class.java)
                    logger.debug("result:{}", agent.intents)

                    with(agent.intents) {
                        shouldNotBeNull()
                        // Contains all Intent + Default one
                        size - 1 shouldBe numberOfToolWithoutCurrentAgent
                    }

                    val result = agent.execute(userQuestion)
                    logger.debug("Intent:{}", result)
                    with(result) {
                        shouldNotBeNull()
                        intent shouldBe intentId
                        reasoning.shouldNotBeEmpty()
                    }
                }
            }
    }

    private val logger = LoggerFactory.getLogger(this::class.java)
}


@Configuration
@ComponentScan(basePackageClasses = [ToolRegistry::class])
class SampleToolConfig {
    @Bean
    fun chat(): Chat = ChatApiConfigs().chatOllama(
        model = "llama3",
    )

    @Bean(IdentityTool.TOOL_NAME)
    fun identity(): Tool = IdentityTool()

    @Bean(WeatherForecastFunction.TOOL_NAME)
    fun weatherForecastFunction(): Tool = WeatherForecastFunction()
}