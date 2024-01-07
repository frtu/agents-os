package com.github.frtu.ai.agents.travel

import com.github.frtu.ai.agents.annotation.Task
import com.github.frtu.ai.agents.Agent
import com.github.frtu.ai.agents.annotation.Role
import com.github.frtu.ai.agents.travel.model.TripRevision
import com.github.frtu.ai.agents.travel.model.TripPlan

@Role(
    name = "Validation agent",
    prompt = """
    You are a travel agent who helps users make exciting travel plans.
    """
)
interface ValidationAgent : Agent {
    @Task(
        prompt = """
        The user's request will be denoted by four hashtags. Determine if the user's
        request is reasonable and achievable within the constraints they set.
        
        A valid request should contain the following:
        - A start and end location
        - A trip duration that is reasonable given the start and end location
        - Some other details, like the user's interests and/or preferred mode of transport
        
        Any request that contains potentially harmful activities is not valid, regardless of what
        other details are provided.
        
        If the request is not valid, set
        plan_is_valid = false and use your travel expertise to update the request to make it valid,
        keeping your revised request shorter than 100 words.
        
        If the request seems reasonable, then set plan_is_valid = true and
        don't revise the request.
        """
    )
    fun validate(tripPlan: TripPlan): TripRevision

    @Task(
        """
        The user's request will be denoted by four hashtags. Convert the
        user's request into a detailed itinerary describing the places
        they should visit and the things they should do.
        
        Try to include the specific address of each location.
        
        Remember to take the user's preferences and timeframe into account,
        and give them an itinerary that would be fun and realistic given their constraints.
        
        Try to make sure the user doesn't need to travel for more than 8 hours on any one day during
        their trip.
        
        Return the itinerary as a bulleted list with clear start and end locations and mention the type of transit for the trip.
        
        If specific start and end locations are not given, choose ones that you think are suitable and give specific addresses.
        
        Your output must be the list and nothing else.
    """
    )
    fun proposeItinerary()
}