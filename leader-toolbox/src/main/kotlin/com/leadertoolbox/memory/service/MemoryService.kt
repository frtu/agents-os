package com.leadertoolbox.memory.service

import com.leadertoolbox.memory.dto.*
import com.leadertoolbox.memory.model.*
import com.leadertoolbox.memory.repository.*
import kotlinx.coroutines.*
import org.slf4j.LoggerFactory
import org.springframework.cache.annotation.CacheEvict
import org.springframework.cache.annotation.Cacheable
import org.springframework.data.domain.Page
import org.springframework.data.domain.PageRequest
import org.springframework.data.domain.Pageable
import org.springframework.data.domain.Sort
import org.springframework.stereotype.Service
import org.springframework.transaction.annotation.Transactional
import java.time.OffsetDateTime
import java.util.*

/**
 * Memory Service
 *
 * Core service for managing the memory system including document ingestion,
 * chunking, embedding generation, and search operations.
 */
@Service
@Transactional
class MemoryService(
    private val documentRepository: MemoryDocumentRepository,
    private val chunkRepository: MemoryChunkRepository,
    private val embeddingRepository: ChunkEmbeddingRepository,
    private val sessionRepository: MemorySessionRepository,
    private val tagRepository: MetadataTagRepository,
    private val analyticsRepository: SearchAnalyticRepository,
    private val embeddingService: EmbeddingService,
    private val searchService: MemorySearchService,
    private val elasticsearchService: ElasticsearchService
) {
    private val logger = LoggerFactory.getLogger(MemoryService::class.java)

    /**
     * Ingest a document into the memory system
     */
    @CacheEvict(value = ["documents", "search"], allEntries = true)
    suspend fun ingestDocument(request: DocumentIngestRequest): MemoryDocumentResponse {
        logger.info("Ingesting document: ${request.title}")

        // Check for existing document with same content hash
        val contentHash = generateContentHash(request.content)
        val existingDocument = documentRepository.findByContentHashAndDeletedAtIsNull(contentHash)

        if (existingDocument.isNotEmpty()) {
            logger.info("Document with same content already exists: ${existingDocument.first().id}")
            return MemoryDocumentResponse.fromEntity(existingDocument.first())
        }

        // Create document
        val document = MemoryDocument.fromContent(
            title = request.title,
            content = request.content,
            contentType = request.contentType,
            sourcePath = request.sourcePath,
            sourceUrl = request.sourceUrl,
            metadata = request.metadata
        )

        val savedDocument = documentRepository.save(document)
        logger.debug("Created document with ID: ${savedDocument.id}")

        // Create chunks
        val chunks = MemoryChunk.createChunks(
            documentId = savedDocument.id,
            content = request.content,
            chunkSize = request.chunkSize,
            overlap = request.chunkOverlap
        )

        val savedChunks = chunkRepository.saveAll(chunks)
        logger.debug("Created ${savedChunks.size} chunks for document ${savedDocument.id}")

        // Generate embeddings asynchronously
        GlobalScope.launch {
            try {
                generateAndStoreEmbeddings(savedChunks)
                indexInElasticsearch(savedDocument, savedChunks)
                logger.info("Successfully processed document ${savedDocument.id} with ${savedChunks.size} chunks")
            } catch (e: Exception) {
                logger.error("Failed to process embeddings for document ${savedDocument.id}", e)
                // Consider marking document as failed or retry mechanism
            }
        }

        return MemoryDocumentResponse.fromEntity(savedDocument, savedChunks.size)
    }

    /**
     * Search memory using hybrid approach
     */
    suspend fun searchMemory(request: MemorySearchRequest): MemorySearchResponse {
        val startTime = System.currentTimeMillis()

        try {
            val results = searchService.hybridSearch(request)

            // Record analytics
            val topScore = results.maxOfOrNull { it.score }?.toFloat()
            val analytic = SearchAnalytic.fromSearchExecution(
                sessionId = request.sessionId,
                queryText = request.query,
                queryType = when (request.searchType) {
                    SearchType.SEMANTIC -> SearchAnalytic.QueryType.SEMANTIC
                    SearchType.KEYWORD -> SearchAnalytic.QueryType.KEYWORD
                    SearchType.HYBRID -> SearchAnalytic.QueryType.HYBRID
                },
                results = results,
                startTime = startTime,
                topScore = topScore
            )

            analyticsRepository.save(analytic)

            return MemorySearchResponse(
                results = results,
                totalResults = results.size,
                query = request.query,
                searchType = request.searchType.name,
                executionTimeMs = (System.currentTimeMillis() - startTime).toInt()
            )
        } catch (e: Exception) {
            logger.error("Search failed for query: ${request.query}", e)

            // Record failed search
            val analytic = SearchAnalytic.fromSearchExecution(
                sessionId = request.sessionId,
                queryText = request.query,
                queryType = SearchAnalytic.QueryType.HYBRID,
                results = emptyList(),
                startTime = startTime
            )
            analyticsRepository.save(analytic)

            throw e
        }
    }

    /**
     * Get document by ID
     */
    @Cacheable("documents")
    fun getDocument(documentId: UUID): MemoryDocumentResponse? {
        val document = documentRepository.findByIdAndDeletedAtIsNull(documentId)
        return document?.let {
            val chunkCount = chunkRepository.countByDocumentId(documentId)
            MemoryDocumentResponse.fromEntity(it, chunkCount.toInt())
        }
    }

    /**
     * List documents with pagination and search
     */
    @Cacheable("documents")
    fun listDocuments(
        page: Int = 0,
        size: Int = 20,
        search: String? = null,
        sortBy: String = "createdAt",
        sortDirection: String = "DESC"
    ): PagedResponse<MemoryDocumentResponse> {
        val pageable: Pageable = PageRequest.of(
            page, size,
            Sort.by(Sort.Direction.fromString(sortDirection), sortBy)
        )

        val documentsPage: Page<MemoryDocument> = if (search.isNullOrBlank()) {
            documentRepository.findByDeletedAtIsNull(pageable)
        } else {
            documentRepository.findByTitleContainingIgnoreCaseAndDeletedAtIsNull(search, pageable)
        }

        val documents = documentsPage.content.map { document ->
            val chunkCount = chunkRepository.countByDocumentId(document.id)
            MemoryDocumentResponse.fromEntity(document, chunkCount.toInt())
        }

        return PagedResponse(
            content = documents,
            page = page,
            size = size,
            totalElements = documentsPage.totalElements,
            totalPages = documentsPage.totalPages,
            first = documentsPage.isFirst,
            last = documentsPage.isLast
        )
    }

    /**
     * Delete document (soft delete)
     */
    @CacheEvict(value = ["documents", "search"], allEntries = true)
    fun deleteDocument(documentId: UUID) {
        val document = documentRepository.findById(documentId).orElseThrow {
            IllegalArgumentException("Document not found: $documentId")
        }

        // Soft delete
        val deletedDocument = document.copy(deletedAt = OffsetDateTime.now())
        documentRepository.save(deletedDocument)

        // Remove from Elasticsearch
        GlobalScope.launch {
            elasticsearchService.deleteDocument(documentId)
        }

        logger.info("Soft deleted document: $documentId")
    }

    /**
     * Get chunk by ID with document context
     */
    fun getChunk(chunkId: UUID): ChunkDetailResponse? {
        return chunkRepository.findById(chunkId)
            .map { chunk ->
                val document = documentRepository.findById(chunk.documentId).orElse(null)
                val embedding = embeddingRepository.findById(chunkId).orElse(null)
                ChunkDetailResponse.fromEntities(chunk, document, embedding)
            }
            .orElse(null)
    }

    /**
     * Get system health status
     */
    suspend fun getSystemHealth(): HealthResponse {
        val documentCount = documentRepository.countByDeletedAtIsNull()
        val chunkCount = chunkRepository.count()
        val embeddingCount = embeddingRepository.count()

        val recentSearches = analyticsRepository.findTop10ByOrderByCreatedAtDesc()
        val avgQueryTime = recentSearches.takeIf { it.isNotEmpty() }
            ?.map { it.executionTimeMs }
            ?.average() ?: 0.0

        val elasticsearchHealthy = try {
            elasticsearchService.isHealthy()
        } catch (e: Exception) {
            false
        }

        return HealthResponse(
            status = if (elasticsearchHealthy) "healthy" else "degraded",
            documentCount = documentCount.toInt(),
            chunkCount = chunkCount.toInt(),
            embeddingCount = embeddingCount.toInt(),
            averageQueryTimeMs = avgQueryTime,
            elasticsearchHealthy = elasticsearchHealthy,
            timestamp = OffsetDateTime.now()
        )
    }

    /**
     * Create or get session
     */
    fun createSession(request: CreateSessionRequest): MemorySessionResponse {
        val session = if (request.userId != null) {
            MemorySession.createForUser(
                userId = request.userId,
                sessionName = request.sessionName,
                contextData = request.contextData,
                expiresIn = request.expiresIn
            )
        } else {
            MemorySession.createAnonymous(
                sessionName = request.sessionName,
                contextData = request.contextData,
                expiresIn = request.expiresIn
            )
        }

        val savedSession = sessionRepository.save(session)
        return MemorySessionResponse.fromEntity(savedSession)
    }

    /**
     * Get session by ID
     */
    fun getSession(sessionId: UUID): MemorySessionResponse? {
        return sessionRepository.findById(sessionId)
            .filter { it.isActive }
            .map { MemorySessionResponse.fromEntity(it) }
            .orElse(null)
    }

    /**
     * Update session context
     */
    fun updateSessionContext(sessionId: UUID, contextData: Map<String, Any>): MemorySessionResponse {
        val session = sessionRepository.findById(sessionId).orElseThrow {
            IllegalArgumentException("Session not found: $sessionId")
        }

        val updatedSession = session.copy(
            contextData = session.contextData + contextData,
            lastAccessedAt = OffsetDateTime.now()
        )

        val savedSession = sessionRepository.save(updatedSession)
        return MemorySessionResponse.fromEntity(savedSession)
    }

    /**
     * Get search analytics for a session
     */
    fun getSessionAnalytics(sessionId: UUID): SearchAnalyticsResponse {
        val analytics = analyticsRepository.findBySessionIdOrderByCreatedAtDesc(sessionId)
        val metrics = SearchAnalyticsHelper.calculatePerformanceMetrics(analytics)
        val patterns = SearchAnalyticsHelper.analyzeQueryPatterns(analytics)

        return SearchAnalyticsResponse(
            sessionId = sessionId,
            totalQueries = analytics.size,
            averageExecutionTimeMs = metrics.avgExecutionTimeMs,
            averageResultCount = metrics.avgResultCount,
            successRate = metrics.successRate,
            mostCommonQueryType = patterns.mostCommonQueryType.name,
            recentQueries = analytics.take(10).map {
                RecentQueryInfo(
                    query = it.queryText,
                    queryType = it.queryType.name,
                    resultCount = it.resultCount,
                    executionTimeMs = it.executionTimeMs,
                    timestamp = it.createdAt
                )
            }
        )
    }

    // Private helper methods

    private suspend fun generateAndStoreEmbeddings(chunks: List<MemoryChunk>) {
        logger.debug("Generating embeddings for ${chunks.size} chunks")

        try {
            val embeddings = embeddingService.generateEmbeddings(chunks.map { it.content })

            val chunkEmbeddings = chunks.zip(embeddings).map { (chunk, embedding) ->
                ChunkEmbedding.fromVector(
                    chunkId = chunk.id,
                    vector = embedding,
                    modelName = EmbeddingService.MODEL_NAME
                )
            }

            embeddingRepository.saveAll(chunkEmbeddings)
            logger.debug("Saved ${chunkEmbeddings.size} embeddings")
        } catch (e: Exception) {
            logger.error("Failed to generate embeddings for chunks", e)
            throw e
        }
    }

    private suspend fun indexInElasticsearch(document: MemoryDocument, chunks: List<MemoryChunk>) {
        try {
            elasticsearchService.indexDocument(document, chunks)
            logger.debug("Indexed document ${document.id} in Elasticsearch")
        } catch (e: Exception) {
            logger.error("Failed to index document ${document.id} in Elasticsearch", e)
            // Don't throw - Elasticsearch indexing is optional
        }
    }

    private fun generateContentHash(content: String): String {
        return java.security.MessageDigest.getInstance("SHA-256")
            .digest(content.toByteArray())
            .joinToString("") { "%02x".format(it) }
    }
}