package com.leadertoolbox.memory.controller

import com.leadertoolbox.memory.dto.*
import com.leadertoolbox.memory.service.MemoryService
import com.leadertoolbox.memory.service.MemorySearchService
import jakarta.validation.Valid
import org.slf4j.LoggerFactory
import org.springframework.http.HttpStatus
import org.springframework.http.ResponseEntity
import org.springframework.validation.annotation.Validated
import org.springframework.web.bind.annotation.*
import java.time.OffsetDateTime
import java.util.*

/**
 * Memory System REST Controller
 *
 * Provides both new APIs and OpenClaw-compatible endpoints for:
 * - Document ingestion and management
 * - Memory search (semantic, keyword, hybrid)
 * - Session management
 * - System health and analytics
 */
@RestController
@RequestMapping("/api/v1/memory")
@Validated
@CrossOrigin(origins = ["\${cors.allowed-origins}"])
class MemoryController(
    private val memoryService: MemoryService,
    private val searchService: MemorySearchService
) {
    private val logger = LoggerFactory.getLogger(MemoryController::class.java)

    // ==================== DOCUMENT MANAGEMENT ====================

    @PostMapping("/documents")
    suspend fun ingestDocument(
        @Valid @RequestBody request: DocumentIngestRequest
    ): ResponseEntity<MemoryDocumentResponse> {
        logger.info("Ingesting document: ${request.title}")
        val document = memoryService.ingestDocument(request)
        return ResponseEntity.ok(document)
    }

    @GetMapping("/documents")
    suspend fun listDocuments(
        @RequestParam(defaultValue = "0") page: Int,
        @RequestParam(defaultValue = "20") size: Int,
        @RequestParam(required = false) search: String?,
        @RequestParam(defaultValue = "createdAt") sortBy: String,
        @RequestParam(defaultValue = "DESC") sortDirection: String
    ): ResponseEntity<PagedResponse<MemoryDocumentResponse>> {
        val documents = memoryService.listDocuments(page, size, search, sortBy, sortDirection)
        return ResponseEntity.ok(documents)
    }

    @GetMapping("/documents/{id}")
    suspend fun getDocument(@PathVariable id: UUID): ResponseEntity<MemoryDocumentResponse> {
        val document = memoryService.getDocument(id)
        return if (document != null) {
            ResponseEntity.ok(document)
        } else {
            ResponseEntity.notFound().build()
        }
    }

    @DeleteMapping("/documents/{id}")
    suspend fun deleteDocument(@PathVariable id: UUID): ResponseEntity<Void> {
        memoryService.deleteDocument(id)
        return ResponseEntity.noContent().build()
    }

    @PostMapping("/documents/bulk")
    suspend fun bulkIngestDocuments(
        @Valid @RequestBody request: BulkIngestRequest
    ): ResponseEntity<BulkIngestResponse> {
        val results = mutableListOf<BulkIngestResult>()
        var successfulIngests = 0
        var failedIngests = 0

        request.documents.forEachIndexed { index, docRequest ->
            try {
                val document = memoryService.ingestDocument(docRequest)
                results.add(
                    BulkIngestResult(
                        index = index,
                        title = docRequest.title,
                        success = true,
                        documentId = document.id
                    )
                )
                successfulIngests++

                // Process in batches to avoid overwhelming the system
                if (index % request.batchSize == 0 && index > 0) {
                    kotlinx.coroutines.delay(100) // Brief pause between batches
                }
            } catch (e: Exception) {
                logger.error("Failed to ingest document at index $index: ${docRequest.title}", e)
                results.add(
                    BulkIngestResult(
                        index = index,
                        title = docRequest.title,
                        success = false,
                        error = e.message ?: "Unknown error"
                    )
                )
                failedIngests++

                if (!request.continueOnError) {
                    throw e
                }
            }
        }

        val response = BulkIngestResponse(
            totalDocuments = request.documents.size,
            successfulIngests = successfulIngests,
            failedIngests = failedIngests,
            results = results
        )

        return ResponseEntity.ok(response)
    }

    // ==================== SEARCH ENDPOINTS ====================

    @PostMapping("/search")
    suspend fun searchMemory(
        @Valid @RequestBody request: MemorySearchRequest
    ): ResponseEntity<MemorySearchResponse> {
        logger.info("Searching memory: ${request.query} (${request.searchType})")
        val results = memoryService.searchMemory(request)
        return ResponseEntity.ok(results)
    }

    @GetMapping("/search/suggestions")
    suspend fun getSearchSuggestions(
        @RequestParam query: String,
        @RequestParam(defaultValue = "5") maxSuggestions: Int
    ): ResponseEntity<List<String>> {
        val suggestions = searchService.getSearchSuggestions(query, maxSuggestions)
        return ResponseEntity.ok(suggestions)
    }

    @GetMapping("/documents/{id}/similar")
    suspend fun findSimilarDocuments(
        @PathVariable id: UUID,
        @RequestParam(defaultValue = "5") maxResults: Int,
        @RequestParam(defaultValue = "0.3") minScore: Double
    ): ResponseEntity<List<MemorySearchResult>> {
        val similarDocuments = searchService.findSimilarDocuments(id, maxResults, minScore)
        return ResponseEntity.ok(similarDocuments)
    }

    // ==================== CHUNK MANAGEMENT ====================

    @GetMapping("/chunks/{id}")
    suspend fun getChunk(@PathVariable id: UUID): ResponseEntity<ChunkDetailResponse> {
        val chunk = memoryService.getChunk(id)
        return if (chunk != null) {
            ResponseEntity.ok(chunk)
        } else {
            ResponseEntity.notFound().build()
        }
    }

    // ==================== SESSION MANAGEMENT ====================

    @PostMapping("/sessions")
    suspend fun createSession(
        @Valid @RequestBody request: CreateSessionRequest
    ): ResponseEntity<MemorySessionResponse> {
        val session = memoryService.createSession(request)
        return ResponseEntity.ok(session)
    }

    @GetMapping("/sessions/{id}")
    suspend fun getSession(@PathVariable id: UUID): ResponseEntity<MemorySessionResponse> {
        val session = memoryService.getSession(id)
        return if (session != null) {
            ResponseEntity.ok(session)
        } else {
            ResponseEntity.notFound().build()
        }
    }

    @PutMapping("/sessions/{id}/context")
    suspend fun updateSessionContext(
        @PathVariable id: UUID,
        @Valid @RequestBody request: UpdateSessionContextRequest
    ): ResponseEntity<MemorySessionResponse> {
        val session = memoryService.updateSessionContext(id, request.contextData)
        return ResponseEntity.ok(session)
    }

    @GetMapping("/sessions/{id}/analytics")
    suspend fun getSessionAnalytics(@PathVariable id: UUID): ResponseEntity<SearchAnalyticsResponse> {
        val analytics = memoryService.getSessionAnalytics(id)
        return ResponseEntity.ok(analytics)
    }

    // ==================== SYSTEM HEALTH & ANALYTICS ====================

    @GetMapping("/health")
    suspend fun getSystemHealth(): ResponseEntity<HealthResponse> {
        val health = memoryService.getSystemHealth()
        return ResponseEntity.ok(health)
    }

    @GetMapping("/statistics")
    suspend fun getSearchStatistics(): ResponseEntity<Map<String, Any>> {
        val statistics = searchService.getSearchStatistics()
        return ResponseEntity.ok(statistics)
    }

    // ==================== OPENCLAW COMPATIBILITY ENDPOINTS ====================

    /**
     * OpenClaw-compatible chat endpoint
     * Provides backward compatibility with existing OpenClaw applications
     */
    @PostMapping("/chat")
    suspend fun chat(@Valid @RequestBody request: ChatRequest): ResponseEntity<ChatResponse> {
        logger.info("OpenClaw-compatible chat request: ${request.message}")

        try {
            // Convert to internal search request
            val searchRequest = MemorySearchRequest(
                query = request.message,
                sessionId = request.sessionId?.let { UUID.fromString(it) },
                userId = request.userId,
                maxResults = request.maxResults,
                minScore = request.minScore,
                searchType = SearchType.HYBRID,
                includeContent = true
            )

            val searchResponse = memoryService.searchMemory(searchRequest)

            // Generate response text based on search results
            val responseText = generateChatResponse(searchResponse.results, request.message)

            // Convert to OpenClaw format
            val citations = searchResponse.results.map { result ->
                Citation(
                    source = result.source ?: result.title,
                    excerpt = result.excerpt,
                    score = result.score,
                    lineRange = result.lineRange
                )
            }

            val chatResponse = ChatResponse(
                text = responseText,
                citations = citations,
                usedKbIds = searchResponse.results.map { it.chunkId.toString() },
                kbVersion = "2.0"
            )

            return ResponseEntity.ok(chatResponse)

        } catch (e: Exception) {
            logger.error("OpenClaw chat request failed", e)
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                .body(
                    ChatResponse(
                        text = "I apologize, but I encountered an error while searching for information. Please try again.",
                        citations = emptyList(),
                        usedKbIds = emptyList()
                    )
                )
        }
    }

    /**
     * OpenClaw-compatible text ingestion endpoint
     */
    @PostMapping("/ingest_text")
    suspend fun ingestText(@Valid @RequestBody request: IngestTextRequest): ResponseEntity<MemoryDocumentResponse> {
        logger.info("OpenClaw-compatible ingest request: ${request.name}")

        val documentRequest = DocumentIngestRequest(
            title = request.name,
            content = request.content,
            contentType = "text/plain",
            metadata = request.metadata
        )

        val document = memoryService.ingestDocument(documentRequest)
        return ResponseEntity.ok(document)
    }

    /**
     * OpenClaw-compatible status endpoint
     */
    @GetMapping("/status")
    suspend fun getStatus(): ResponseEntity<StatusResponse> {
        try {
            val health = memoryService.getSystemHealth()
            val statistics = searchService.getSearchStatistics()

            val statusResponse = StatusResponse(
                backend = "leader-toolbox",
                documentsIndexed = health.documentCount,
                chunksIndexed = health.chunkCount,
                embeddingsGenerated = health.embeddingCount,
                searchCapabilities = listOf("semantic", "keyword", "hybrid"),
                health = if (health.elasticsearchHealthy) "healthy" else "degraded"
            )

            return ResponseEntity.ok(statusResponse)

        } catch (e: Exception) {
            logger.error("Status check failed", e)
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                .body(
                    StatusResponse(
                        backend = "leader-toolbox",
                        documentsIndexed = 0,
                        chunksIndexed = 0,
                        embeddingsGenerated = 0,
                        health = "error"
                    )
                )
        }
    }

    // ==================== EXCEPTION HANDLING ====================

    @ExceptionHandler(IllegalArgumentException::class)
    fun handleIllegalArgumentException(e: IllegalArgumentException): ResponseEntity<ErrorResponse> {
        val errorResponse = ErrorResponse(
            error = "Invalid Argument",
            message = e.message ?: "Invalid argument provided"
        )
        return ResponseEntity.badRequest().body(errorResponse)
    }

    @ExceptionHandler(Exception::class)
    fun handleGenericException(e: Exception): ResponseEntity<ErrorResponse> {
        logger.error("Unexpected error in MemoryController", e)
        val errorResponse = ErrorResponse(
            error = "Internal Server Error",
            message = "An unexpected error occurred. Please try again later."
        )
        return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(errorResponse)
    }

    // ==================== HELPER METHODS ====================

    /**
     * Generate a chat response based on search results
     * This mimics OpenClaw's response generation behavior
     */
    private fun generateChatResponse(results: List<MemorySearchResult>, query: String): String {
        if (results.isEmpty()) {
            return "I couldn't find any relevant information in the knowledge base for your query. Please try rephrasing your question or check if the information has been added to the system."
        }

        val topResults = results.take(3) // Use top 3 results for response
        val responseBuilder = StringBuilder()

        responseBuilder.append("Based on the information in the knowledge base:\n\n")

        topResults.forEachIndexed { index, result ->
            responseBuilder.append("${index + 1}. ")
            if (result.fullContent != null && result.fullContent.length > 200) {
                responseBuilder.append(result.fullContent.take(200).trim())
                if (result.fullContent.length > 200) {
                    responseBuilder.append("...")
                }
            } else {
                responseBuilder.append(result.excerpt)
            }
            responseBuilder.append("\n\n")
        }

        responseBuilder.append("This information comes from ${results.size} relevant source(s) in the knowledge base.")

        if (results.any { it.score < 0.6 }) {
            responseBuilder.append(" Some results may be less directly related to your query.")
        }

        return responseBuilder.toString()
    }
}