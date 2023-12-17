package com.github.frtu.ai.agents.travel.model

import com.fasterxml.jackson.annotation.JsonPropertyDescription
import com.fasterxml.jackson.databind.PropertyNamingStrategies
import com.fasterxml.jackson.databind.annotation.JsonNaming
import com.kjetland.jackson.jsonSchema.annotations.JsonSchemaDescription

@JsonSchemaDescription("Trip review object")
@JsonNaming(PropertyNamingStrategies.SnakeCaseStrategy::class)
data class TripRevision(
    @JsonPropertyDescription("This field is 'true' if the plan is feasible, 'false' otherwise")
    val isPlanValid: Boolean,

    @JsonPropertyDescription("Your update to the plan")
    val updatedRequest: String,
)
