# Memory System Design for Leader-Toolbox

## Overview

This memory system extends the existing leader-toolbox architecture with persistent storage, advanced search capabilities, and multi-provider embedding support while maintaining the current FastAPI patterns and constitution-driven configuration approach.

## Integration Points with Existing System

### Current Architecture Analysis
- **FastAPI** with async/await patterns
- **sentence-transformers** (all-MiniLM-L6-v2, 384 dimensions)
- **FAISS** vector indexing with numpy fallback
- **Pydantic** models for data validation
- **Constitution-driven** configuration
- **Module-level state** management
- **Local-first** deployment model

### Design Philosophy
1. **Extend, Don't Replace**: Build on top of existing patterns
2. **Backward Compatible**: Maintain existing API contracts
3. **Graceful Fallbacks**: Support both persistent and in-memory modes
4. **Constitution Driven**: Extend existing config patterns
5. **Optional Dependencies**: Make advanced features optional

## Architecture Overview

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
│  │  ├─ Files table (metadata)                              │
│  │  ├─ Chunks table (text + embeddings)                    │
│  │  ├─ FTS table (keyword search)                          │
│  │  └─ Cache table (embedding cache)                       │
│  └─ Memory Backend (current system)                        │
│     ├─ embeddings_store (numpy arrays)                     │
│     ├─ metadatas (dictionaries)                            │
│     └─ FAISS index                                         │
├─────────────────────────────────────────────────────────────┤
│  Embedding Providers                                        │
│  ├─ SentenceTransformers (current, local)                  │
│  ├─ OpenAI (text-embedding-3-small)                        │
│  ├─ Gemini (gemini-embedding-001)                          │
│  └─ Voyage (voyage-4-large)                                │
├─────────────────────────────────────────────────────────────┤
│  Search Systems                                             │
│  ├─ Vector Search (cosine similarity)                      │
│  ├─ Keyword Search (FTS5 or simple tokenization)           │
│  ├─ Hybrid Search (weighted combination)                   │
│  └─ File Search (semantic search over files)               │
├─────────────────────────────────────────────────────────────┤
│  File Processing Pipeline                                   │
│  ├─ File Watcher (watchdog)                                │
│  ├─ Chunking System (extends existing chunk_text)          │
│  ├─ Batch Processing (embeddings)                          │
│  └─ Sync Operations (file → database)                      │
└─────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. Memory Manager (`memory/manager.py`)

Central orchestrator that coordinates all memory operations:

```python
class MemoryManager:
    def __init__(self, config: MemoryConfig):
        self.config = config
        self.storage = self._init_storage()
        self.embedder = self._init_embedder()
        self.searcher = self._init_searcher()

    async def search(self, query: str, options: SearchOptions = None) -> List[SearchResult]
    async def ingest_text(self, text: str, metadata: Dict = None) -> str
    async def ingest_file(self, filepath: str, metadata: Dict = None) -> str
    async def get_file(self, file_id: str, lines: Range = None) -> str
    async def sync_files(self, paths: List[str] = None) -> SyncStats
    async def get_status(self) -> MemoryStatus
```

### 2. Storage Backends

#### SQLite Backend (`memory/storage/sqlite_backend.py`)
```sql
-- Files table
CREATE TABLE files (
    id TEXT PRIMARY KEY,
    path TEXT UNIQUE NOT NULL,
    hash TEXT NOT NULL,
    size INTEGER NOT NULL,
    mtime REAL NOT NULL,
    metadata JSON,
    created_at REAL NOT NULL,
    updated_at REAL NOT NULL
);

-- Chunks table
CREATE TABLE chunks (
    id TEXT PRIMARY KEY,
    file_id TEXT NOT NULL,
    text TEXT NOT NULL,
    embedding BLOB,  -- Stored as bytes
    start_char INTEGER NOT NULL,
    end_char INTEGER NOT NULL,
    metadata JSON,
    created_at REAL NOT NULL,
    FOREIGN KEY (file_id) REFERENCES files(id) ON DELETE CASCADE
);

-- Full-text search
CREATE VIRTUAL TABLE chunks_fts USING fts5(
    text,
    content='chunks',
    content_rowid='id'
);

-- Embedding cache
CREATE TABLE embedding_cache (
    hash TEXT PRIMARY KEY,
    provider TEXT NOT NULL,
    model TEXT NOT NULL,
    embedding BLOB NOT NULL,
    created_at REAL NOT NULL
);
```

#### Memory Backend (`memory/storage/memory_backend.py`)
Wrapper around existing in-memory system with enhanced interface.

### 3. Embedding Providers

#### Provider Interface (`memory/embeddings/base.py`)
```python
class EmbeddingProvider:
    @abstractmethod
    async def embed(self, texts: List[str]) -> List[np.ndarray]:
        pass

    @property
    @abstractmethod
    def dimensions(self) -> int:
        pass

    @property
    @abstractmethod
    def model_name(self) -> str:
        pass
```

#### Concrete Providers
1. **SentenceTransformersProvider**: Extends current implementation
2. **OpenAIProvider**: Remote API with batching
3. **GeminiProvider**: Google Gemini API
4. **VoyageProvider**: Voyage AI API

### 4. Search Systems

#### Hybrid Search (`memory/search/hybrid.py`)
```python
class HybridSearch:
    async def search(self, query: str, options: SearchOptions) -> List[SearchResult]:
        # Run vector and keyword search in parallel
        vector_results, keyword_results = await asyncio.gather(
            self.vector_search(query, options),
            self.keyword_search(query, options)
        )

        # Merge results with weighted scoring
        return self.merge_results(
            vector_results,
            keyword_results,
            options.vector_weight,
            options.keyword_weight
        )
```

## Configuration Extension

### Extend Constitution Config (`constitution_config.json`)

```json
{
  "memory": {
    "backend": "sqlite",  // "memory" | "sqlite"
    "storage_path": "./data/memory.db",
    "
    "embeddings": {
      "provider": "sentence_transformers",  // "sentence_transformers" | "openai" | "gemini" | "voyage" | "auto"
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
      "sync_interval_seconds": 300
    },
    "session_retention_hours": 24,
    "long_term_opt_in": true
  },
  "privacy": {
    "log_retention_days": 30,
    "auto_pii_redaction": true
  }
}
```

## API Extensions

### New Memory Endpoints

```python
# Enhanced search with multiple modes
@app.post("/memory/search")
async def memory_search(request: MemorySearchRequest) -> MemorySearchResponse:
    pass

# File ingestion with directory support
@app.post("/memory/ingest/file")
async def memory_ingest_file(request: FileIngestRequest) -> IngestResponse:
    pass

# Text ingestion (enhanced version of existing)
@app.post("/memory/ingest/text")
async def memory_ingest_text(request: TextIngestRequest) -> IngestResponse:
    pass

# Get specific file content
@app.get("/memory/files/{file_id}")
async def memory_get_file(file_id: str, lines: Optional[str] = None) -> FileContentResponse:
    pass

# System status and statistics
@app.get("/memory/status")
async def memory_status() -> MemoryStatusResponse:
    pass

# File synchronization
@app.post("/memory/sync")
async def memory_sync(request: SyncRequest) -> SyncResponse:
    pass
```

### Pydantic Models

```python
class MemorySearchRequest(BaseModel):
    query: str
    mode: Literal["vector", "keyword", "hybrid"] = "hybrid"
    max_results: int = 10
    min_score: float = 0.3
    sources: List[str] = None  # Filter by file types or directories

class SearchResult(BaseModel):
    file_id: str
    file_path: str
    text: str
    score: float
    start_char: int
    end_char: int
    metadata: Dict[str, Any]

class MemorySearchResponse(BaseModel):
    results: List[SearchResult]
    query: str
    total_results: int
    search_time_ms: float
    mode_used: str
```

## Implementation Plan

### Phase 1: Core Storage Layer
1. SQLite backend with schema
2. Storage abstraction interface
3. Migration from in-memory to persistent storage
4. Backward compatibility wrapper

### Phase 2: Enhanced Embedding System
1. Provider abstraction
2. Multiple provider implementations
3. Embedding cache
4. Batch processing

### Phase 3: Search Enhancement
1. Keyword/FTS search
2. Hybrid search implementation
3. Result merging and ranking
4. Search result caching

### Phase 4: File Processing
1. File watcher system
2. Enhanced chunking pipeline
3. Batch synchronization
4. Directory monitoring

### Phase 5: API Integration
1. New FastAPI endpoints
2. Enhanced Pydantic models
3. Configuration loading
4. Error handling

### Phase 6: Advanced Features
1. CLI interface
2. Memory analytics
3. Performance monitoring
4. Advanced search features

## Migration Strategy

### Backward Compatibility
1. Existing `/chat` endpoint unchanged
2. Existing `ingest_text` endpoint enhanced but compatible
3. Configuration migration tool
4. Data migration from in-memory to SQLite

### Gradual Adoption
1. Memory backend as default initially
2. Optional SQLite backend via config
3. Gradual migration of features
4. Performance comparison tools

## Testing Strategy

### Unit Tests
- Storage backend tests
- Embedding provider tests
- Search algorithm tests
- Configuration loading tests

### Integration Tests
- End-to-end search workflows
- File processing pipelines
- API endpoint testing
- Multi-provider embedding tests

### Performance Tests
- Large file indexing
- Concurrent search operations
- Memory usage monitoring
- Search latency benchmarks

## Deployment Considerations

### Dependencies
```toml
# New dependencies to add to pyproject.toml
dependencies = [
    # Existing dependencies...
    "watchdog>=4.0.0",        # File watching
    "sqlite-vec>=0.1.7",      # Vector extension (optional)
    "openai>=1.0.0",          # OpenAI embeddings
    "google-generativeai",    # Gemini embeddings
    "voyageai",               # Voyage embeddings
    "click>=8.0.0",           # CLI interface
]
```

### Configuration
- Environment variable support for API keys
- Constitution config validation
- Runtime configuration updates

### Storage
- SQLite database location
- Embedding cache management
- File system permissions
- Backup strategies

This design maintains your existing architecture while adding powerful memory capabilities that can scale from local development to production use cases.