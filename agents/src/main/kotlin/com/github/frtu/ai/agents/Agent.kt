package com.github.frtu.ai.agents

import com.github.frtu.ai.agents.annotation.Persona
import kotlin.reflect.KClass
import kotlin.reflect.full.findAnnotations

@Persona(
    """
    You are a helpful agent
"""
)
open class Agent

fun KClass<out Agent>.getPersona(): String {
    val findAnnotations = this.findAnnotations<Persona>()
    findAnnotations.ifEmpty { throw IllegalArgumentException("You must annotate your agent class:[${this}] with @Persona(prompt)") }
    return findAnnotations.first().prompt.trim()
}
