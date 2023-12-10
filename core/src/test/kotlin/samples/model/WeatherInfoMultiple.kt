package samples.model

import com.fasterxml.jackson.annotation.JsonPropertyDescription
import com.kjetland.jackson.jsonSchema.annotations.JsonSchemaDescription

@JsonSchemaDescription("Current and future Weather Info")
data class WeatherInfoMultiple(
    @JsonPropertyDescription("Unit (celsius or fahrenheit)")
    val unit: Unit,

    @JsonPropertyDescription("Current temperature")
    val temperature: String,

    @JsonPropertyDescription("Number of Days to forecast")
    val numberOfDays: Int,

    @JsonPropertyDescription("Future days forecast")
    val forecast: List<WeatherInfo>,
) {
    constructor(
        unit: String,
        temperature: String,
        numberOfDays: Int,
        forecast: List<WeatherInfo>,
    ) : this(Unit.valueOf(unit), temperature, numberOfDays, forecast)
}
