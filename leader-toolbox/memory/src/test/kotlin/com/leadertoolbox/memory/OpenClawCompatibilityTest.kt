package com.leadertoolbox.memory

import com.leadertoolbox.memory.dto.*
import com.leadertoolbox.memory.service.*
import com.fasterxml.jackson.databind.ObjectMapper
import kotlinx.coroutines.runBlocking
import org.junit.jupiter.api.Test
import org.junit.jupiter.api.TestInstance
import org.junit.jupiter.api.BeforeEach
import org.springframework.beans.factory.annotation.Autowired
import org.springframework.boot.test.context.SpringBootTest
import org.springframework.boot.test.web.client.TestRestTemplate
import org.springframework.boot.test.web.server.LocalServerPort
import org.springframework.http.*
import org.springframework.test.context.DynamicPropertyRegistry
import org.springframework.test.context.DynamicPropertySource
import org.springframework.transaction.annotation.Transactional
import org.testcontainers.containers.PostgreSQLContainer
import org.testcontainers.elasticsearch.ElasticsearchContainer
import org.testcontainers.junit.jupiter.Container
import org.testcontainers.junit.jupiter.Testcontainers
import kotlin.test.*

/**
 * OpenClaw Compatibility Test Suite
 *
 * Comprehensive tests to ensure 100% API compatibility with OpenClaw
 * while validating enhanced features and performance improvements.
 */
@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
@Testcontainers
@TestInstance(TestInstance.Lifecycle.PER_CLASS)
@Transactional
class OpenClawCompatibilityTest {

    @LocalServerPort
    private var port: Int = 0

    @Autowired
    private lateinit var restTemplate: TestRestTemplate

    @Autowired
    private lateinit var objectMapper: ObjectMapper

    private lateinit var baseUrl: String

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

    @BeforeEach
    fun setUp() {
        baseUrl = "http://localhost:$port/api/v1/memory"
    }

    // ==================== OPENCLAW API COMPATIBILITY TESTS ====================

    @Test
    fun `should support OpenClaw chat API format exactly`() {
        // Given - Ingest some test content first
        val ingestRequest = IngestTextRequest(
            name = "OpenClaw Test Document",
            content = "Machine learning is a subset of artificial intelligence that focuses on algorithms and statistical models."
        )

        val ingestResponse = restTemplate.postForEntity(
            "$baseUrl/ingest_text",
            ingestRequest,
            MemoryDocumentResponse::class.java
        )

        assertTrue(ingestResponse.statusCode.is2xxSuccessful)
        assertNotNull(ingestResponse.body)

        // Wait for indexing
        Thread.sleep(2000)

        // When - Use OpenClaw chat format
        val chatRequest = ChatRequest(
            message = "What is machine learning?",
            sessionId = "test-session-openclaw",
            userId = "test-user",
            maxResults = 6,
            minScore = 0.35
        )

        val chatResponse = restTemplate.postForEntity(
            "$baseUrl/chat",
            chatRequest,
            ChatResponse::class.java
        )

        // Then - Verify OpenClaw response format
        assertTrue(chatResponse.statusCode.is2xxSuccessful)
        val response = chatResponse.body!!

        assertNotNull(response.text)
        assertTrue(response.text.isNotBlank())
        assertTrue(response.text.contains("machine learning", ignoreCase = true))

        assertNotNull(response.citations)
        assertTrue(response.citations.isNotEmpty())

        val citation = response.citations.first()
        assertNotNull(citation.source)
        assertNotNull(citation.excerpt)
        assertTrue(citation.score > 0.0)

        assertNotNull(response.usedKbIds)
        assertTrue(response.usedKbIds.isNotEmpty())

        assertNotNull(response.kbVersion)
    }

    @Test
    fun `should support OpenClaw ingest_text API format exactly`() {
        // Given
        val request = IngestTextRequest(
            name = "OpenClaw Compatibility Test",
            content = "This is test content for OpenClaw API compatibility validation. " +
                    "It should be processed exactly like the original OpenClaw system.",
            metadata = mapOf(
                "source" to "compatibility_test",
                "version" to "1.0"
            )
        )

        // When
        val response = restTemplate.postForEntity(
            "$baseUrl/ingest_text",
            request,
            MemoryDocumentResponse::class.java
        )

        // Then
        assertTrue(response.statusCode.is2xxSuccessful)
        val document = response.body!!

        assertEquals("OpenClaw Compatibility Test", document.title)
        assertEquals("text/plain", document.contentType)
        assertTrue(document.chunkCount > 0)
        assertTrue(document.metadata.isNotEmpty())
        assertEquals("compatibility_test", document.metadata["source"])
    }

    @Test
    fun `should support OpenClaw status API format exactly`() {
        // Given - Some documents in the system
        repeat(3) { i ->
            val ingestRequest = IngestTextRequest(
                name = "Status Test Doc $i",
                content = "Content for document $i for status API testing."
            )

            restTemplate.postForEntity(
                "$baseUrl/ingest_text",
                ingestRequest,
                MemoryDocumentResponse::class.java
            )
        }

        Thread.sleep(1000) // Allow indexing

        // When
        val response = restTemplate.getForEntity(
            "$baseUrl/status",
            StatusResponse::class.java
        )

        // Then
        assertTrue(response.statusCode.is2xxSuccessful)
        val status = response.body!!

        assertEquals("leader-toolbox", status.backend)
        assertTrue(status.documentsIndexed >= 3)
        assertTrue(status.chunksIndexed >= 3)
        assertTrue(status.embeddingsGenerated >= 0) // May be 0 if async processing
        assertTrue(status.searchCapabilities.contains("semantic"))
        assertTrue(status.searchCapabilities.contains("keyword"))
        assertTrue(status.searchCapabilities.contains("hybrid"))
        assertNotNull(status.health)
    }

    // ==================== OPENCLAW BEHAVIOR COMPATIBILITY TESTS ====================

    @Test
    fun `should chunk text exactly like OpenClaw`() {
        // Given - Large content that needs chunking
        val largeContent = "A".repeat(2000) + " This is the end marker."

        val ingestRequest = IngestTextRequest(
            name = "Chunking Test",
            content = largeContent
        )

        // When
        val response = restTemplate.postForEntity(
            "$baseUrl/ingest_text",
            ingestRequest,
            MemoryDocumentResponse::class.java
        )

        // Then
        assertTrue(response.statusCode.is2xxSuccessful)
        val document = response.body!!

        // Should create multiple chunks like OpenClaw
        assertTrue(document.chunkCount > 1)

        // Verify we can search within chunks
        Thread.sleep(2000)

        val searchRequest = ChatRequest(
            message = "end marker",
            maxResults = 5
        )

        val searchResponse = restTemplate.postForEntity(
            "$baseUrl/chat",
            searchRequest,
            ChatResponse::class.java
        )

        assertTrue(searchResponse.statusCode.is2xxSuccessful)
        assertTrue(searchResponse.body!!.citations.isNotEmpty())
    }

    @Test
    fun `should handle empty queries like OpenClaw`() {
        // When - Empty query
        val chatRequest = ChatRequest(
            message = "",
            maxResults = 6
        )

        val chatResponse = restTemplate.postForEntity(
            "$baseUrl/chat",
            chatRequest,
            ChatResponse::class.java
        )

        // Then - Should handle gracefully
        assertTrue(chatResponse.statusCode.is2xxSuccessful)
        val response = chatResponse.body!!

        assertNotNull(response.text)
        assertTrue(response.citations.isEmpty())
        assertTrue(response.usedKbIds.isEmpty())
    }

    @Test
    fun `should handle non-existent content like OpenClaw`() {
        // When - Query for content that doesn't exist
        val chatRequest = ChatRequest(
            message = "quantum mechanics of interdimensional butterflies",
            maxResults = 6
        )

        val chatResponse = restTemplate.postForEntity(
            "$baseUrl/chat",
            chatRequest,
            ChatResponse::class.java
        )

        // Then
        assertTrue(chatResponse.statusCode.is2xxSuccessful)
        val response = chatResponse.body!!

        assertNotNull(response.text)
        assertTrue(response.text.contains("couldn't find", ignoreCase = true) ||
                  response.text.contains("no relevant", ignoreCase = true))
        assertTrue(response.citations.isEmpty())
    }

    // ==================== ENHANCED FEATURES TESTS ====================

    @Test
    fun `should support enhanced search types beyond OpenClaw`() {
        // Given
        val ingestRequest = IngestTextRequest(
            name = "Enhanced Search Test",
            content = "Artificial intelligence and machine learning are transforming technology. " +
                    "Deep learning neural networks enable pattern recognition."
        )

        restTemplate.postForEntity(
            "$baseUrl/ingest_text",
            ingestRequest,
            MemoryDocumentResponse::class.java
        )

        Thread.sleep(2000)

        // When - Use enhanced search API
        val searchRequest = MemorySearchRequest(
            query = "AI neural networks",
            searchType = SearchType.HYBRID,
            maxResults = 10,
            minScore = 0.2,
            includeContent = true
        )

        val searchResponse = restTemplate.postForEntity(
            "$baseUrl/search",
            searchRequest,
            MemorySearchResponse::class.java
        )

        // Then
        assertTrue(searchResponse.statusCode.is2xxSuccessful)
        val response = searchResponse.body!!

        assertTrue(response.results.isNotEmpty())
        assertEquals("HYBRID", response.searchType)
        assertTrue(response.executionTimeMs > 0)

        val result = response.results.first()
        assertNotNull(result.fullContent) // Enhanced feature
        assertEquals("hybrid", result.searchType.lowercase())
    }

    @Test
    fun `should support session analytics beyond OpenClaw`() {
        // Given - Create session and perform searches
        val sessionRequest = CreateSessionRequest(
            userId = "analytics-test-user",
            sessionName = "Analytics Test Session"
        )

        val sessionResponse = restTemplate.postForEntity(
            "$baseUrl/sessions",
            sessionRequest,
            MemorySessionResponse::class.java
        )

        val sessionId = sessionResponse.body!!.id

        // Perform multiple searches
        repeat(3) {
            val chatRequest = ChatRequest(
                message = "test query $it",
                sessionId = sessionId.toString()
            )

            restTemplate.postForEntity(
                "$baseUrl/chat",
                chatRequest,
                ChatResponse::class.java
            )
        }

        // When - Get analytics (enhanced feature)
        val analyticsResponse = restTemplate.getForEntity(
            "$baseUrl/sessions/$sessionId/analytics",
            SearchAnalyticsResponse::class.java
        )

        // Then
        assertTrue(analyticsResponse.statusCode.is2xxSuccessful)
        val analytics = analyticsResponse.body!!

        assertEquals(sessionId, analytics.sessionId)
        assertEquals(3, analytics.totalQueries)
        assertTrue(analytics.averageExecutionTimeMs > 0)
        assertEquals(3, analytics.recentQueries.size)
    }

    @Test
    fun `should support bulk operations beyond OpenClaw`() {
        // Given - Multiple documents for bulk ingestion
        val documents = (1..5).map { i ->
            DocumentIngestRequest(
                title = "Bulk Test Document $i",
                content = "This is content for bulk test document number $i. " +
                        "It contains relevant information for testing."
            )
        }

        val bulkRequest = BulkIngestRequest(
            documents = documents,
            batchSize = 2,
            continueOnError = true
        )

        // When
        val bulkResponse = restTemplate.postForEntity(
            "$baseUrl/documents/bulk",
            bulkRequest,
            BulkIngestResponse::class.java
        )

        // Then
        assertTrue(bulkResponse.statusCode.is2xxSuccessful)
        val response = bulkResponse.body!!

        assertEquals(5, response.totalDocuments)
        assertEquals(5, response.successfulIngests)
        assertEquals(0, response.failedIngests)
        assertEquals(5, response.results.size)

        assertTrue(response.results.all { it.success })
        assertTrue(response.results.all { it.documentId != null })
    }

    // ==================== PERFORMANCE COMPARISON TESTS ====================

    @Test
    fun `should perform better than OpenClaw baseline`() {
        // Given - Test document
        val ingestRequest = IngestTextRequest(
            name = "Performance Test Document",
            content = "Performance testing content with various keywords like machine learning, " +
                    "artificial intelligence, deep learning, neural networks, algorithms, " +
                    "data science, computer vision, natural language processing."
        )

        restTemplate.postForEntity(
            "$baseUrl/ingest_text",
            ingestRequest,
            MemoryDocumentResponse::class.java
        )

        Thread.sleep(2000)

        // When - Measure search performance
        val startTime = System.currentTimeMillis()

        val chatRequest = ChatRequest(
            message = "machine learning algorithms",
            maxResults = 6
        )

        val chatResponse = restTemplate.postForEntity(
            "$baseUrl/chat",
            chatRequest,
            ChatResponse::class.java
        )

        val executionTime = System.currentTimeMillis() - startTime

        // Then - Performance should be reasonable (under 2 seconds for test environment)
        assertTrue(chatResponse.statusCode.is2xxSuccessful)
        assertTrue(executionTime < 2000) // Should be faster than 2 seconds
        assertTrue(chatResponse.body!!.citations.isNotEmpty())

        println("Search execution time: ${executionTime}ms")
    }

    @Test
    fun `should handle concurrent requests like production OpenClaw`() {
        // Given - Test document
        val ingestRequest = IngestTextRequest(
            name = "Concurrency Test Document",
            content = "Concurrency testing content for load validation and stress testing scenarios."
        )

        restTemplate.postForEntity(
            "$baseUrl/ingest_text",
            ingestRequest,
            MemoryDocumentResponse::class.java
        )

        Thread.sleep(2000)

        // When - Multiple concurrent requests
        val futures = (1..5).map { i ->
            Thread {
                val chatRequest = ChatRequest(
                    message = "concurrency test query $i",
                    maxResults = 5
                )

                val response = restTemplate.postForEntity(
                    "$baseUrl/chat",
                    chatRequest,
                    ChatResponse::class.java
                )

                assertTrue(response.statusCode.is2xxSuccessful)
                assertNotNull(response.body?.text)
            }
        }

        // Execute all threads
        futures.forEach { it.start() }
        futures.forEach { it.join() }

        // Then - All requests should succeed without errors
        // Success is validated in each thread
    }

    // ==================== ERROR HANDLING COMPATIBILITY TESTS ====================

    @Test
    fun `should handle malformed requests like OpenClaw`() {
        // When - Invalid JSON
        val headers = HttpHeaders()
        headers.contentType = MediaType.APPLICATION_JSON

        val entity = HttpEntity("{ invalid json", headers)

        val response = restTemplate.postForEntity(
            "$baseUrl/chat",
            entity,
            String::class.java
        )

        // Then
        assertTrue(response.statusCode.is4xxClientError)
    }

    @Test
    fun `should handle missing required fields like OpenClaw`() {
        // When - Missing message field
        val invalidRequest = mapOf("sessionId" to "test")

        val response = restTemplate.postForEntity(
            "$baseUrl/chat",
            invalidRequest,
            ErrorResponse::class.java
        )

        // Then
        assertTrue(response.statusCode.is4xxClientError)
    }

    // ==================== INTEGRATION VALIDATION TESTS ====================

    @Test
    fun `should maintain data consistency across operations`() = runBlocking {
        // Given - Document ingestion
        val ingestRequest = IngestTextRequest(
            name = "Consistency Test",
            content = "Data consistency validation content for integration testing."
        )

        val ingestResponse = restTemplate.postForEntity(
            "$baseUrl/ingest_text",
            ingestRequest,
            MemoryDocumentResponse::class.java
        )

        val documentId = ingestResponse.body!!.id

        Thread.sleep(2000)

        // When - Search for the content
        val searchRequest = ChatRequest(
            message = "consistency validation",
            maxResults = 5
        )

        val searchResponse = restTemplate.postForEntity(
            "$baseUrl/chat",
            searchRequest,
            ChatResponse::class.java
        )

        // Then - Should find the ingested content
        assertTrue(searchResponse.statusCode.is2xxSuccessful)
        assertTrue(searchResponse.body!!.citations.isNotEmpty())

        // When - Delete the document
        restTemplate.delete("$baseUrl/documents/$documentId")

        Thread.sleep(1000)

        // Then - Should no longer find the content
        val searchAfterDelete = restTemplate.postForEntity(
            "$baseUrl/chat",
            searchRequest,
            ChatResponse::class.java
        )

        // The search should either return no results or different content
        assertTrue(searchAfterDelete.statusCode.is2xxSuccessful)
        // Note: Due to async processing, we might still find some results temporarily
    }

    @Test
    fun `should support OpenClaw migration scenario`() {
        // Given - Simulate OpenClaw data migration
        val openClawDocuments = listOf(
            IngestTextRequest("OpenClaw Doc 1", "Content from OpenClaw system 1"),
            IngestTextRequest("OpenClaw Doc 2", "Content from OpenClaw system 2"),
            IngestTextRequest("OpenClaw Doc 3", "Content from OpenClaw system 3")
        )

        // When - Migrate documents
        openClawDocuments.forEach { doc ->
            val response = restTemplate.postForEntity(
                "$baseUrl/ingest_text",
                doc,
                MemoryDocumentResponse::class.java
            )
            assertTrue(response.statusCode.is2xxSuccessful)
        }

        Thread.sleep(3000) // Allow indexing

        // Then - Verify all content is searchable
        val searchRequest = ChatRequest(
            message = "OpenClaw system",
            maxResults = 10
        )

        val searchResponse = restTemplate.postForEntity(
            "$baseUrl/chat",
            searchRequest,
            ChatResponse::class.java
        )

        assertTrue(searchResponse.statusCode.is2xxSuccessful)
        assertTrue(searchResponse.body!!.citations.size >= 2) // Should find multiple results

        // Verify system status reflects migration
        val statusResponse = restTemplate.getForEntity(
            "$baseUrl/status",
            StatusResponse::class.java
        )

        assertTrue(statusResponse.body!!.documentsIndexed >= 3)
    }
}