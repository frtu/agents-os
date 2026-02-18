# Memory Storage Design: PostgreSQL + Elasticsearch + Kotlin/Spring Boot

This document outlines the storage architecture for rebuilding the leader-toolbox memory system using PostgreSQL for structured data, Elasticsearch for full-text and vector search, and Kotlin/Spring Boot for the backend services.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Storage Layer Design](#storage-layer-design)
3. [Data Models](#data-models)
4. [Search Strategy](#search-strategy)
5. [Service Architecture](#service-architecture)
6. [API Design](#api-design)
7. [Performance Considerations](#performance-considerations)
8. [Implementation Plan](#implementation-plan)

## Architecture Overview

### High-Level Components

```
┌─────────────────────────────────────────────────────────────────┐
│                    Leader Toolbox Memory System                 │
└─────────────────────────────────────────────────────────────────┘
                                   │
    ┌─────────────────┬─────────────┼─────────────┬─────────────────┐
    │                 │             │             │                 │
    ▼                 ▼             ▼             ▼                 ▼
┌─────────┐    ┌────────────┐  ┌─────────┐  ┌────────────┐  ┌─────────────┐
│ Web API │    │   Memory   │  │Embedding│  │   Search   │  │   Admin     │
│Controller│    │  Service   │  │ Service │  │  Service   │  │  Service    │
│         │    │            │  │         │  │            │  │             │
└─────────┘    └────────────┘  └─────────┘  └────────────┘  └─────────────┘
    │                 │             │             │                 │
    └─────────────────┼─────────────┼─────────────┼─────────────────┘
                      │             │             │
              ┌───────┼─────────────┼─────────────┼────────────────┐
              │       │             │             │                │
              ▼       ▼             ▼             ▼                ▼
    ┌─────────────────────┐                ┌──────────────────────────┐
    │    PostgreSQL       │                │      Elasticsearch       │
    │                     │                │                          │
    │ ├─ memory_documents │ ◄─────────────► │ ├─ documents            │
    │ ├─ memory_chunks    │                │ ├─ embeddings            │
    │ ├─ memory_sessions  │                │ └─ search_analytics      │
    │ ├─ chunk_embeddings │                │                          │
    │ └─ metadata_tags    │                └──────────────────────────┘
    └─────────────────────┘
```

### Technology Stack

- **Backend Framework**: Spring Boot 3.x with Kotlin
- **Database**: PostgreSQL 15+ (structured data, ACID transactions)
- **Search Engine**: Elasticsearch 8.x (full-text search + vector search)
- **Embedding Model**: all-MiniLM-L6-v2 (384 dimensions)
- **Build Tool**: Gradle with Kotlin DSL
- **Testing**: JUnit 5, Testcontainers, MockK

## Storage Layer Design

### PostgreSQL Schema Design

PostgreSQL serves as the **source of truth** for all structured data, relationships, and metadata.

#### Core Tables

1. **memory_documents** - Document metadata and source content
2. **memory_chunks** - Text chunks with positioning information
3. **chunk_embeddings** - Vector embeddings (with compression)
4. **memory_sessions** - User sessions and conversation context
5. **metadata_tags** - Flexible tagging system

#### Design Principles

- **Normalized structure** for data integrity
- **JSONB fields** for flexible metadata
- **Vector compression** using PostgreSQL arrays
- **Audit trails** with created/updated timestamps
- **Soft deletes** for data retention
- **Partitioning** for large-scale chunk storage

### Elasticsearch Index Design

Elasticsearch provides **high-performance search** capabilities with both text and vector search.

#### Core Indices

1. **documents** - Optimized for document-level search
2. **chunks** - Chunk-level search with vector embeddings
3. **search_analytics** - Query patterns and performance metrics

#### Design Principles

- **Denormalized structure** for search performance
- **Dense vector fields** for semantic search
- **Text analyzers** for keyword search
- **Completion suggesters** for autocomplete
- **Index templates** for consistent mapping

## Data Models

### PostgreSQL Entities

#### MemoryDocument
```sql
CREATE TABLE memory_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(500) NOT NULL,
    content_type VARCHAR(50) NOT NULL DEFAULT 'text/plain',
    source_path TEXT,
    source_url TEXT,
    content_hash VARCHAR(64) NOT NULL,
    content_length INTEGER NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ,

    CONSTRAINT chk_source CHECK (
        source_path IS NOT NULL OR source_url IS NOT NULL
    )
);
```

#### MemoryChunk
```sql
CREATE TABLE memory_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES memory_documents(id),
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    token_count INTEGER NOT NULL,
    char_start_pos INTEGER NOT NULL,
    char_end_pos INTEGER NOT NULL,
    content_hash VARCHAR(64) NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT uk_document_chunk UNIQUE (document_id, chunk_index)
);
```

#### ChunkEmbedding
```sql
CREATE TABLE chunk_embeddings (
    chunk_id UUID PRIMARY KEY REFERENCES memory_chunks(id),
    embedding_vector REAL[] NOT NULL,
    model_name VARCHAR(100) NOT NULL DEFAULT 'all-MiniLM-L6-v2',
    vector_dimension INTEGER NOT NULL DEFAULT 384,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT chk_vector_dimension CHECK (
        array_length(embedding_vector, 1) = vector_dimension
    )
);
```

#### MemorySession
```sql
CREATE TABLE memory_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(100),
    session_name VARCHAR(200),
    context_data JSONB DEFAULT '{}',
    last_accessed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ
);
```

### Kotlin Data Classes

#### Domain Models
```kotlin
@Entity
@Table(name = "memory_documents")
data class MemoryDocument(
    @Id
    val id: UUID = UUID.randomUUID(),

    @Column(length = 500, nullable = false)
    val title: String,

    @Column(name = "content_type", length = 50, nullable = false)
    val contentType: String = "text/plain",

    @Column(name = "source_path")
    val sourcePath: String? = null,

    @Column(name = "source_url")
    val sourceUrl: String? = null,

    @Column(name = "content_hash", length = 64, nullable = false)
    val contentHash: String,

    @Column(name = "content_length", nullable = false)
    val contentLength: Int,

    @Type(JsonType::class)
    @Column(columnDefinition = "jsonb")
    val metadata: Map<String, Any> = emptyMap(),

    @CreationTimestamp
    @Column(name = "created_at", nullable = false)
    val createdAt: OffsetDateTime = OffsetDateTime.now(),

    @UpdateTimestamp
    @Column(name = "updated_at", nullable = false)
    val updatedAt: OffsetDateTime = OffsetDateTime.now(),

    @Column(name = "deleted_at")
    val deletedAt: OffsetDateTime? = null
)
```

#### DTOs and Requests
```kotlin
data class DocumentIngestRequest(
    val title: String,
    val content: String,
    val contentType: String = "text/plain",
    val sourcePath: String? = null,
    val sourceUrl: String? = null,
    val metadata: Map<String, Any> = emptyMap(),

    @field:Min(100)
    @field:Max(5000)
    val chunkSize: Int = 1000,

    @field:Min(50)
    @field:Max(1000)
    val chunkOverlap: Int = 200
)

data class MemorySearchRequest(
    val query: String,
    val sessionId: UUID? = null,
    val userId: String? = null,

    @field:Min(1)
    @field:Max(50)
    val maxResults: Int = 10,

    @field:DecimalMin("0.0")
    @field:DecimalMax("1.0")
    val minScore: Double = 0.3,

    val searchType: SearchType = SearchType.HYBRID,
    val includeContent: Boolean = false
)

enum class SearchType {
    SEMANTIC,   // Vector similarity only
    KEYWORD,    // Text search only
    HYBRID      // Combined approach
}

data class MemorySearchResult(
    val chunkId: UUID,
    val documentId: UUID,
    val title: String,
    val excerpt: String,
    val fullContent: String? = null,
    val score: Double,
    val chunkIndex: Int,
    val searchType: String,
    val metadata: Map<String, Any> = emptyMap()
)
```

## Search Strategy

### Hybrid Search Implementation

The system implements a sophisticated hybrid search combining semantic vector search with keyword-based text search.

#### Search Flow
```
Query Input
     │
     ▼
┌─────────────────────────────────┐
│     Query Processing            │
│ ├─ Normalize and clean text    │
│ ├─ Generate embedding vector   │
│ └─ Extract keywords            │
└─────────────────────────────────┘
     │
     ▼
┌─────────────────┬─────────────────┐
│   Vector Search │  Keyword Search │
│                 │                 │
│ ├─ Elasticsearch│ ├─ Elasticsearch│
│ │  dense_vector │ │  full_text     │
│ │  cosine sim.  │ │  BM25 scoring  │
│ └─ Top N*4      │ └─ Top N*4       │
└─────────────────┴─────────────────┘
     │                       │
     └───────────┬───────────┘
                 ▼
    ┌─────────────────────────────┐
    │   Result Fusion & Ranking  │
    │ ├─ Reciprocal Rank Fusion  │
    │ ├─ Score normalization     │
    │ ├─ Duplicate removal       │
    │ └─ Final ranking           │
    └─────────────────────────────┘
                 │
                 ▼
           Final Results
```

#### Elasticsearch Queries

**Vector Search Query:**
```json
{
  "query": {
    "script_score": {
      "query": {"match_all": {}},
      "script": {
        "source": "cosineSimilarity(params.query_vector, 'embedding_vector') + 1.0",
        "params": {
          "query_vector": [0.1, 0.2, ...]
        }
      }
    }
  },
  "size": 40
}
```

**Keyword Search Query:**
```json
{
  "query": {
    "multi_match": {
      "query": "user query text",
      "fields": ["title^2", "content", "metadata.tags^1.5"],
      "type": "best_fields",
      "fuzziness": "AUTO"
    }
  },
  "_source": ["id", "title", "content", "metadata"],
  "size": 40
}
```

#### Reciprocal Rank Fusion (RRF)
```kotlin
class HybridSearchService {
    fun fuseResults(
        vectorResults: List<SearchResult>,
        keywordResults: List<SearchResult>,
        k: Int = 60
    ): List<SearchResult> {
        val fusedScores = mutableMapOf<UUID, Double>()

        // Process vector search results
        vectorResults.forEachIndexed { rank, result ->
            val rrfScore = 1.0 / (k + rank + 1)
            fusedScores[result.chunkId] = fusedScores.getOrDefault(result.chunkId, 0.0) + rrfScore
        }

        // Process keyword search results
        keywordResults.forEachIndexed { rank, result ->
            val rrfScore = 1.0 / (k + rank + 1)
            fusedScores[result.chunkId] = fusedScores.getOrDefault(result.chunkId, 0.0) + rrfScore
        }

        // Combine and rank results
        return fusedScores.entries
            .sortedByDescending { it.value }
            .mapNotNull { entry ->
                // Retrieve full result data and apply final scoring
                findResultByChunkId(entry.key, vectorResults, keywordResults)
                    ?.copy(score = entry.value)
            }
    }
}
```

## Service Architecture

### Spring Boot Service Layer

#### MemoryService
```kotlin
@Service
@Transactional
class MemoryService(
    private val documentRepository: MemoryDocumentRepository,
    private val chunkRepository: MemoryChunkRepository,
    private val embeddingRepository: ChunkEmbeddingRepository,
    private val searchService: MemorySearchService,
    private val embeddingService: EmbeddingService,
    private val chunkingService: TextChunkingService
) {

    suspend fun ingestDocument(request: DocumentIngestRequest): MemoryDocument {
        log.info("Ingesting document: ${request.title}")

        // 1. Create document record
        val contentHash = sha256(request.content)
        val document = documentRepository.save(
            MemoryDocument(
                title = request.title,
                contentType = request.contentType,
                sourcePath = request.sourcePath,
                sourceUrl = request.sourceUrl,
                contentHash = contentHash,
                contentLength = request.content.length,
                metadata = request.metadata
            )
        )

        // 2. Chunk the content
        val chunks = chunkingService.chunkText(
            request.content,
            chunkSize = request.chunkSize,
            overlap = request.chunkOverlap
        )

        // 3. Save chunks and generate embeddings
        val savedChunks = chunks.mapIndexed { index, chunk ->
            chunkRepository.save(
                MemoryChunk(
                    documentId = document.id,
                    chunkIndex = index,
                    content = chunk.text,
                    tokenCount = chunk.tokenCount,
                    charStartPos = chunk.startPos,
                    charEndPos = chunk.endPos,
                    contentHash = sha256(chunk.text)
                )
            )
        }

        // 4. Generate embeddings asynchronously
        GlobalScope.launch {
            generateAndStoreEmbeddings(savedChunks)
            indexInElasticsearch(document, savedChunks)
        }

        return document
    }

    suspend fun searchMemory(request: MemorySearchRequest): List<MemorySearchResult> {
        return searchService.hybridSearch(request)
    }

    private suspend fun generateAndStoreEmbeddings(chunks: List<MemoryChunk>) {
        val embeddings = embeddingService.generateEmbeddings(chunks.map { it.content })

        chunks.zip(embeddings).forEach { (chunk, embedding) ->
            embeddingRepository.save(
                ChunkEmbedding(
                    chunkId = chunk.id,
                    embeddingVector = embedding,
                    modelName = "all-MiniLM-L6-v2",
                    vectorDimension = 384
                )
            )
        }
    }
}
```

#### EmbeddingService
```kotlin
@Service
class EmbeddingService(
    @Value("\${memory.embedding.model-path:#{null}}")
    private val modelPath: String?,

    private val cacheManager: CacheManager
) {

    private val model: SentenceTransformerModel by lazy {
        initializeModel()
    }

    private fun initializeModel(): SentenceTransformerModel {
        return if (modelPath != null) {
            // Load from local path if specified
            SentenceTransformerModel.load(Paths.get(modelPath))
        } else {
            // Download all-MiniLM-L6-v2 from HuggingFace
            SentenceTransformerModel.load("sentence-transformers/all-MiniLM-L6-v2")
        }
    }

    @Cacheable("embeddings")
    suspend fun generateEmbedding(text: String): FloatArray {
        return withContext(Dispatchers.IO) {
            model.encode(text)
        }
    }

    suspend fun generateEmbeddings(texts: List<String>): List<FloatArray> {
        return withContext(Dispatchers.IO) {
            model.encode(texts)
        }
    }

    companion object {
        private val log = LoggerFactory.getLogger(EmbeddingService::class.java)
        const val VECTOR_DIMENSION = 384
    }
}
```

### Elasticsearch Integration

#### ElasticsearchService
```kotlin
@Service
class ElasticsearchService(
    private val elasticsearchClient: ElasticsearchClient
) {

    suspend fun indexDocument(document: MemoryDocument, chunks: List<MemoryChunk>) {
        // Index document
        val documentIndex = DocumentIndexRequest(
            id = document.id.toString(),
            title = document.title,
            contentType = document.contentType,
            sourcePath = document.sourcePath,
            sourceUrl = document.sourceUrl,
            metadata = document.metadata,
            chunkCount = chunks.size,
            totalTokens = chunks.sumOf { it.tokenCount }
        )

        elasticsearchClient.index(
            IndexRequest.of { req ->
                req.index("documents")
                    .id(document.id.toString())
                    .document(documentIndex)
            }
        )

        // Index chunks with embeddings
        chunks.forEach { chunk ->
            val embedding = getEmbeddingForChunk(chunk.id)

            val chunkIndex = ChunkIndexRequest(
                id = chunk.id.toString(),
                documentId = document.id.toString(),
                title = document.title,
                content = chunk.content,
                chunkIndex = chunk.chunkIndex,
                tokenCount = chunk.tokenCount,
                embeddingVector = embedding,
                metadata = document.metadata
            )

            elasticsearchClient.index(
                IndexRequest.of { req ->
                    req.index("chunks")
                        .id(chunk.id.toString())
                        .document(chunkIndex)
                }
            )
        }
    }

    suspend fun vectorSearch(
        queryEmbedding: FloatArray,
        maxResults: Int = 40
    ): List<SearchResult> {
        val searchRequest = SearchRequest.of { req ->
            req.index("chunks")
                .query { q ->
                    q.scriptScore { ss ->
                        ss.query { mq -> mq.matchAll { ma -> ma } }
                            .script { s ->
                                s.source("cosineSimilarity(params.query_vector, 'embedding_vector') + 1.0")
                                    .params("query_vector", queryEmbedding.toList())
                            }
                    }
                }
                .size(maxResults)
                .source { src ->
                    src.includes("id", "document_id", "title", "content", "chunk_index", "metadata")
                }
        }

        val response = elasticsearchClient.search(searchRequest, ChunkIndexRequest::class.java)

        return response.hits().hits().map { hit ->
            val chunk = hit.source()!!
            SearchResult(
                chunkId = UUID.fromString(chunk.id),
                documentId = UUID.fromString(chunk.documentId),
                title = chunk.title,
                excerpt = chunk.content.take(400),
                score = hit.score()?.toDouble() ?: 0.0,
                chunkIndex = chunk.chunkIndex,
                searchType = "vector",
                metadata = chunk.metadata
            )
        }
    }
}
```

## API Design

### REST Endpoints

#### DocumentController
```kotlin
@RestController
@RequestMapping("/api/v1/memory")
@Validated
class MemoryController(
    private val memoryService: MemoryService
) {

    @PostMapping("/documents")
    suspend fun ingestDocument(
        @Valid @RequestBody request: DocumentIngestRequest
    ): ResponseEntity<MemoryDocumentResponse> {
        val document = memoryService.ingestDocument(request)
        return ResponseEntity.ok(MemoryDocumentResponse.fromEntity(document))
    }

    @PostMapping("/search")
    suspend fun searchMemory(
        @Valid @RequestBody request: MemorySearchRequest
    ): ResponseEntity<MemorySearchResponse> {
        val results = memoryService.searchMemory(request)
        return ResponseEntity.ok(MemorySearchResponse(results))
    }

    @GetMapping("/documents")
    suspend fun listDocuments(
        @RequestParam(defaultValue = "0") page: Int,
        @RequestParam(defaultValue = "20") size: Int,
        @RequestParam(required = false) search: String?
    ): ResponseEntity<PagedResponse<MemoryDocumentResponse>> {
        val documents = memoryService.listDocuments(page, size, search)
        return ResponseEntity.ok(documents)
    }

    @DeleteMapping("/documents/{id}")
    suspend fun deleteDocument(@PathVariable id: UUID): ResponseEntity<Void> {
        memoryService.deleteDocument(id)
        return ResponseEntity.noContent().build()
    }

    @GetMapping("/health")
    suspend fun healthCheck(): ResponseEntity<HealthResponse> {
        val health = memoryService.getSystemHealth()
        return ResponseEntity.ok(health)
    }
}
```

## Performance Considerations

### Database Optimizations

#### PostgreSQL Indexes
```sql
-- Primary performance indexes
CREATE INDEX idx_memory_chunks_document_id ON memory_chunks(document_id);
CREATE INDEX idx_memory_chunks_content_hash ON memory_chunks(content_hash);
CREATE INDEX idx_chunk_embeddings_model ON chunk_embeddings(model_name);
CREATE INDEX idx_memory_documents_created_at ON memory_documents(created_at DESC);
CREATE INDEX idx_memory_documents_content_type ON memory_documents(content_type);

-- Full-text search indexes
CREATE INDEX idx_memory_documents_title_gin ON memory_documents USING gin(to_tsvector('english', title));
CREATE INDEX idx_memory_chunks_content_gin ON memory_chunks USING gin(to_tsvector('english', content));

-- JSONB metadata indexes
CREATE INDEX idx_memory_documents_metadata_gin ON memory_documents USING gin(metadata);
CREATE INDEX idx_memory_chunks_metadata_gin ON memory_chunks USING gin(metadata);

-- Vector similarity optimization (requires pgvector extension)
CREATE EXTENSION IF NOT EXISTS vector;
ALTER TABLE chunk_embeddings ADD COLUMN embedding_vector_pgv vector(384);
CREATE INDEX idx_chunk_embeddings_vector_cosine
    ON chunk_embeddings USING ivfflat (embedding_vector_pgv vector_cosine_ops)
    WITH (lists = 100);
```

#### Connection Pooling
```yaml
spring:
  datasource:
    hikari:
      maximum-pool-size: 20
      minimum-idle: 5
      idle-timeout: 300000
      connection-timeout: 20000
      validation-timeout: 5000
      leak-detection-threshold: 60000
```

### Elasticsearch Optimizations

#### Index Settings
```json
{
  "settings": {
    "number_of_shards": 1,
    "number_of_replicas": 1,
    "refresh_interval": "30s",
    "index": {
      "mapping": {
        "total_fields": {
          "limit": 2000
        }
      },
      "max_result_window": 50000
    }
  },
  "mappings": {
    "properties": {
      "embedding_vector": {
        "type": "dense_vector",
        "dims": 384,
        "index": true,
        "similarity": "cosine"
      },
      "content": {
        "type": "text",
        "analyzer": "english",
        "fields": {
          "keyword": {
            "type": "keyword",
            "ignore_above": 256
          }
        }
      }
    }
  }
}
```

### Caching Strategy

#### Multi-Level Caching
```kotlin
@Configuration
@EnableCaching
class CacheConfiguration {

    @Bean
    fun cacheManager(): CacheManager {
        return CaffeineCacheManager().apply {
            setCaffeine(
                Caffeine.newBuilder()
                    .maximumSize(10000)
                    .expireAfterWrite(Duration.ofHours(1))
                    .recordStats()
            )
        }
    }

    @Bean("embeddingCache")
    fun embeddingCache(): Cache<String, FloatArray> {
        return Caffeine.newBuilder()
            .maximumSize(50000)
            .expireAfterWrite(Duration.ofHours(24))
            .build()
    }

    @Bean("searchCache")
    fun searchCache(): Cache<String, List<MemorySearchResult>> {
        return Caffeine.newBuilder()
            .maximumSize(1000)
            .expireAfterWrite(Duration.ofMinutes(15))
            .build()
    }
}
```

## Implementation Plan

### Phase 1: Foundation (Week 1-2)
1. ✅ **Project Setup**
   - Initialize Kotlin/Spring Boot project
   - Configure PostgreSQL and Elasticsearch connections
   - Set up basic project structure and dependencies

2. **Database Schema**
   - Create PostgreSQL migration scripts
   - Set up Flyway for database migrations
   - Create basic entity classes and repositories

3. **Basic Services**
   - Implement text chunking service
   - Set up embedding service with all-MiniLM-L6-v2
   - Create basic document ingestion

### Phase 2: Core Functionality (Week 3-4)
1. **Search Implementation**
   - Implement vector search in Elasticsearch
   - Add keyword search capabilities
   - Develop hybrid search with RRF

2. **API Development**
   - Create REST controllers and DTOs
   - Add input validation and error handling
   - Implement pagination and filtering

### Phase 3: Optimization (Week 5-6)
1. **Performance Tuning**
   - Add database indexes and query optimization
   - Implement multi-level caching
   - Add async processing for embeddings

2. **Testing & Quality**
   - Create comprehensive test suite
   - Add integration tests with Testcontainers
   - Performance testing and optimization

### Phase 4: Production Ready (Week 7-8)
1. **Monitoring & Operations**
   - Add metrics and health checks
   - Implement logging and observability
   - Create deployment configurations

2. **Documentation & Polish**
   - API documentation with OpenAPI
   - Operation runbooks
   - Performance benchmarks

This design provides a robust, scalable foundation for the leader-toolbox memory system while maintaining clean architecture and strong performance characteristics.