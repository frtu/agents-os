package com.github.frtu.ai.agents.travel.model

import com.fasterxml.jackson.annotation.JsonPropertyDescription
import com.fasterxml.jackson.databind.PropertyNamingStrategies
import com.fasterxml.jackson.databind.annotation.JsonNaming
import com.kjetland.jackson.jsonSchema.annotations.JsonSchemaDescription

@JsonSchemaDescription("Trip object")
@JsonNaming(PropertyNamingStrategies.SnakeCaseStrategy::class)
data class TripPlan(
    @JsonPropertyDescription("Start location of trip")
    val start: String,

    @JsonPropertyDescription("End location of trip")
    val end: String,

    @JsonPropertyDescription("List of waypoints")
    val waypoints: List<String>,

    @JsonPropertyDescription("Mode of transportation")
    val transit: String,
)
