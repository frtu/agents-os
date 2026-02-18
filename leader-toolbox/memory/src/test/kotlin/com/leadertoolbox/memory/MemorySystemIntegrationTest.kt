package com.leadertoolbox.memory

import com.leadertoolbox.memory.dto.*
import com.leadertoolbox.memory.model.*
import com.leadertoolbox.memory.service.*
import kotlinx.coroutines.runBlocking
import org.junit.jupiter.api.Test
import org.junit.jupiter.api.TestInstance
import org.springframework.beans.factory.annotation.Autowired
import org.springframework.boot.test.context.SpringBootTest
import org.springframework.test.context.DynamicPropertyRegistry
import org.springframework.test.context.DynamicPropertySource
import org.springframework.transaction.annotation.Transactional
import org.testcontainers.containers.PostgreSQLContainer
import org.testcontainers.elasticsearch.ElasticsearchContainer
import org.testcontainers.junit.jupiter.Container
import org.testcontainers.junit.jupiter.Testcontainers
import kotlin.test.*

/**
 * Integration Test for Memory System
 *
 * Tests the complete memory system including:
 * - Document ingestion and chunking
 * - Embedding generation (using fallback local embeddings)
 * - Vector and hybrid search
 * - PostgreSQL persistence
 * - Session management
 * - Analytics tracking
 */
@SpringBootTest
@Testcontainers
@TestInstance(TestInstance.Lifecycle.PER_CLASS)
@Transactional
class MemorySystemIntegrationTest {

    @Autowired
    private lateinit var memoryService: MemoryService

    @Autowired
    private lateinit var embeddingService: EmbeddingService

    companion object {
        @Container
        @JvmStatic
        val postgres = PostgreSQLContainer("postgres:15")
            .withDatabaseName("memory_test")
            .withUsername("test")
            .withPassword("test")

        @Container
        @JvmStatic
        val elasticsearch = ElasticsearchContainer("docker.elastic.co/elasticsearch/elasticsearch:8.11.1")
            .withEnv("discovery.type", "single-node")
            .withEnv("xpack.security.enabled", "false")
            .withEnv("ES_JAVA_OPTS", "-Xms512m -Xmx512m")

        @JvmStatic
        @DynamicPropertySource
        fun configureProperties(registry: DynamicPropertyRegistry) {
            registry.add("spring.datasource.url") { postgres.jdbcUrl }
            registry.add("spring.datasource.username") { postgres.username }
            registry.add("spring.datasource.password") { postgres.password }
            registry.add("spring.elasticsearch.uris") { elasticsearch.httpHostAddress }
        }
    }

    @Test
    fun `should ingest document and create chunks`() = runBlocking {
        // Given
        val request = DocumentIngestRequest(
            title = "Test Document",
            content = "This is a test document with multiple sentences. " +
                    "It should be split into chunks during ingestion. " +
                    "Each chunk should have its own embedding vector for semantic search.",
            contentType = "text/plain",
            sourcePath = "/test/document.txt",
            metadata = mapOf("category" to "test", "priority" to "high"),
            chunkSize = 100,
            chunkOverlap = 20
        )

        // When
        val response = memoryService.ingestDocument(request)

        // Then
        assertNotNull(response)
        assertEquals("Test Document", response.title)
        assertEquals("text/plain", response.contentType)
        assertEquals("/test/document.txt", response.sourcePath)
        assertTrue(response.chunkCount > 1) // Should be split into multiple chunks
    }

    @Test
    fun `should generate embeddings for text`() = runBlocking {
        // Given
        val text = "This is a test sentence for embedding generation."

        // When
        val embedding = embeddingService.generateEmbedding(text)

        // Then
        assertEquals(384, embedding.size) // all-MiniLM-L6-v2 dimension
        assertTrue(embedding.all { it.isFinite() })
        assertTrue(embeddingService.validateEmbedding(embedding))

        // Verify embedding statistics
        val stats = embeddingService.getEmbeddingStats(embedding)
        assertEquals(384, stats.dimension)
        assertTrue(stats.magnitude > 0)
    }

    @Test
    fun `should calculate cosine similarity correctly`() = runBlocking {
        // Given
        val text1 = "The cat sits on the mat"
        val text2 = "A cat is sitting on the mat"
        val text3 = "The dog runs in the park"

        // When
        val embedding1 = embeddingService.generateEmbedding(text1)
        val embedding2 = embeddingService.generateEmbedding(text2)
        val embedding3 = embeddingService.generateEmbedding(text3)

        val similarity12 = embeddingService.cosineSimilarity(embedding1, embedding2)
        val similarity13 = embeddingService.cosineSimilarity(embedding1, embedding3)

        // Then
        assertTrue(similarity12 > similarity13) // Similar texts should have higher similarity
        assertTrue(similarity12 > 0.0f)
        assertTrue(similarity13 >= 0.0f)
    }

    @Test
    fun `should perform semantic search`() = runBlocking {
        // Given - Ingest a document first
        val document = DocumentIngestRequest(
            title = "Programming Guide",
            content = "Python is a programming language. " +
                    "JavaScript is used for web development. " +
                    "Kotlin is great for Android development. " +
                    "Machine learning uses data science techniques.",
            chunkSize = 80,
            chunkOverlap = 10
        )
        memoryService.ingestDocument(document)

        // Wait a moment for async processing
        kotlinx.coroutines.delay(2000)

        // When - Search for programming languages
        val searchRequest = MemorySearchRequest(
            query = "programming languages",
            searchType = SearchType.SEMANTIC,
            maxResults = 5,
            minScore = 0.0
        )
        val results = memoryService.searchMemory(searchRequest)

        // Then
        assertNotNull(results)
        assertTrue(results.results.isNotEmpty())
        assertEquals("SEMANTIC", results.searchType)
        assertTrue(results.executionTimeMs > 0)

        // Verify result structure
        results.results.forEach { result ->
            assertNotNull(result.chunkId)
            assertNotNull(result.documentId)
            assertNotNull(result.excerpt)
            assertTrue(result.score >= 0.0)
        }
    }

    @Test
    fun `should perform hybrid search`() = runBlocking {
        // Given
        val document = DocumentIngestRequest(
            title = "Technology Overview",
            content = "Artificial intelligence and machine learning are transforming industries. " +
                    "Deep learning models use neural networks for pattern recognition. " +
                    "Natural language processing enables computers to understand text. " +
                    "Computer vision allows machines to interpret visual information.",
            chunkSize = 100,
            chunkOverlap = 20
        )
        memoryService.ingestDocument(document)

        kotlinx.coroutines.delay(2000)

        // When - Hybrid search combining semantic and keyword matching
        val searchRequest = MemorySearchRequest(
            query = "neural networks deep learning",
            searchType = SearchType.HYBRID,
            maxResults = 3
        )
        val results = memoryService.searchMemory(searchRequest)

        // Then
        assertNotNull(results)
        assertEquals("HYBRID", results.searchType)

        // Should find relevant content
        val hasRelevantContent = results.results.any { result ->
            result.excerpt.contains("neural", ignoreCase = true) ||
                    result.excerpt.contains("deep", ignoreCase = true)
        }
        assertTrue(hasRelevantContent)
    }

    @Test
    fun `should manage sessions and context`() = runBlocking {
        // Given
        val sessionRequest = CreateSessionRequest(
            userId = "test-user",
            sessionName = "Test Session",
            contextData = mapOf("preference" to "technical", "language" to "en")
        )

        // When
        val session = memoryService.createSession(sessionRequest)

        // Then
        assertNotNull(session)
        assertEquals("test-user", session.userId)
        assertEquals("Test Session", session.sessionName)
        assertEquals(2, session.contextData.size)

        // Update context
        val updatedSession = memoryService.updateSessionContext(
            session.id,
            mapOf("lastQuery" to "test query", "resultCount" to 5)
        )

        assertEquals(4, updatedSession.contextData.size) // Original + new context
    }

    @Test
    fun `should track search analytics`() = runBlocking {
        // Given - Create session and perform searches
        val session = memoryService.createSession(
            CreateSessionRequest(userId = "analytics-test", sessionName = "Analytics Test")
        )

        val document = DocumentIngestRequest(
            title = "Analytics Test Document",
            content = "This document is used for testing search analytics and performance tracking."
        )
        memoryService.ingestDocument(document)

        kotlinx.coroutines.delay(1000)

        // Perform multiple searches
        repeat(3) { i ->
            val searchRequest = MemorySearchRequest(
                query = "analytics test query $i",
                sessionId = session.id,
                searchType = SearchType.HYBRID
            )
            memoryService.searchMemory(searchRequest)
        }

        // When
        val analytics = memoryService.getSessionAnalytics(session.id)

        // Then
        assertNotNull(analytics)
        assertEquals(session.id, analytics.sessionId)
        assertEquals(3, analytics.totalQueries)
        assertTrue(analytics.averageExecutionTimeMs > 0)
        assertEquals("HYBRID", analytics.mostCommonQueryType)
        assertEquals(3, analytics.recentQueries.size)
    }

    @Test
    fun `should handle document listing and filtering`() = runBlocking {
        // Given - Create multiple documents
        val documents = listOf(
            DocumentIngestRequest(title = "First Document", content = "Content of first document"),
            DocumentIngestRequest(title = "Second Document", content = "Content of second document"),
            DocumentIngestRequest(title = "Important Document", content = "Important content here")
        )

        documents.forEach { memoryService.ingestDocument(it) }

        // When - List all documents
        val allDocs = memoryService.listDocuments(page = 0, size = 10)

        // Then
        assertTrue(allDocs.content.size >= 3)
        assertTrue(allDocs.totalElements >= 3)

        // When - Search for specific document
        val filteredDocs = memoryService.listDocuments(page = 0, size = 10, search = "Important")

        // Then
        assertTrue(filteredDocs.content.isNotEmpty())
        assertTrue(filteredDocs.content.any { it.title.contains("Important") })
    }

    @Test
    fun `should provide system health status`(): Unit = runBlocking {
        // Given - System with some data
        memoryService.ingestDocument(
            DocumentIngestRequest(title = "Health Test", content = "Testing system health")
        )

        // When
        val health = memoryService.getSystemHealth()

        // Then
        assertNotNull(health)
        assertTrue(health.documentCount > 0)
        assertTrue(health.chunkCount > 0)
        assertNotNull(health.status)
        assertNotNull(health.timestamp)
    }

    @Test
    fun `should handle document deletion`() = runBlocking {
        // Given
        val document = memoryService.ingestDocument(
            DocumentIngestRequest(title = "Delete Test", content = "This will be deleted")
        )

        // Verify document exists
        val retrievedDoc = memoryService.getDocument(document.id)
        assertNotNull(retrievedDoc)

        // When
        memoryService.deleteDocument(document.id)

        // Then
        val deletedDoc = memoryService.getDocument(document.id)
        assertNull(deletedDoc) // Should not be found after soft delete
    }

    @Test
    fun `should handle duplicate content detection`() = runBlocking {
        // Given - Same content, different title
        val content = "This is duplicate content for testing purposes."

        val request1 = DocumentIngestRequest(title = "First Copy", content = content)
        val request2 = DocumentIngestRequest(title = "Second Copy", content = content)

        // When
        val doc1 = memoryService.ingestDocument(request1)
        val doc2 = memoryService.ingestDocument(request2)

        // Then
        assertNotNull(doc1)
        assertNotNull(doc2)

        // Should detect duplicate (implementation may vary)
        // This test verifies the system can handle duplicates gracefully
        assertTrue(doc1.contentHash.isNotEmpty())
        assertEquals(doc1.contentHash, doc2.contentHash) // Same content hash
    }

    @Test
    fun `should handle edge cases and validation`() = runBlocking {
        // Test empty content
        assertFailsWith<IllegalArgumentException> {
            memoryService.ingestDocument(
                DocumentIngestRequest(title = "Empty", content = "")
            )
        }

        // Test very long title
        val longTitle = "A".repeat(600) // Exceeds max length
        val documentWithLongTitle = DocumentIngestRequest(
            title = longTitle,
            content = "Some content"
        )

        // Should handle gracefully (truncate title)
        val result = memoryService.ingestDocument(documentWithLongTitle)
        assertTrue(result.title.length <= 500) // Should be truncated

        // Test search with empty query
        val emptySearchResult = memoryService.searchMemory(
            MemorySearchRequest(query = "", maxResults = 1)
        )
        assertNotNull(emptySearchResult)
        assertEquals(0, emptySearchResult.results.size)
    }
}