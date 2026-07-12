# Leader Assistant

An IM (Instant Messaging) assistant that listens to messages, retrieves knowledge, and returns best answers to project questions.

## Architecture

This project uses **claude-agent-sdk** (Python) to:

1. Listen to incoming IM messages via Gradio web interface
2. Retrieve relevant knowledge from project documentation using Read/Glob/Grep tools
3. Generate contextual answers using Claude

## Project Structure

```text
leader-assistant/
├── CLAUDE.md          # Project documentation
├── README.md          # API documentation
├── pyproject.toml     # Python dependencies (uv)
├── agents/
│   └── assistant.md   # Agent system prompt
├── app.py             # Gradio web interface
├── core.py            # Core assistant logic with Claude Agent SDK
└── style.py           # UI styling
```

## Development

```bash
# Install dependencies
uv sync

# Run the assistant server
uv run python app.py
```

## Environment Variables

- `ANTHROPIC_API_KEY` - Claude API key (required)

## Key Commands

- `uv sync` - Install dependencies
- `uv run python app.py` - Start the Gradio web server
- `uv run pytest` - Run tests
