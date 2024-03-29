package com.github.frtu.ai.agents.travel

import com.github.frtu.ai.agents.Agent
import com.github.frtu.ai.agents.annotation.Role

@Role(
    name = "Travel agent",
    description = "Agent giving advice on travel",
    prompt = """
    You are a travel agent who helps users make exciting travel plans.
    """
)
interface TravelAgent : Agent