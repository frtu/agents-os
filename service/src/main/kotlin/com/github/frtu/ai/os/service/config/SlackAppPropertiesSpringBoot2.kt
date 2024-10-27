package com.github.frtu.ai.os.service.config

import com.github.frtu.kotlin.spring.slack.config.SlackAppProperties
import org.springframework.boot.context.properties.ConstructorBinding

@ConstructorBinding
class SlackAppPropertiesSpringBoot2(
    token: String,
    signingSecret: String,
    botOauthToken: String,
) : SlackAppProperties(
    token,
    signingSecret,
    botOauthToken,
)