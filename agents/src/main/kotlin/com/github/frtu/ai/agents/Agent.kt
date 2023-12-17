package com.github.frtu.ai.agents

import com.github.frtu.ai.agents.annotation.Action
import com.github.frtu.ai.agents.annotation.Persona
import kotlin.reflect.KClass
import kotlin.reflect.KFunction
import kotlin.reflect.full.findAnnotations

@Persona(
    name = "Generic agent",
    prompt = """
    You are a helpful assistant
    """
)
open class Agent

fun KClass<out Agent>.getPersona(): String {
    val findAnnotations = this.findAnnotations<Persona>()
    findAnnotations.ifEmpty { throw IllegalArgumentException("You must annotate your agent class:[${this}] with @Persona(prompt)") }
    return findAnnotations.first().prompt.trimIndent().trim()
}

fun KFunction<*>.getAction(): String {
    val findAnnotations = this.findAnnotations<Action>()
    findAnnotations.ifEmpty { throw IllegalArgumentException("You must annotate your function:[${this}] with @Action(prompt)") }
    return findAnnotations.first().prompt.trimIndent().trim()
}
