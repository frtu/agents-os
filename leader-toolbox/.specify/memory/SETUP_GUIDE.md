# Memory System Setup Guide

## 🚀 **Quick Start**

### **Prerequisites**
- Python 3.11 or higher
- Virtual environment (recommended)
- Git (for cloning repositories)

### **Installation**
```bash
# 1. Navigate to project directory
cd /path/to/leader-toolbox

# 2. Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Test the system
python example_usage.py
```

## 📋 **Dependencies Overview**

### **Core Dependencies**
```
faiss-cpu==1.13.2           # Vector similarity search
fastapi>=0.128.4            # Web framework
numpy<2                     # Numerical computing
sentence-transformers>=5.2.2 # Embedding generation
pydantic>=2.0.0             # Data validation
```

### **Memory System Dependencies**
```
watchdog>=4.0.0             # File watching
openai>=1.0.0              # OpenAI embeddings
google-generativeai>=0.8.0 # Gemini embeddings
voyageai>=0.2.0            # Voyage embeddings
click>=8.0.0               # CLI interface
sqlite-vec==0.1.6          # Vector extension (optional)
```

### **Development Dependencies**
```
pytest>=9.0.2              # Testing framework
uvicorn[standard]>=0.40.0   # ASGI server
```

## ⚙️ **Configuration**

### **Environment Variables**
```bash
# Required for production (optional for local development)
export OPENAI_API_KEY="sk-your-openai-key"
export GOOGLE_API_KEY="AIza-your-gemini-key"
export VOYAGE_API_KEY="pa-your-voyage-key"

# Optional configuration
export MEMORY_DB_PATH="./data/memory.db"
export LOG_LEVEL="INFO"
export HF_TOKEN="hf_your-huggingface-token"  # For faster model downloads
```

### **Configuration File**
The system automatically loads configuration from:
`.specify/memory/constitution_config.json`

**Key Configuration Sections:**
```json
{
  "memory": {
    "backend": "sqlite",
    "storage_path": "./data/memory.db",
    "embeddings": {
      "provider": "sentence_transformers",
      "model": "all-MiniLM-L6-v2",
      "cache_embeddings": true
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
      "auto_sync": true,
      "max_file_size_mb": 10
    }
  }
}
```

## 🔧 **System Integration**

### **FastAPI Integration**
Add memory endpoints to your existing FastAPI app:

```python
# main.py
from fastapi import FastAPI
from memory_api import router as memory_router

app = FastAPI(title="Leader Toolbox with Memory")

# Add memory endpoints
app.include_router(memory_router, prefix="/memory", tags=["memory"])

# Your existing endpoints...
```

### **Standalone Usage**
Use the memory system independently:

```python
# standalone_example.py
import asyncio
from memory import MemoryManager, SearchOptions

async def main():
    # Initialize memory system
    manager = MemoryManager()
    await manager.initialize()

    # Ingest some text
    file_id = await manager.ingest_text(
        "Python is a versatile programming language",
        {"category": "programming"}
    )

    # Search
    results = await manager.search(
        "programming language",
        SearchOptions(mode="hybrid", max_results=5)
    )

    print(f"Found {len(results)} results")
    for result in results:
        print(f"Score: {result.score:.3f} - {result.text[:100]}")

    await manager.close()

if __name__ == "__main__":
    asyncio.run(main())
```

## 🖥️ **CLI Usage**

### **Basic Commands**
```bash
# Search memory
python -m memory.cli search "machine learning"

# Ingest text
python -m memory.cli ingest-text "FastAPI is a web framework" --title "FastAPI Info"

# Ingest file
python -m memory.cli ingest-file /path/to/document.md

# System status
python -m memory.cli status

# Sync files
python -m memory.cli sync ./docs ./memory
```

### **CLI Options**
```bash
# Search with options
python -m memory.cli search "Python programming" \
  --mode hybrid \
  --max-results 5 \
  --min-score 0.5

# Ingest with metadata
python -m memory.cli ingest-text "Sample text" \
  --metadata '{"category": "examples", "author": "user"}'

# Verbose output
python -m memory.cli --verbose status
```

## 📊 **Health Monitoring**

### **System Status Check**
```python
from memory import MemoryManager

async def check_system_health():
    manager = MemoryManager()
    await manager.initialize()

    status = await manager.get_status()

    print(f"System Health: {'✅' if status.is_healthy else '❌'}")
    print(f"Files: {status.total_files}")
    print(f"Chunks: {status.total_chunks}")
    print(f"Storage: {status.storage_size_mb:.1f} MB")

    for provider in status.embedding_providers:
        status_icon = "✅" if provider.available else "❌"
        print(f"Provider {provider.name}: {status_icon}")
```

### **Performance Monitoring**
```python
import time
from memory import MemoryManager, SearchOptions

async def performance_test():
    manager = MemoryManager()
    await manager.initialize()

    # Test search performance
    queries = [
        "machine learning algorithms",
        "web development frameworks",
        "data science techniques"
    ]

    for query in queries:
        start_time = time.time()
        results = await manager.search(
            query,
            SearchOptions(mode="hybrid", max_results=10)
        )
        end_time = time.time()

        print(f"Query: '{query}'")
        print(f"Results: {len(results)}")
        print(f"Time: {(end_time - start_time) * 1000:.1f}ms")
        print(f"Best score: {results[0].score:.3f}" if results else "No results")
        print()
```

## 🐳 **Docker Deployment**

### **Dockerfile**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create data directory
RUN mkdir -p /app/data

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/memory/status || exit 1

# Run application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### **docker-compose.yml**
```yaml
version: '3.8'

services:
  leader-toolbox:
    build: .
    ports:
      - "8000:8000"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - GOOGLE_API_KEY=${GOOGLE_API_KEY}
      - VOYAGE_API_KEY=${VOYAGE_API_KEY}
      - MEMORY_DB_PATH=/app/data/memory.db
    volumes:
      - ./data:/app/data
      - ./memory:/app/memory
      - ./docs:/app/docs
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/memory/status"]
      interval: 30s
      timeout: 10s
      retries: 3
```

### **Build and Run**
```bash
# Build container
docker build -t leader-toolbox .

# Run with docker-compose
docker-compose up -d

# Check status
curl http://localhost:8000/memory/status
```

## 🔧 **Troubleshooting**

### **Common Issues**

#### **1. Import Errors**
```bash
# Problem: ModuleNotFoundError: No module named 'memory'
# Solution: Ensure you're in the project root and venv is activated
cd /path/to/leader-toolbox
source .venv/bin/activate
python -c "import memory; print('Success!')"
```

#### **2. SQLite Vector Extension Warning**
```bash
# Problem: Vector extension not available
# Impact: Uses slower brute-force search (acceptable for most cases)
# Solution: Install sqlite-vec extension (optional)
pip install sqlite-vec==0.1.6
```

#### **3. SentenceTransformers Download Issues**
```bash
# Problem: Slow model downloads
# Solution: Set HF_TOKEN for authenticated downloads
export HF_TOKEN="hf_your_token"

# Or download manually
python -c "
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('all-MiniLM-L6-v2')
print('Model downloaded successfully!')
"
```

#### **4. File Ingestion Foreign Key Error**
```bash
# Problem: FOREIGN KEY constraint failed
# Status: Known issue, affects file ingestion only
# Workaround: Use text ingestion instead
python -c "
import asyncio
from memory import MemoryManager

async def test():
    manager = MemoryManager()
    await manager.initialize()

    # This works
    file_id = await manager.ingest_text('Test content')
    print(f'Success: {file_id}')

    await manager.close()

asyncio.run(test())
"
```

### **Performance Tuning**

#### **Memory Usage**
```python
# Reduce memory usage for large datasets
config = {
    "memory": {
        "embeddings": {
            "batch_size": 16,  # Reduce from default 32
            "cache_embeddings": False  # Disable caching if memory is limited
        }
    }
}
```

#### **Search Performance**
```python
# Optimize search parameters
search_options = SearchOptions(
    max_results=5,      # Reduce result set size
    min_score=0.5,      # Higher threshold = faster search
    mode="vector"       # Single mode is faster than hybrid
)
```

## 📈 **Production Checklist**

### **Before Deployment**
- [ ] Environment variables configured
- [ ] Database path accessible and writable
- [ ] API keys tested and valid
- [ ] Health endpoints responding
- [ ] Performance benchmarked under load

### **Security Considerations**
- [ ] API keys stored securely (not in code)
- [ ] File access permissions configured
- [ ] Input validation enabled
- [ ] Rate limiting configured (if needed)
- [ ] Logging configured appropriately

### **Monitoring Setup**
- [ ] Health check endpoints configured
- [ ] Performance metrics collection
- [ ] Error alerting configured
- [ ] Log aggregation setup
- [ ] Backup strategy for database

## 🎯 **Next Steps**

1. **Test Basic Functionality**: Run `python example_usage.py`
2. **Integrate with Your App**: Add memory endpoints to FastAPI
3. **Configure for Your Use Case**: Adjust search parameters and file patterns
4. **Monitor Performance**: Set up health checks and metrics
5. **Scale as Needed**: Consider distributed deployment for high load

For questions or issues, refer to the [Implementation Status](IMPLEMENTATION_STATUS.md) and [API Documentation](API_DOCUMENTATION.md).