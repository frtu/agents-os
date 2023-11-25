package com.github.frtu.ai.agents.os.app

data class WeatherInfo(
    val location: String,
    val unit: Unit,
    val temperature: String,
    val forecast: List<String>,
) {
    constructor(
        location: String,
        unit: String,
        temperature: String,
        forecast: List<String>,
    ) : this(location, Unit.valueOf(unit), temperature, forecast)
}

enum class Unit {
    celsius,
    fahrenheit,
}
