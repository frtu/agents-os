# Development env

## Guide for `text-generation-webui`

### Select the most suitable model

Check [HuggingFace leaderboard](https://huggingface.co/spaces/bigcode/bigcode-models-leaderboard) to balance between :

* Purpose you want to achieve (Coding, Generate a story, ..)
* Number of RAM on your machine

You can download the most optimized version by looking from [TheBloke](https://huggingface.co/TheBloke/) &
recommend `Q4_K_M.gguf` for normal laptop.

### First setup and test

#### Using Ollama

[Setup API service](https://github.com/ollama/ollama/blob/main/docs/faq.md#how-do-i-configure-ollama-server) (by
using `launchctl setenv` on MacOS) :

=> Test using API at [http://localhost:11434/](http://localhost:11434/).

```bash
curl http://localhost:11434/v1/chat/completions \
    -H "Content-Type: application/json" \
    -d '{
        "model": "llama2",
        "messages": [
            {
                "role": "system",
                "content": "You are a helpful assistant."
            },
            {
                "role": "user",
                "content": "Hello!"
            }
        ]
    }'
```

See https://ollama.com/blog/openai-compatibility

#### Using Oobabooga

Setup [oobabooga/text-generation-webui](https://github.com/oobabooga/text-generation-webui) by running auto installer `start_xx` on your machine (ex: `. start_macos.sh` on MacOS).

=> Test using UI at [http://127.0.0.1:7860/](http://127.0.0.1:7860/).

If UI is loading :

* Go to `Model` tab
* Make sure to `Download model`
* Select your `Model` in drop down (ex: `mistral-7b-instruct-v0.1.Q4_K_M.gguf`) 
* Configure `n-gpu-layers` to `1` (for performance)
* `Load` it !

##### Start OpenAI compatible endpoint

`oobabooga/text-generation-webui` provide an [enpoint that is compatible with OpenAI](https://github.com/oobabooga/text-generation-webui/wiki/12-%E2%80%90-OpenAI-API)

Configure it using :

* In `CMD_FLAGS.txt` configure `--listen --api` & maybe  `--api-port [port]` if you want to change from default `5000`.
* Test it using [endpoint & payload](https://github.com/oobabooga/text-generation-webui/wiki/12-%E2%80%90-OpenAI-API#examples) at `http://127.0.0.1:5000/v1/chat/completions` 

### Use API

https://cheatsheet.md/llm-leaderboard/mistral-7b.en

```python
import openai

openai.api_base = "http://127.0.0.1:5000/v1" 
openai.api_key = "none"

messages = [{"role": "user", "content": "What is the bash command to list all files in a folder and sort them by last modification?"}]

chat_completion = openai.ChatCompletion.create(
  model="mistral-7b-instruct-v0.1.Q4_K_M.gguf", 
  temperature=1,
  max_tokens=1024,
  messages=messages
)

print(chat_completion.to_dict_recursive())
```

## Troubleshooting

### Cannot recognize `openai` module

Don't forget to run `pip install -r extensions/openai/requirements.txt`

### 500 Server error

* Check the server log 
* If you get this error :
```
    raise ValueError('No tokenizer is loaded')
ValueError: No tokenizer is loaded
```

Please don't forget to [load a Model](#First setup and test).
