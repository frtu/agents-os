package com.github.frtu.ai.agents.annotation

/**
 * Annotation for a Role prompt an Agent needs to impersonate.
 *
 * Common usage is `Act as a [Role]`
 */
annotation class Role(
    val name: String,
    val prompt: String,
)
