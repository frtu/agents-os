package com.github.frtu.ai.agents.annotation

/**
 * Annotation for a Role prompt an Agent needs to impersonate.
 */
annotation class Role(
    val name: String,
    val prompt: String,
)
