package com.github.frtu.ai.agents.os.app

data class WeatherInfoMultiple(
    val location: String,
    val unit: Unit,
    val numberOfDays: Int,
    val temperature: String,
    val forecast: List<String>,
) {
    constructor(
        location: String,
        unit: String,
        numberOfDays: Int,
        temperature: String,
        forecast: List<String>,
    ) : this(location, Unit.valueOf(unit), numberOfDays, temperature, forecast)
}
