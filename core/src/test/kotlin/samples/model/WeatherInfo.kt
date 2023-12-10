package samples.model

import com.fasterxml.jackson.annotation.JsonPropertyDescription
import com.fasterxml.jackson.annotation.JsonValue
import com.kjetland.jackson.jsonSchema.annotations.JsonSchemaDescription

@JsonSchemaDescription("Weather Info object")
data class WeatherInfo(
    @JsonPropertyDescription("Location for weather")
    val location: String,

    @JsonPropertyDescription("Unit (celsius or fahrenheit)")
    val unit: Unit,

    @JsonPropertyDescription("Temperature")
    val temperature: String,

    @JsonPropertyDescription("Future temperature")
    val forecast: List<String>,
) {
    constructor(
        location: String,
        unit: String,
        temperature: String,
        forecast: List<String>,
    ) : this(location, unit.toUnit(), temperature, forecast)
}

enum class Unit(val value : String) {
    Celsius("celsius"),
    Fahrenheit("fahrenheit"),;

    @JsonValue
    override fun toString(): String {
        return value
    }
}

fun String.toUnit(): Unit = try {
    Unit.valueOf(this)
} catch (e:  Exception) {
    println("Cannot convert $this, Error:${e.message}")
    throw e
}
