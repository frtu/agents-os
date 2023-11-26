package samples.service

import com.fasterxml.jackson.module.kotlin.jacksonObjectMapper
import samples.model.WeatherInfo

object WeatherService

fun currentWeather(location: String, unit: String): String {
    val weatherInfo = WeatherInfo(location, unit, "72", listOf("sunny", "windy"))
    return jacksonObjectMapper().writeValueAsString(weatherInfo)
}