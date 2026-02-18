# Memory System for Leader-Toolbox

A comprehensive memory and knowledge management system that extends the leader-toolbox with persistent storage, advanced search capabilities, and multi-provider embedding support.

## Features

- **Hybrid Search**: Combines vector similarity and keyword matching for optimal results
- **Multiple Embedding Providers**: OpenAI, Google Gemini, Voyage AI, and local embeddings
- **Persistent Storage**: SQLite with optional vector extensions or in-memory storage
- **File Processing**: Automatic chunking and processing of documents
- **File Watching**: Real-time monitoring and synchronization of file changes
- **RESTful API**: FastAPI integration with existing endpoints
- **CLI Interface**: Command-line tools for memory management
- **Backward Compatible**: Extends existing functionality without breaking changes

## Quick Start

### Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Install optional dependencies for enhanced features:
```bash
# For vector search acceleration (optional)
pip install sqlite-vec

# For file watching (recommended)
pip install watchdog
```

### Configuration

Create or extend the configuration file at `.specify/memory/constitution_config.json`:

```json
{
  "memory": {
    "backend": "sqlite",
    "storage_path": "./data/memory.db",
    "embeddings": {
      "provider": "sentence_transformers",
      "model": "all-MiniLM-L6-v2",
      "cache_embeddings": true,
      "openai": {
        "model": "text-embedding-3-small",
        "api_key": "${OPENAI_API_KEY}"
      }
    },
    "search": {
      "max_results": 10,
      "min_score": 0.3,
      "hybrid_enabled": true,
      "vector_weight": 0.7,
      "keyword_weight": 0.3
    },
    "files": {
      "watch_directories": ["./memory", "./docs"],
      "file_patterns": ["*.md", "*.txt", "*.py"],
      "auto_sync": true
    }
  }
}
```

### Basic Usage

#### Using the API

Start the enhanced API server:

```bash
python memory_api.py
```

#### Using the CLI

```bash
# Check system status
python memory_cli.py status

# Search memory
python memory_cli.py search "machine learning"

# Ingest a file
python memory_cli.py ingest-file ./docs/readme.md

# Ingest text content
python memory_cli.py ingest-text --text "Important information to remember" --title "Notes"

# Sync files
python memory_cli.py sync
```

#### Using Programmatically

```python
from memory import MemoryManager, load_memory_config
from memory.models import SearchOptions

# Initialize
config = load_memory_config()
manager = MemoryManager(config)
await manager.initialize()

# Ingest content
file_id = await manager.ingest_text("Important document content")

# Search
results = await manager.search("important information",
    SearchOptions(mode="hybrid", max_results=5))

# Clean up
await manager.close()
```

## Architecture

### Core Components

```
┌─────────────────────────────────────────────────────────────┐
│                    Memory System Architecture                │
├─────────────────────────────────────────────────────────────┤
│  FastAPI Integration Layer                                  │
│  ├─ /memory/search (enhanced semantic search)              │
│  ├─ /memory/ingest (file and text ingestion)               │
│  ├─ /memory/status (system status and stats)               │
│  └─ /memory/manage (CRUD operations)                       │
├─────────────────────────────────────────────────────────────┤
│  Memory Manager (memory/manager.py)                        │
│  ├─ Search Orchestration (vector + keyword + hybrid)       │
│  ├─ Provider Management (embedding providers)              │
│  ├─ Storage Abstraction (persistent + in-memory)           │
│  └─ File Processing (chunking, watching, sync)             │
├─────────────────────────────────────────────────────────────┤
│  Storage Backends                                           │
│  ├─ SQLite Backend (persistent)                            │
│  └─ Memory Backend (current system)                        │
├─────────────────────────────────────────────────────────────┤
│  Embedding Providers                                        │
│  ├─ SentenceTransformers (local)                           │
│  ├─ OpenAI (text-embedding-3-small)                        │
│  ├─ Gemini (gemini-embedding-001)                          │
│  └─ Voyage (voyage-4-large)                                │
├─────────────────────────────────────────────────────────────┤
│  Search Systems                                             │
│  ├─ Vector Search (cosine similarity)                      │
│  ├─ Keyword Search (FTS5 or simple tokenization)           │
│  └─ Hybrid Search (weighted combination)                   │
└─────────────────────────────────────────────────────────────┘
```

### Storage Backends

#### SQLite Backend
- Persistent storage with full SQL capabilities
- FTS5 full-text search for keyword matching
- Optional vector extensions for fast similarity search
- Embedding cache for performance optimization

#### Memory Backend
- In-memory storage for development and testing
- Backward compatibility with existing system
- FAISS integration for vector search

### Embedding Providers

| Provider | Model | Dimensions | Local | Cost | Notes |
|----------|-------|------------|-------|------|--------|
| SentenceTransformers | all-MiniLM-L6-v2 | 384 | Yes | Free | Default, fast |
| OpenAI | text-embedding-3-small | 1536 | No | $0.02/1M | High quality |
| Gemini | gemini-embedding-001 | 768 | No | Free tier | Google AI |
| Voyage | voyage-4-large | 1024 | No | $0.13/1M | Specialized |

## API Reference

### Memory Endpoints

#### Search Memory
```http
POST /memory/search
Content-Type: application/json

{
  "query": "machine learning algorithms",
  "options": {
    "mode": "hybrid",
    "max_results": 10,
    "min_score": 0.3
  }
}
```

#### Ingest Text
```http
POST /memory/ingest/text
Content-Type: application/json

{
  "text": "Document content...",
  "metadata": {
    "title": "Document Title",
    "category": "research"
  }
}
```

#### Ingest File
```http
POST /memory/ingest/file
Content-Type: application/json

{
  "file_path": "/path/to/document.md",
  "metadata": {
    "source": "documentation"
  }
}
```

#### Get System Status
```http
GET /memory/status
```

#### Enhanced Chat
```http
POST /chat/enhanced
Content-Type: application/json

{
  "session_id": "session-123",
  "user_id": "user-456",
  "message": "What do you know about machine learning?"
}
```

### CLI Reference

#### Status Commands
```bash
# System status
python memory_cli.py status

# Configuration
python memory_cli.py config show
python memory_cli.py config validate
```

#### Search Commands
```bash
# Basic search
python memory_cli.py search "query text"

# Advanced search
python memory_cli.py search "query" --mode hybrid --max-results 10 --min-score 0.4

# JSON output
python memory_cli.py search "query" --format json
```

#### Ingestion Commands
```bash
# Ingest single file
python memory_cli.py ingest-file document.md

# Ingest with metadata
python memory_cli.py ingest-file document.md --metadata '{"category": "research"}'

# Ingest directory
python memory_cli.py ingest-directory ./docs --pattern "*.md" --pattern "*.txt"

# Ingest text
python memory_cli.py ingest-text --text "Content" --title "Title"
```

#### Sync Commands
```bash
# Sync all configured directories
python memory_cli.py sync

# Sync specific paths
python memory_cli.py sync --paths ./docs --paths ./notes
```

#### File Commands
```bash
# Get file content
python memory_cli.py get-file file-id-123

# Get specific lines
python memory_cli.py get-file file-id-123 --lines 10:50
```

## Configuration Reference

### Memory Configuration

```json
{
  "memory": {
    "backend": "sqlite",           // "sqlite" | "memory"
    "storage_path": "./data/memory.db",

    "embeddings": {
      "provider": "sentence_transformers",  // Primary provider
      "model": "all-MiniLM-L6-v2",
      "fallback_provider": "sentence_transformers",
      "cache_embeddings": true,
      "batch_size": 32,

      "openai": {
        "model": "text-embedding-3-small",
        "api_key": "${OPENAI_API_KEY}",
        "base_url": null
      },

      "gemini": {
        "model": "gemini-embedding-001",
        "api_key": "${GOOGLE_API_KEY}"
      },

      "voyage": {
        "model": "voyage-4-large",
        "api_key": "${VOYAGE_API_KEY}"
      }
    },

    "search": {
      "max_results": 10,
      "min_score": 0.3,
      "hybrid_enabled": true,
      "vector_weight": 0.7,
      "keyword_weight": 0.3
    },

    "chunking": {
      "chunk_size_chars": 1000,
      "chunk_overlap_chars": 200,
      "preserve_structure": true
    },

    "files": {
      "watch_directories": ["./memory", "./docs"],
      "file_patterns": ["*.md", "*.txt", "*.py"],
      "auto_sync": true,
      "sync_interval_seconds": 300,
      "max_file_size_mb": 10
    }
  }
}
```

### Environment Variables

```bash
# Embedding provider API keys
export OPENAI_API_KEY="your-openai-key"
export GOOGLE_API_KEY="your-google-key"
export VOYAGE_API_KEY="your-voyage-key"

# Optional: Custom API endpoints
export OPENAI_BASE_URL="https://custom-endpoint.com/v1"
```

## Advanced Features

### Custom Chunking

```python
from memory.processing import TextChunker, MarkdownChunker

# Basic text chunker
chunker = TextChunker(
    chunk_size_chars=500,
    chunk_overlap_chars=50,
    preserve_structure=True
)

# Markdown-aware chunker
md_chunker = MarkdownChunker(
    chunk_size_chars=800,
    chunk_overlap_chars=100
)
```

### Custom Search Options

```python
from memory.models import SearchOptions

# Vector-only search
options = SearchOptions(
    mode="vector",
    max_results=20,
    min_score=0.5
)

# Weighted hybrid search
options = SearchOptions(
    mode="hybrid",
    vector_weight=0.8,
    keyword_weight=0.2,
    max_results=15
)
```

### File Watching

```python
from memory.processing import FileWatcher

watcher = FileWatcher(
    debounce_seconds=2.0,
    supported_extensions=['.md', '.txt', '.py']
)

async def on_change(files):
    print(f"Files changed: {files}")

await watcher.start_watching([Path("./docs")], on_change)
```

## Performance Optimization

### Embedding Caching
- Enable embedding caching to avoid recomputing embeddings
- Cache is persistent across restarts with SQLite backend
- Automatic cache cleanup based on LRU policy

### Batch Processing
- Embeddings are generated in batches for efficiency
- Configurable batch sizes per provider
- Automatic retry with exponential backoff

### Vector Search Acceleration
- Install `sqlite-vec` for fast vector similarity search
- Falls back to numpy cosine similarity if unavailable
- FAISS integration for memory backend

### Database Optimization
- SQLite database with optimized indexes
- FTS5 for fast full-text search
- Connection pooling and prepared statements

## Troubleshooting

### Common Issues

#### "Memory system not available" Error
```bash
# Check system status
python memory_cli.py status

# Validate configuration
python memory_cli.py config validate
```

#### Embedding Provider Issues
```bash
# Check provider status
python memory_cli.py status --format json | jq .embedding_providers

# Test with fallback provider
export MEMORY_PROVIDER="sentence_transformers"
```

#### Performance Issues
```bash
# Check database size and statistics
python memory_cli.py status

# Rebuild search indexes
rm ./data/memory.db
python memory_cli.py sync
```

#### File Watching Not Working
```bash
# Install watchdog
pip install watchdog

# Check directory permissions
ls -la ./memory ./docs
```

### Logging

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Or via environment variable
export LOG_LEVEL=DEBUG
```

### Database Maintenance

```bash
# Vacuum database (reclaim space)
sqlite3 ./data/memory.db "VACUUM;"

# Analyze query performance
sqlite3 ./data/memory.db ".explain query plan SELECT ..."
```

## Migration Guide

### From Existing System

The memory system is designed to be backward compatible:

1. **Existing endpoints** continue to work unchanged
2. **Enhanced endpoints** provide additional functionality
3. **Data migration** automatically syncs existing data

### Upgrading

1. Install new dependencies
2. Update configuration file
3. Run database migrations (automatic)
4. Test enhanced endpoints

### Rollback

To disable the memory system:

1. Set `memory.enabled = false` in config
2. Use original endpoints (`/chat`, `/ingest_text`)
3. Remove memory-specific dependencies

## Contributing

### Development Setup

```bash
# Clone repository
git clone <repository-url>
cd leader-toolbox

# Install development dependencies
pip install -r requirements.txt
pip install pytest pytest-asyncio

# Run tests
pytest tests/test_memory_system.py -v

# Run linting
black memory/ tests/
flake8 memory/ tests/
```

### Adding New Providers

1. Implement `EmbeddingProvider` interface
2. Add provider configuration
3. Update `EmbeddingManager` factory
4. Add tests and documentation

### Adding Storage Backends

1. Implement `StorageBackend` interface
2. Add backend configuration options
3. Update `MemoryManager` initialization
4. Add migration utilities

## License

This memory system extends the leader-toolbox project and follows the same licensing terms.