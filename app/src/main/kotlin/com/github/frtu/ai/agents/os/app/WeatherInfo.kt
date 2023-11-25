package com.github.frtu.ai.agents.os.app

data class WeatherInfo(
    val location: String,
    val temperature: String,
    val unit: Unit,
    val forecast: List<String>,
) {
    constructor(
        location: String,
        temperature: String,
        unit: String,
        forecast: List<String>,
    ) : this(location, temperature, Unit.valueOf(unit), forecast)
}

enum class Unit {
    celsius,
    fahrenheit,
}
