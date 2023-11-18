package com.github.frtu.ai.os.model

/**
 * Message class is a base unit from a Thread
 * @author frtu
 */
data class Message(
    val role: Role,
    val content: String,
)