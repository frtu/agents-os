package com.github.frtu.ai.os.service

import com.github.frtu.ai.os.service.intent.config.IntentClassifierConfig
import com.github.frtu.kotlin.ai.spring.config.LlmOsAutoConfigs
import com.github.frtu.kotlin.spring.slack.config.SlackAutoConfigs
import com.github.frtu.kotlin.spring.tool.config.SpringToolAutoConfigs
import org.springframework.boot.autoconfigure.SpringBootApplication
import org.springframework.boot.runApplication
import org.springframework.context.annotation.Import
import sample.tool.SampleToolConfig

@SpringBootApplication
@Import(
    IntentClassifierConfig::class,
    SpringToolAutoConfigs::class,
    SampleToolConfig::class,
)
class AssistantApplication

fun main(args: Array<String>) {
    runApplication<AssistantApplication>(*args)
}
