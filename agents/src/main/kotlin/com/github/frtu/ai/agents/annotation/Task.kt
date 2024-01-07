package com.github.frtu.ai.agents.annotation

/**
 * Annotation for an action an Agent can execute.
 *
 * It tags one `Task a role need to perform`
 */
annotation class Task(
    val prompt: String,
    val format: Format = Format.TEXT,
)
