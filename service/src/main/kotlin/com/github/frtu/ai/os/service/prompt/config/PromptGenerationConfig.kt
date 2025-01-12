package com.github.frtu.ai.os.service.prompt.config

import com.github.frtu.kotlin.ai.os.instruction.PromptTemplate
import com.github.frtu.kotlin.ai.os.llm.Chat
import com.github.frtu.kotlin.ai.os.llm.agent.UnstructuredBaseAgent
import org.slf4j.LoggerFactory
import org.springframework.beans.factory.annotation.Qualifier
import org.springframework.context.annotation.Bean
import org.springframework.context.annotation.Configuration

@Configuration
class PromptGenerationConfig {
    @Bean(TOOL_NAME)
    @Qualifier(TOOL_NAME)
    fun promptGenerationAgent(chat: Chat): UnstructuredBaseAgent {
        return UnstructuredBaseAgent.create(chat, PROMPT_GENERATION_TEMPLATE).also { agent ->
            logger.info("Created new agent id:{} from prompt:{}", agent.id, agent.instructions)
        }
    }

    companion object {
        const val TOOL_NAME = "prompt-generation-agent"

        val PROMPT_GENERATION_TEMPLATE = PromptTemplate(
            id = TOOL_NAME,
            description = "A meta-prompt Agent instructs the model to create a good prompt based on your task description or improve an existing one",
            template = """
                You're a prompt engineer, write a very bespoke, detailed and succinct prompt, that will generate an Cartoon storyboard writer optimized to write a story for my 2 pages cartoon content called UFO of a cute space cat and a police dog chasing him.
                
                Instructions
                - output the prompt you generate in markdown using variables in double curly brackets
                - output the prompt in a codeblock
                """.trimIndent(),
        )
    }

    private val logger = LoggerFactory.getLogger(this::class.java)
}