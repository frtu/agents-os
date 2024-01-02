package com.github.frtu.ai.os.tool.agent

import com.github.frtu.ai.agents.Agent
import com.github.frtu.ai.agents.core.functioncall.JsonFormatAgent
import com.github.frtu.ai.os.llm.Chat
import com.github.frtu.ai.os.llm.MessageBuilder.user
import com.github.frtu.ai.os.memory.Conversation
import java.lang.reflect.InvocationHandler
import java.lang.reflect.InvocationTargetException
import java.lang.reflect.Method
import java.lang.reflect.Proxy
import kotlin.coroutines.Continuation
import kotlin.coroutines.CoroutineContext
import kotlin.coroutines.resumeWithException
import kotlin.reflect.jvm.kotlinFunction
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.runBlocking

class AgentBuilder(
    val chat: Chat,
) {
    /**
     * Creates an instance of [T] that utilizes our custom [InvocationHandler]
     */
    inline fun <reified T : Agent> createProxy(): T {
        val service = T::class.java
        val invocationHandler = object : InvocationHandler {
            val conversation = Conversation()

            override fun invoke(proxy: Any, method: Method, args: Array<out Any>?): Any {
                val nonNullArgs = args ?: arrayOf()

                // Create a systemDirective based on the current function called
                val systemDirective = AgentCallGenerator.generateSystemPrompt(
                    // Kotlin function
                    method.kotlinFunction!!,
                    // Declaring class that must extend Agent
                    (method.declaringClass as Class<Agent>).kotlin,
                )
                // Retrieve the first parameter and transform to user message
                val message = user(nonNullArgs[0].toString())

                // Invoke Chat with the ongoing conversation
                val result = try {
                    with(conversation) {
                        system(systemDirective)
                        runBlocking {
                            return@runBlocking chat.sendMessage(append(message)).content
                        }
                    } ?: throw IllegalStateException("Error")
                } catch(e: InvocationTargetException) {
                    throw e.targetException
                }
                return result
            }
        }
        return Proxy.newProxyInstance(
            service.classLoader,
            arrayOf(service),
            invocationHandler,
        ) as T
    }
}