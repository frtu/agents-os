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

# Run with debug logging
uv run python app.py --debug
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
├── skills/            # Installed skills (symlinks or copies)
├── app.py             # Gradio web interface
├── core.py            # Core assistant logic with Claude Agent SDK
├── skill_manager.py   # CLI for installing skills from ../skills
└── style.py           # UI styling
```

## How It Works

The assistant uses **claude-agent-sdk** with Read/Glob/Grep tools to:

1. Search for relevant files in the knowledge base
2. Read file contents to gather information
3. Synthesize answers with source citations

## Skill Management

Skills extend the assistant with additional capabilities. Manage them using `skill_manager.py`:

```bash
# List available skills from ../skills
python skill_manager.py list

# Show details of a specific skill
python skill_manager.py show <skill-name>

# Install a skill (creates symlink by default)
python skill_manager.py install <skill-name>

# Install as a copy instead of symlink
python skill_manager.py install <skill-name> --copy

# List installed skills
python skill_manager.py installed

# Uninstall a skill
python skill_manager.py uninstall <skill-name>
```

Installed skills are automatically loaded into the assistant's context.

## Command Line Options

```bash
uv run python app.py [options]
```

| Option | Description |
|--------|-------------|
| `--debug` | Enable debug logging (logs SDK events, requests, and responses) |
| `--port PORT` | Server port (default: 7860) |
| `--share` | Create a public Gradio URL |

## Configuration

- `agents/assistant.md` - Edit the agent system prompt
- `core.py` - Customize `KNOWLEDGE_BASE` (default: parent directory), model, and tools
