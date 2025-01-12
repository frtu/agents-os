package com.github.frtu.ai.os.service.prompt.agent

import com.github.frtu.kotlin.ai.os.llm.Chat
import com.github.frtu.kotlin.ai.os.llm.agent.StructuredBaseAgent
import com.github.frtu.kotlin.ai.os.llm.agent.UnstructuredBaseAgent
import org.springframework.beans.factory.annotation.Qualifier
import org.springframework.stereotype.Component

@Component(PromptGenerationAgent.TOOL_NAME)
@Qualifier(PromptGenerationAgent.TOOL_NAME)
class PromptGenerationAgent(
    // Chat engine
    chat: Chat,
) : UnstructuredBaseAgent(
    id = TOOL_NAME,
    description = "A meta-prompt Agent instructs the model to create a good prompt based on your task description or improve an existing one",
    instructions = """
You re a prompt engineer, write a very bespoke, detailed and succinct prompt, that will generate an Cartoon storyboard writer optimized to write a story for my 2 pages cartoon content called UFO of a cute space cat and a police dog chasing him.

Instructions
- output the prompt you generate in markdown using variables in double curly brackets
- output the prompt in a codeblock
    """.trimIndent(),
    chat = chat,
) {
    companion object {
        const val TOOL_NAME = "prompt-generation-agent"
    }
}
