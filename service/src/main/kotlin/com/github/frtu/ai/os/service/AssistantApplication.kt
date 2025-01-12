package com.github.frtu.ai.os.service

import com.github.frtu.ai.os.service.intent.config.IntentClassifierConfig
import com.github.frtu.kotlin.spring.tool.config.SpringToolAutoConfigs
import org.springframework.boot.autoconfigure.SpringBootApplication
import org.springframework.boot.runApplication
import org.springframework.context.annotation.Import

@SpringBootApplication
@Import(
    IntentClassifierConfig::class,
    SpringToolAutoConfigs::class,
)
class AssistantApplication

fun main(args: Array<String>) {
    runApplication<AssistantApplication>(*args)
}
