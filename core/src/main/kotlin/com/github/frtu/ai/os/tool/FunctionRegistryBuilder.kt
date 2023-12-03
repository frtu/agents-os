package com.github.frtu.ai.os.tool

import com.github.frtu.ai.os.BuilderMarker
import kotlin.reflect.KFunction2

class FunctionRegistryBuilder(
    private val functionRegistry: FunctionRegistry = FunctionRegistry()
) {
    fun function(
        name: String,
        description: String,
        kFunction2: KFunction2<String, String, String>,
        parameterClass: Class<*>,
    ) = functionRegistry.registerFunction(
        name = name,
        description = description,
        kFunction2 = kFunction2,
        parameterClass = parameterClass,
    )

    fun function(
        name: String,
        description: String,
        kFunction2: KFunction2<String, String, String>,
        jsonSchema: String,
    ) = functionRegistry.registerFunction(
        name = name,
        description = description,
        kFunction2 = kFunction2,
        jsonSchema = jsonSchema,
    )

    fun build(): FunctionRegistry = functionRegistry
}


@BuilderMarker
fun registry(actions: FunctionRegistryBuilder.() -> Unit): FunctionRegistry =
    FunctionRegistryBuilder().apply(actions).build()