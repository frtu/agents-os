package com.github.frtu.ai.os.utils

import kotlinx.serialization.json.JsonArray
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive

object JsonExtensions

fun JsonArray?.getJsonObject(index: Int): JsonObject? =
    this?.let { this[index].jsonObject }

fun JsonObject?.getString(key: String): String? =
    this?.let { getValue(key).jsonPrimitive.content }

fun JsonObject?.getInt(key: String): Int? =
    this?.getString(key)?.toInt()
