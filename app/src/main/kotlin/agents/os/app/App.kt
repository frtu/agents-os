package agents.os.app

import com.aallam.openai.api.chat.ChatCompletion
import com.aallam.openai.api.chat.ChatCompletionChunk
import com.aallam.openai.api.chat.ChatCompletionRequest
import com.aallam.openai.api.chat.ChatMessage
import com.aallam.openai.api.chat.ChatRole
import com.aallam.openai.api.http.Timeout
import com.aallam.openai.api.model.ModelId
import com.aallam.openai.client.OpenAI
import com.aallam.openai.client.OpenAIConfig
import kotlin.time.Duration.Companion.seconds
import kotlinx.coroutines.flow.Flow

suspend fun main() {
    val apiKey = "sk-xxxxx"
    val config = OpenAIConfig(
        token = apiKey,
        timeout = Timeout(socket = 60.seconds),
    )

    val openAI = OpenAI(config)

    val chatCompletionRequest = ChatCompletionRequest(
        model = ModelId("gpt-3.5-turbo"),
        messages = listOf(
            ChatMessage(
                role = ChatRole.System,
                content = "You are a helpful assistant!"
            ),
            ChatMessage(
                role = ChatRole.User,
                content = "Hello!"
            )
        )
    )
    val completion: ChatCompletion = openAI.chatCompletion(chatCompletionRequest)
    println(completion.choices)
//// or, as flow
//    val completions: Flow<ChatCompletionChunk> = openAI.chatCompletions(chatCompletionRequest)
//    completions.collect {
//        println(it.choices)
//    }
}
