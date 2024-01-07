package com.github.frtu.ai.agents.core.functioncall

import com.github.frtu.ai.agents.annotation.Task
import com.github.frtu.ai.agents.Agent
import com.github.frtu.ai.agents.annotation.Role

@Role(
    name = "Json Formatter Agent",
    prompt = """
    You are a JSON generator, you only reply in JSON format.
    """
)
interface JsonFormatAgent : Agent {
    @Task(
        prompt = """
        The only JSON you can generate has this schema:
        { "${'$'}schema": "http://json-schema.org/draft-04/schema#", "type": "array", "items": { "${'$'}ref": "#/definitions/Anonymous" }, 
        "definitions": { "Parameter": { "type": "object", "properties": { "Name": { "type": "string" }, "Value": { "type": "string" } } }, 
        "Anonymous": { "type": "object", "properties": { "FunctionName": { "type": "string" }, 
        "Parameters": { "type": "array", "items": { "${'$'}ref": "#/definitions/Parameter" } } } } } }
        
        For example, the input might look like this: 'GetHotel(nights: 5, rooms: 2)', and you create this JSON from it:
        [{"FunctionName":"GetHotel","Parameters":[{"Name":"nights","Value":"5"},{"Name":"rooms","Value":"2"}]}].
        
        There might be multiple input Functions, or just one. Put them in an array, like the example. Input: Start(understood: true)
        """
    )
    fun convertTextToJson(text: String): String
}