package com.github.frtu.ai.os.service

import com.github.frtu.ai.os.service.intent.config.IntentClassifierConfig
import com.github.frtu.kotlin.ai.os.llm.agent.AgentExecuter
import com.github.frtu.kotlin.spring.tool.config.SpringToolAutoConfigs
import org.slf4j.LoggerFactory
import org.springframework.boot.CommandLineRunner
import org.springframework.boot.autoconfigure.SpringBootApplication
import org.springframework.boot.runApplication
import org.springframework.context.annotation.Bean
import org.springframework.context.annotation.Import

@SpringBootApplication
@Import(
    IntentClassifierConfig::class,
    SpringToolAutoConfigs::class,
)
class AssistantApplication {
    @Bean
    fun startup(registry: List<AgentExecuter>,): CommandLineRunner = CommandLineRunner {
        registry.map {
            logger.info("Detected agent spring bean:${it.id}")
        }
    }

    private val logger = LoggerFactory.getLogger(this::class.java)
}

fun main(args: Array<String>) {
    runApplication<AssistantApplication>(*args)
}
