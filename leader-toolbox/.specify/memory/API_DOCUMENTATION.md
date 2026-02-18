# Memory System API Documentation

## 🚀 **FastAPI Integration**

The memory system integrates seamlessly with FastAPI, providing REST endpoints for all memory operations.

## 📋 **API Endpoints**

### **POST /memory/search**
Search the memory system with vector, keyword, or hybrid search.

**Request Body:**
```json
{
  "query": "Python programming language",
  "mode": "hybrid",
  "max_results": 10,
  "min_score": 0.3,
  "vector_weight": 0.7,
  "keyword_weight": 0.3
}
```

**Response:**
```json
{
  "results": [
    {
      "id": "chunk_123",
      "file_id": "file_456",
      "file_path": "python_guide.md",
      "text": "Python is a high-level programming language...",
      "score": 0.916,
      "start_char": 0,
      "end_char": 150,
      "metadata": {
        "title": "Python Introduction",
        "category": "programming"
      }
    }
  ],
  "total_results": 1,
  "search_time_ms": 45.2,
  "search_mode": "hybrid"
}
```

**Search Modes:**
- `vector`: Semantic similarity search
- `keyword`: BM25 full-text search
- `hybrid`: Combined vector + keyword (recommended)

### **POST /memory/ingest/text**
Ingest raw text into the memory system.

**Request Body:**
```json
{
  "text": "Python is a versatile programming language...",
  "metadata": {
    "title": "Python Overview",
    "category": "programming",
    "source": "documentation"
  }
}
```

**Response:**
```json
{
  "file_id": "af464f7f-1234-5678-9abc-def123456789",
  "chunks_created": 1,
  "embeddings_generated": 1,
  "processing_time_ms": 2.7
}
```

### **POST /memory/ingest/file**
Ingest a file into the memory system.

**Request Body:**
```json
{
  "file_path": "/path/to/document.md",
  "metadata": {
    "source": "documentation",
    "category": "guides"
  }
}
```

**Response:**
```json
{
  "file_id": "d576751d-5678-9abc-def1-23456789abcd",
  "chunks_created": 3,
  "embeddings_generated": 3,
  "processing_time_ms": 8.5
}
```

### **GET /memory/status**
Get comprehensive system status and health information.

**Response:**
```json
{
  "backend": "sqlite",
  "total_files": 6,
  "total_chunks": 9,
  "total_embeddings": 9,
  "storage_size_mb": 2.3,
  "is_healthy": true,
  "vector_extension_available": false,
  "embedding_providers": [
    {
      "name": "sentence_transformers",
      "model": "all-MiniLM-L6-v2",
      "available": true,
      "dimensions": 384
    },
    {
      "name": "openai",
      "model": "text-embedding-3-small",
      "available": true,
      "dimensions": null
    }
  ],
  "search_capabilities": {
    "vector_search": true,
    "keyword_search": true,
    "hybrid_search": true
  }
}
```

### **POST /memory/sync**
Synchronize files from specified directories.

**Request Body:**
```json
{
  "paths": [
    "./memory",
    "./docs"
  ]
}
```

**Response:**
```json
{
  "files_processed": 15,
  "files_added": 3,
  "files_updated": 2,
  "files_removed": 0,
  "sync_time_ms": 1250.0
}
```

### **GET /memory/file/{file_id}**
Retrieve file content by ID.

**Response:**
```json
{
  "file_id": "af464f7f-1234-5678-9abc-def123456789",
  "content": "Full file content here...",
  "metadata": {
    "title": "Python Guide",
    "size": 2048,
    "created_at": "2026-02-15T10:30:00Z"
  }
}
```

## 🔧 **Usage Examples**

### **Python Client Example**
```python
import httpx
import asyncio

async def search_memory(query: str):
    async with httpx.AsyncClient() as client:
        response = await client.post("http://localhost:8000/memory/search", json={
            "query": query,
            "mode": "hybrid",
            "max_results": 5,
            "min_score": 0.3
        })
        return response.json()

# Usage
results = await search_memory("machine learning algorithms")
print(f"Found {len(results['results'])} results")
for result in results['results']:
    print(f"Score: {result['score']:.3f} - {result['text'][:100]}...")
```

### **cURL Example**
```bash
# Search
curl -X POST "http://localhost:8000/memory/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Python programming",
    "mode": "hybrid",
    "max_results": 3
  }'

# Ingest text
curl -X POST "http://localhost:8000/memory/ingest/text" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "FastAPI is a modern web framework for Python",
    "metadata": {"category": "web development"}
  }'

# Get status
curl "http://localhost:8000/memory/status"
```

### **JavaScript/TypeScript Example**
```typescript
interface SearchRequest {
  query: string;
  mode: 'vector' | 'keyword' | 'hybrid';
  max_results?: number;
  min_score?: number;
}

interface SearchResult {
  id: string;
  text: string;
  score: number;
  metadata: Record<string, any>;
}

async function searchMemory(request: SearchRequest): Promise<SearchResult[]> {
  const response = await fetch('http://localhost:8000/memory/search', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request)
  });

  const data = await response.json();
  return data.results;
}

// Usage
const results = await searchMemory({
  query: "web framework API",
  mode: "hybrid",
  max_results: 5
});
```

## 🎯 **Error Handling**

### **Common Error Responses**

**400 Bad Request:**
```json
{
  "detail": "Invalid search mode. Must be 'vector', 'keyword', or 'hybrid'"
}
```

**404 Not Found:**
```json
{
  "detail": "File not found: file_id_123"
}
```

**500 Internal Server Error:**
```json
{
  "detail": "Memory system initialization failed",
  "error_type": "MemorySystemError"
}
```

## ⚡ **Performance Characteristics**

| Operation | Latency | Throughput |
|-----------|---------|------------|
| **Search (vector)** | <100ms | 100+ QPS |
| **Search (keyword)** | <50ms | 200+ QPS |
| **Search (hybrid)** | <150ms | 80+ QPS |
| **Text ingestion** | 1-3ms | 500+ ops/sec |
| **File ingestion** | 5-50ms | 100+ files/sec |
| **Status check** | <10ms | 1000+ QPS |

## 🔒 **Security Considerations**

- **Input Validation**: All inputs validated with Pydantic models
- **File Access**: File paths validated to prevent directory traversal
- **Rate Limiting**: Recommended for production deployments
- **API Keys**: Environment variable configuration for embedding providers
- **PII Redaction**: Configurable automatic PII detection and redaction

## 🚀 **Production Deployment**

### **Environment Variables**
```bash
export OPENAI_API_KEY="sk-..."
export GOOGLE_API_KEY="AIza..."
export VOYAGE_API_KEY="pa-..."
export MEMORY_DB_PATH="./data/memory.db"
export LOG_LEVEL="INFO"
```

### **Docker Integration**
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### **Monitoring Endpoints**
- `GET /health` - Basic health check
- `GET /metrics` - Prometheus metrics (if configured)
- `GET /memory/status` - Detailed system status

## 📊 **OpenAPI Documentation**

The memory system automatically generates OpenAPI documentation available at:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **OpenAPI JSON**: `http://localhost:8000/openapi.json`

These provide interactive API documentation with request/response examples and the ability to test endpoints directly in the browser.