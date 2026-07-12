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
├── skills/            # Installed skills (symlinks)
├── app.py             # Gradio web interface
├── core.py            # Core assistant logic with Claude Agent SDK
├── skill_manager.py   # CLI for installing skills from ../skills
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

## Skill Management

Skills can be installed from the shared `../skills` folder using `skill_manager.py`:

```bash
# List available skills
python3 skill_manager.py list

# Show skill details
python3 skill_manager.py show <skill-name>

# Install a skill (creates symlink)
python3 skill_manager.py install <skill-name>

# Install as copy instead of symlink
python3 skill_manager.py install <skill-name> --copy

# List installed skills
python3 skill_manager.py installed

# Uninstall a skill
python3 skill_manager.py uninstall <skill-name>
```

Installed skills are stored in `skills/` as symlinks (by default) or copies.
