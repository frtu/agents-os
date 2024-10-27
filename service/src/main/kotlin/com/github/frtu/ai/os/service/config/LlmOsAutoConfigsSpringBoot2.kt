package com.github.frtu.ai.os.service.config

import com.github.frtu.kotlin.llm.spring.builder.ChatApiConfigs
import org.springframework.boot.context.properties.EnableConfigurationProperties
import org.springframework.context.annotation.ComponentScan
import org.springframework.context.annotation.Configuration
import org.springframework.context.annotation.Import

/**
 * Allow to bootstrap AI OS configuration
 */
@Configuration
@Import(
    ChatApiConfigs::class,
)
@EnableConfigurationProperties(ChatApiPropertiesSpringBoot2::class)
@ComponentScan("com.github.frtu.kotlin.llm.os")
class LlmOsAutoConfigsSpringBoot2