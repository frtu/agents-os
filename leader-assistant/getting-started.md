# Getting Started

Leader Assistant is an IM-style assistant that retrieves knowledge from project
documentation and answers questions using Claude. It serves both a **Gradio web
UI** and a **REST API** on the same port.

## 1. Prerequisites

- Python **3.13+**
- [uv](https://docs.astral.sh/uv/) for dependency management
- An Anthropic API key

## 2. Install

```bash
# From the leader-assistant/ directory
uv sync
```

## 3. Configure

Set your Claude API key:

```bash
export ANTHROPIC_API_KEY=your_key_here
```

## 4. Run

```bash
# Start the server (UI + REST API)
uv run python app.py

# With debug logging (SDK events, requests, responses)
uv run python app.py --debug

# On a custom host/port
uv run python app.py --host 127.0.0.1 --port 8080
```

Once running:

- **Web UI:** http://localhost:7860/
- **REST API:** http://localhost:7860/api/...
- **Interactive API docs (Swagger):** http://localhost:7860/docs

### Command-line options

| Option | Description | Default |
|--------|-------------|---------|
| `--debug` | Enable debug logging | off |
| `--host HOST` | Server host | `0.0.0.0` |
| `--port PORT` | Server port | `7860` |

## 5. Install skills (optional)

Skills extend what the agent can do. They are loaded into the agent's context,
so any installed skill is available to both the UI and the REST API.

```bash
# List skills available from the shared ../skills library
python3 skill_manager.py list

# Install one (symlink by default)
python3 skill_manager.py install <skill-name>

# See what's installed
python3 skill_manager.py installed
```

## REST API

The Gradio UI is mounted onto a FastAPI app, so the UI and REST API share one
server. Use the REST API to trigger the agent (and its installed skills)
programmatically.

| Method | Path | Description |
|--------|------|-------------|
| `GET`  | `/api/health` | Health check. Returns `{"status": "ok"}`. |
| `GET`  | `/api/skills` | List available and installed skills. |
| `POST` | `/api/agent` | Trigger the agent, return the full reply as JSON. |
| `POST` | `/api/agent/stream` | Trigger the agent, stream the reply via Server-Sent Events. |

### Request body

`/api/agent` and `/api/agent/stream` accept the same JSON body:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `message` | string | yes | The prompt/question for the agent. |
| `session_id` | string | no | A session ID returned by a previous call, to continue the conversation. |

```json
{ "message": "your question", "session_id": "optional-session-to-resume" }
```

### Responses

- `/api/agent` returns JSON: `{ "reply": "...", "session_id": "..." }`
- `/api/agent/stream` returns a `text/event-stream` of SSE messages. Each event
  carries the accumulated reply so far; the final event includes `"done": true`:

  ```text
  data: {"reply": "No", "session_id": "abc-123"}

  data: {"reply": "No skills installed.", "session_id": "abc-123"}

  data: {"reply": "No skills installed.", "session_id": "abc-123", "done": true}
  ```

## Examples

### Health check

```bash
curl http://localhost:7860/api/health
# {"status":"ok"}
```

### List skills

```bash
curl http://localhost:7860/api/skills
# {"available":[{"name":"...","description":"..."}],"installed":["..."]}
```

### Trigger the agent (JSON reply)

```bash
curl -X POST http://localhost:7860/api/agent \
  -H 'Content-Type: application/json' \
  -d '{"message": "What skills are installed?"}'
# {"reply":"...","session_id":"8cb5ce7f-..."}
```

### Continue a conversation

Pass the `session_id` returned by the previous call:

```bash
curl -X POST http://localhost:7860/api/agent \
  -H 'Content-Type: application/json' \
  -d '{"message": "And which ones are available?", "session_id": "8cb5ce7f-..."}'
```

### Stream the reply (SSE)

```bash
curl -N -X POST http://localhost:7860/api/agent/stream \
  -H 'Content-Type: application/json' \
  -d '{"message": "Summarize the project docs"}'
```

The `-N` flag disables curl buffering so events appear as they arrive.

### Python client

```python
import requests

# Full reply
r = requests.post(
    "http://localhost:7860/api/agent",
    json={"message": "What skills are installed?"},
)
data = r.json()
print(data["reply"])
session_id = data["session_id"]

# Continue the conversation
r = requests.post(
    "http://localhost:7860/api/agent",
    json={"message": "And which are available?", "session_id": session_id},
)
print(r.json()["reply"])
```

### Python streaming client (SSE)

```python
import json
import requests

with requests.post(
    "http://localhost:7860/api/agent/stream",
    json={"message": "Summarize the project docs"},
    stream=True,
) as r:
    for line in r.iter_lines():
        if line and line.startswith(b"data: "):
            event = json.loads(line[len(b"data: "):])
            print(event["reply"], end="\r")  # accumulated reply
            if event.get("done"):
                break
```

### JavaScript / fetch (SSE)

```javascript
const res = await fetch("http://localhost:7860/api/agent/stream", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ message: "Summarize the project docs" }),
});

const reader = res.body.getReader();
const decoder = new TextDecoder();
let buffer = "";

while (true) {
  const { value, done } = await reader.read();
  if (done) break;
  buffer += decoder.decode(value, { stream: true });
  for (const chunk of buffer.split("\n\n")) {
    if (chunk.startsWith("data: ")) {
      const event = JSON.parse(chunk.slice(6));
      console.log(event.reply); // accumulated reply so far
    }
  }
  buffer = buffer.endsWith("\n\n") ? "" : buffer;
}
```

## Troubleshooting

- **`ANTHROPIC_API_KEY` not set** — the agent calls will fail; export the key
  before starting the server.
- **Port already in use** — start with a different `--port`.
- **Want to see what the agent is doing** — run with `--debug` to log SDK
  events, tool calls, requests, and responses.
