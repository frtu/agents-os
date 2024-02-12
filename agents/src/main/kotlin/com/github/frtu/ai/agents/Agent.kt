package com.github.frtu.ai.agents

import com.github.frtu.ai.agents.annotation.Task
import com.github.frtu.ai.agents.annotation.Role
import kotlin.reflect.KClass
import kotlin.reflect.KFunction
import kotlin.reflect.full.findAnnotations

@Role(
    name = "Generic agent",
    prompt = """
    You are a helpful assistant
    """
)
open interface Agent

fun Agent.getRole(): Role = this::class.getRole()

fun KClass<out Agent>.getRole(): Role {
    val findAnnotations = this.findAnnotations<Role>()
    findAnnotations.ifEmpty { throw IllegalArgumentException("You must annotate your agent class:[${this}] with @Persona(prompt)") }
    return findAnnotations.first()
}

fun KClass<out Agent>.getRolePrompt(): String = this.getRole().prompt.trimIndent().trim()

fun KFunction<*>.getTask(): Task {
    val findAnnotations = this.findAnnotations<Task>()
    findAnnotations.ifEmpty { throw IllegalArgumentException("You must annotate your function:[${this}] with @Action(prompt)") }
    return findAnnotations.first()
}

fun KFunction<*>.getTaskPrompt(): String = this.getTask().prompt.trimIndent().trim()
