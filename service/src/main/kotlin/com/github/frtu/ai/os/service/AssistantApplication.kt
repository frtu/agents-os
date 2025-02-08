package com.github.frtu.ai.os.service

import com.github.frtu.ai.os.service.intent.config.IntentClassifierConfig
import com.github.frtu.kotlin.ai.os.llm.agent.AgentExecuter
import com.github.frtu.kotlin.spring.tool.config.SpringToolAutoConfigs
import org.slf4j.LoggerFactory
import org.springframework.boot.CommandLineRunner
import org.springframework.boot.WebApplicationType
import org.springframework.boot.autoconfigure.SpringBootApplication
import org.springframework.boot.builder.SpringApplicationBuilder
import org.springframework.context.annotation.Bean
import org.springframework.context.annotation.Import
import sample.tool.SampleToolConfig

@SpringBootApplication
@Import(
    SampleToolConfig::class,
    IntentClassifierConfig::class,
    SpringToolAutoConfigs::class,
)
class AssistantApplication {
    @Bean
    fun startup(
        registryAgents: List<AgentExecuter>,
    ): CommandLineRunner = CommandLineRunner {
        registryAgents.map {
            logger.info("Detected agent spring bean:${it.id}")
        }
    }

    private val logger = LoggerFactory.getLogger(this::class.java)
}

fun main(args: Array<String>) {
    try {
        SpringApplicationBuilder(AssistantApplication::class.java)
            .web(WebApplicationType.REACTIVE)
            .run(*args)
    } catch (e: Exception) {
        e.printStackTrace()
    }
}
