# Leader Assistant

An IM assistant that retrieves knowledge from project documentation and answers questions using Claude.

## Quick Start

```bash
# Install dependencies
uv sync

# Set your API key
export ANTHROPIC_API_KEY=your_key_here

# Run the assistant
uv run python app.py
```

Then open http://localhost:7860 in your browser.

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

## How It Works

The assistant uses **claude-agent-sdk** with Read/Glob/Grep tools to:

1. Search for relevant files in the knowledge base
2. Read file contents to gather information
3. Synthesize answers with source citations

## Configuration

- `agents/assistant.md` - Edit the agent system prompt
- `core.py` - Customize `KNOWLEDGE_BASE` (default: parent directory), model, and tools
