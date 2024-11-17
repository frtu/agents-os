package com.github.frtu.ai.os.service.config

import com.github.frtu.kotlin.ai.os.llm.openai.OpenAiCompatibleChat.Companion.LOCAL_MODEL
import com.github.frtu.kotlin.ai.os.llm.openai.OpenAiCompatibleChat.Companion.LOCAL_URL
import com.github.frtu.kotlin.ai.spring.config.ChatApiProperties
import org.springframework.boot.context.properties.ConstructorBinding

@ConstructorBinding
class ChatApiPropertiesSpringBoot2(
    apiKey: String? = null,
    model: String = LOCAL_MODEL, // "mistral"
    baseUrl: String = LOCAL_URL, // "http://localhost:11434/v1/"
) : ChatApiProperties(
    apiKey,
    model,
    baseUrl,
)
