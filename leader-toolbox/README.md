# Leader Toolbox Memory System

A comprehensive memory system built with PostgreSQL, Elasticsearch, and Kotlin/Spring Boot, featuring semantic search using all-MiniLM-L6-v2 embeddings.

## 🚀 Features

- **Document Ingestion**: Automatic text chunking and embedding generation
- **Hybrid Search**: Combines semantic vector search with keyword-based search
- **PostgreSQL Storage**: Robust relational database with JSONB support
- **Elasticsearch Integration**: Fast full-text and vector search capabilities
- **Session Management**: User sessions with context tracking
- **Search Analytics**: Performance monitoring and usage insights
- **Flexible Tagging**: Metadata organization system
- **REST API**: Complete REST interface with OpenAPI documentation

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                  Spring Boot Application                │
├─────────────────┬─────────────┬─────────────────────────┤
│   Memory        │  Embedding  │      Search             │
│   Service       │  Service    │      Service            │
└─────────────────┴─────────────┴─────────────────────────┘
        │               │                    │
        ▼               ▼                    ▼
┌─────────────┐  ┌─────────────┐    ┌─────────────────┐
│PostgreSQL   │  │HuggingFace  │    │  Elasticsearch  │
│- Documents  │  │API +        │    │  - Full-text   │
│- Chunks     │  │Local        │    │  - Vector       │
│- Embeddings │  │Fallback     │    │  - Analytics    │
│- Sessions   │  │             │    │                 │
└─────────────┘  └─────────────┘    └─────────────────┘
```

## 🛠️ Technology Stack

- **Backend**: Kotlin + Spring Boot 3.2
- **Database**: PostgreSQL 15+ with pgvector extension (optional)
- **Search**: Elasticsearch 8.x
- **Embedding**: all-MiniLM-L6-v2 (384 dimensions)
- **Caching**: Caffeine + Redis (optional)
- **Testing**: JUnit 5 + Testcontainers
- **Build**: Gradle with Kotlin DSL

## 📋 Prerequisites

- Java 17+
- PostgreSQL 15+
- Elasticsearch 8.x
- Docker (for local development)
- HuggingFace API key (optional, for remote embeddings)

## 🔧 Quick Start

### 1. Clone and Setup

```bash
git clone <repository>
cd leader-toolbox
```

### 2. Start Dependencies with Docker Compose

```bash
docker-compose up -d
```

This starts:
- PostgreSQL on port 5432
- Elasticsearch on port 9200
- (Optional) Redis for caching

### 3. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit configuration
export DB_USERNAME=debezium
export DB_PASSWORD=debezium
export ELASTICSEARCH_URIS=http://localhost:9200
export HUGGINGFACE_API_KEY=your_key_here  # Optional
```

### 4. Run Database Migrations

```bash
./gradlew flywayMigrate
```

### 5. Build and Run

```bash
./gradlew bootRun

# Or for development with hot reload
./gradlew bootRun --args='--spring.profiles.active=development'
```

The API will be available at `http://localhost:8080/api`

## 📖 API Usage

### Document Ingestion

```bash
# Ingest a document
curl -X POST http://localhost:8080/api/v1/memory/documents \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Machine Learning Guide",
    "content": "Machine learning is a subset of artificial intelligence...",
    "contentType": "text/plain",
    "sourcePath": "/docs/ml-guide.txt",
    "metadata": {
      "category": "education",
      "author": "John Doe"
    },
    "chunkSize": 1000,
    "chunkOverlap": 200
  }'
```

### Search Documents

```bash
# Semantic search
curl -X POST http://localhost:8080/api/v1/memory/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "artificial intelligence and machine learning",
    "searchType": "HYBRID",
    "maxResults": 10,
    "minScore": 0.3,
    "includeContent": true
  }'
```

### List Documents

```bash
# Get all documents with pagination
curl "http://localhost:8080/api/v1/memory/documents?page=0&size=20&search=machine"
```

### Session Management

```bash
# Create a session
curl -X POST http://localhost:8080/api/v1/memory/sessions \
  -H "Content-Type: application/json" \
  -d '{
    "userId": "user123",
    "sessionName": "Research Session",
    "contextData": {
      "preferences": {"theme": "dark"},
      "lastQuery": "neural networks"
    }
  }'

# Search with session context
curl -X POST http://localhost:8080/api/v1/memory/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "deep learning",
    "sessionId": "session-uuid-here",
    "searchType": "HYBRID"
  }'
```

### Health Check

```bash
# System health
curl http://localhost:8080/api/actuator/health

# Memory system status
curl http://localhost:8080/api/v1/memory/health
```

## 🧪 Testing

### Run All Tests

```bash
./gradlew test
```

### Integration Tests with Testcontainers

```bash
# Run integration tests (starts PostgreSQL and Elasticsearch containers)
./gradlew integrationTest
```

### Unit Tests Only

```bash
./gradlew test --tests "*.unit.*"
```
