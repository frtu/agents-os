package com.github.frtu.ai.os.service.agent

import com.github.frtu.kotlin.ai.os.llm.Chat
import com.github.frtu.kotlin.ai.os.llm.agent.UnstructuredBaseAgent
import com.github.frtu.kotlin.tool.ToolRegistry

class SummarizerAgent(
    // Chat engine
    chat: Chat,
    // For execution
    toolRegistry: ToolRegistry? = null,
) : UnstructuredBaseAgent(
    id = "summarizer-agent",
    description = "Agent summarising content",
    instructions = "Don't make assumptions about what values to plug into functions. Ask for clarification if a user request is ambiguous.",
    chat = chat,
    toolRegistry = toolRegistry,
    isStateful = true,
)
