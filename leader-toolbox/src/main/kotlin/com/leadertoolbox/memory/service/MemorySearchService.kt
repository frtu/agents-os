package com.leadertoolbox.memory.service

import com.leadertoolbox.memory.dto.*
import com.leadertoolbox.memory.model.*
import com.leadertoolbox.memory.repository.*
import kotlinx.coroutines.*
import org.slf4j.LoggerFactory
import org.springframework.cache.annotation.Cacheable
import org.springframework.stereotype.Service
import java.util.*
import kotlin.math.min

/**
 * Memory Search Service
 *
 * Implements hybrid search combining semantic vector search with keyword-based search
 * using Reciprocal Rank Fusion (RRF) for optimal results.
 */
@Service
class MemorySearchService(
    private val embeddingService: EmbeddingService,
    private val chunkRepository: MemoryChunkRepository,
    private val embeddingRepository: ChunkEmbeddingRepository,
    private val documentRepository: MemoryDocumentRepository,
    private val elasticsearchService: ElasticsearchService
) {
    private val logger = LoggerFactory.getLogger(MemorySearchService::class.java)

    /**
     * Perform hybrid search combining semantic and keyword search
     */
    suspend fun hybridSearch(request: MemorySearchRequest): List<MemorySearchResult> {
        return when (request.searchType) {
            SearchType.SEMANTIC -> semanticSearch(request)
            SearchType.KEYWORD -> keywordSearch(request)
            SearchType.HYBRID -> performHybridSearch(request)
        }
    }

    /**
     * Semantic search using vector embeddings
     */
    @Cacheable("semantic_search", key = "#request.query + '_' + #request.maxResults")
    private suspend fun semanticSearch(request: MemorySearchRequest): List<MemorySearchResult> {
        val startTime = System.currentTimeMillis()
        logger.debug("Performing semantic search for: ${request.query}")

        try {
            // Generate query embedding
            val queryEmbedding = embeddingService.generateEmbedding(request.query)

            // Use Elasticsearch if available, otherwise fall back to PostgreSQL
            val results = try {
                elasticsearchService.vectorSearch(queryEmbedding, request.maxResults * 2)
            } catch (e: Exception) {
                logger.warn("Elasticsearch vector search failed, falling back to PostgreSQL", e)
                postgresVectorSearch(queryEmbedding, request)
            }

            val filteredResults = results
                .filter { it.score >= request.minScore }
                .take(request.maxResults)

            logger.debug("Semantic search completed in ${System.currentTimeMillis() - startTime}ms, found ${filteredResults.size} results")
            return filteredResults

        } catch (e: Exception) {
            logger.error("Semantic search failed for query: ${request.query}", e)
            return emptyList()
        }
    }

    /**
     * Keyword search using full-text search
     */
    private suspend fun keywordSearch(request: MemorySearchRequest): List<MemorySearchResult> {
        val startTime = System.currentTimeMillis()
        logger.debug("Performing keyword search for: ${request.query}")

        try {
            // Use Elasticsearch if available, otherwise fall back to PostgreSQL
            val results = try {
                elasticsearchService.keywordSearch(request.query, request.maxResults)
            } catch (e: Exception) {
                logger.warn("Elasticsearch keyword search failed, falling back to PostgreSQL", e)
                postgresKeywordSearch(request)
            }

            logger.debug("Keyword search completed in ${System.currentTimeMillis() - startTime}ms, found ${results.size} results")
            return results

        } catch (e: Exception) {
            logger.error("Keyword search failed for query: ${request.query}", e)
            return emptyList()
        }
    }

    /**
     * Hybrid search using Reciprocal Rank Fusion
     */
    private suspend fun performHybridSearch(request: MemorySearchRequest): List<MemorySearchResult> {
        val startTime = System.currentTimeMillis()
        logger.debug("Performing hybrid search for: ${request.query}")

        try {
            // Perform both searches in parallel
            val candidateMultiplier = 4 // Retrieve 4x more candidates for better fusion
            val expandedRequest = request.copy(maxResults = request.maxResults * candidateMultiplier)

            val (semanticResults, keywordResults) = coroutineScope {
                val semanticDeferred = async { semanticSearch(expandedRequest) }
                val keywordDeferred = async { keywordSearch(expandedRequest) }

                Pair(semanticDeferred.await(), keywordDeferred.await())
            }

            // Fuse results using Reciprocal Rank Fusion
            val fusedResults = fuseResults(
                semanticResults = semanticResults,
                keywordResults = keywordResults,
                vectorWeight = 0.7,
                textWeight = 0.3,
                k = 60
            )

            val finalResults = fusedResults
                .filter { it.score >= request.minScore }
                .take(request.maxResults)

            logger.debug("Hybrid search completed in ${System.currentTimeMillis() - startTime}ms")
            logger.debug("Found ${semanticResults.size} semantic + ${keywordResults.size} keyword → ${finalResults.size} final results")

            return finalResults

        } catch (e: Exception) {
            logger.error("Hybrid search failed for query: ${request.query}", e)
            // Fall back to semantic search only
            return semanticSearch(request)
        }
    }

    /**
     * PostgreSQL-based vector search fallback
     */
    private suspend fun postgresVectorSearch(
        queryEmbedding: FloatArray,
        request: MemorySearchRequest
    ): List<MemorySearchResult> {
        return withContext(Dispatchers.IO) {
            try {
                // Try pgvector first if available
                val embeddings = try {
                    embeddingRepository.findSimilarChunksWithPgVector(
                        queryVector = queryEmbedding.toTypedArray(),
                        minSimilarity = request.minScore,
                        maxResults = request.maxResults
                    )
                } catch (e: Exception) {
                    // Fall back to array-based similarity
                    embeddingRepository.findSimilarChunks(
                        queryVector = queryEmbedding.toTypedArray(),
                        minSimilarity = request.minScore,
                        maxResults = request.maxResults
                    )
                }

                embeddings.mapNotNull { embedding ->
                    val chunk = chunkRepository.findById(embedding.chunkId).orElse(null)
                    val document = chunk?.let {
                        documentRepository.findById(it.documentId).orElse(null)
                    }

                    if (chunk != null && document != null && document.deletedAt == null) {
                        MemorySearchResult(
                            chunkId = chunk.id,
                            documentId = document.id,
                            title = document.title,
                            excerpt = chunk.excerpt,
                            fullContent = if (request.includeContent) chunk.content else null,
                            score = embeddingService.cosineSimilarity(queryEmbedding, embedding.embeddingVector).toDouble(),
                            chunkIndex = chunk.chunkIndex,
                            searchType = "semantic",
                            source = document.sourcePath ?: document.sourceUrl,
                            lineRange = "${chunk.charStartPos}-${chunk.charEndPos}",
                            metadata = document.metadata + chunk.metadata
                        )
                    } else null
                }
            } catch (e: Exception) {
                logger.error("PostgreSQL vector search failed", e)
                emptyList()
            }
        }
    }

    /**
     * PostgreSQL-based keyword search fallback
     */
    private suspend fun postgresKeywordSearch(request: MemorySearchRequest): List<MemorySearchResult> {
        return withContext(Dispatchers.IO) {
            try {
                val chunks = chunkRepository.searchByContent(request.query)
                    .take(request.maxResults)

                chunks.mapNotNull { chunk ->
                    val document = documentRepository.findById(chunk.documentId).orElse(null)

                    if (document?.deletedAt == null) {
                        // Simple scoring based on query term frequency
                        val score = calculateKeywordScore(chunk.content, request.query)

                        if (score >= request.minScore) {
                            MemorySearchResult(
                                chunkId = chunk.id,
                                documentId = document.id,
                                title = document.title,
                                excerpt = chunk.excerpt,
                                fullContent = if (request.includeContent) chunk.content else null,
                                score = score,
                                chunkIndex = chunk.chunkIndex,
                                searchType = "keyword",
                                source = document.sourcePath ?: document.sourceUrl,
                                lineRange = "${chunk.charStartPos}-${chunk.charEndPos}",
                                metadata = document.metadata + chunk.metadata
                            )
                        } else null
                    } else null
                }
            } catch (e: Exception) {
                logger.error("PostgreSQL keyword search failed", e)
                emptyList()
            }
        }
    }

    /**
     * Fuse search results using Reciprocal Rank Fusion (RRF)
     */
    private fun fuseResults(
        semanticResults: List<MemorySearchResult>,
        keywordResults: List<MemorySearchResult>,
        vectorWeight: Double = 0.7,
        textWeight: Double = 0.3,
        k: Int = 60
    ): List<MemorySearchResult> {
        val fusedScores = mutableMapOf<Pair<UUID, UUID>, Double>()
        val resultMap = mutableMapOf<Pair<UUID, UUID>, MemorySearchResult>()

        // Process semantic (vector) results
        semanticResults.forEachIndexed { rank, result ->
            val key = Pair(result.chunkId, result.documentId)
            val rrfScore = vectorWeight / (k + rank + 1)
            fusedScores[key] = fusedScores.getOrDefault(key, 0.0) + rrfScore
            resultMap[key] = result.copy(searchType = "hybrid")
        }

        // Process keyword results
        keywordResults.forEachIndexed { rank, result ->
            val key = Pair(result.chunkId, result.documentId)
            val rrfScore = textWeight / (k + rank + 1)
            fusedScores[key] = fusedScores.getOrDefault(key, 0.0) + rrfScore

            // Update result or use existing one
            if (!resultMap.containsKey(key)) {
                resultMap[key] = result.copy(searchType = "hybrid")
            }
        }

        // Sort by fused score and return
        return fusedScores.entries
            .sortedByDescending { it.value }
            .mapNotNull { entry ->
                resultMap[entry.key]?.copy(score = entry.value)
            }
    }

    /**
     * Calculate simple keyword-based score
     */
    private fun calculateKeywordScore(content: String, query: String): Double {
        val contentLower = content.lowercase()
        val queryTerms = query.lowercase().split("\\s+".toRegex()).filter { it.isNotBlank() }

        if (queryTerms.isEmpty()) return 0.0

        var score = 0.0
        val contentWords = contentLower.split("\\s+".toRegex())

        for (term in queryTerms) {
            val termCount = contentWords.count { it.contains(term) }
            val termFrequency = termCount.toDouble() / contentWords.size
            val termScore = termFrequency * (1.0 + kotlin.math.ln(termCount + 1.0))
            score += termScore
        }

        // Normalize by query length
        return min(score / queryTerms.size, 1.0)
    }

    /**
     * Search similar documents based on a given document
     */
    suspend fun findSimilarDocuments(
        documentId: UUID,
        maxResults: Int = 5,
        minScore: Double = 0.3
    ): List<MemorySearchResult> {
        try {
            // Get document content for similarity
            val document = documentRepository.findById(documentId).orElse(null)
                ?: return emptyList()

            if (document.deletedAt != null) return emptyList()

            // Use the first chunk or title for similarity search
            val chunks = chunkRepository.findByDocumentIdOrderByChunkIndex(documentId)
            val searchText = if (chunks.isNotEmpty()) {
                chunks.first().content.take(500) // Use first chunk
            } else {
                document.title // Fallback to title
            }

            val request = MemorySearchRequest(
                query = searchText,
                maxResults = maxResults + 1, // +1 to exclude self
                minScore = minScore,
                searchType = SearchType.SEMANTIC
            )

            return semanticSearch(request)
                .filter { it.documentId != documentId } // Exclude the source document
                .take(maxResults)

        } catch (e: Exception) {
            logger.error("Failed to find similar documents for $documentId", e)
            return emptyList()
        }
    }

    /**
     * Get search suggestions based on query
     */
    suspend fun getSearchSuggestions(
        query: String,
        maxSuggestions: Int = 5
    ): List<String> {
        if (query.length < 3) return emptyList()

        try {
            // Simple implementation - can be enhanced with more sophisticated NLP
            val queryWords = query.lowercase().split("\\s+".toRegex())
                .filter { it.length > 2 }

            if (queryWords.isEmpty()) return emptyList()

            val suggestions = mutableSetOf<String>()

            // Add variations and extensions
            queryWords.forEach { word ->
                suggestions.add("$word*") // Wildcard suggestion
                suggestions.add("how to $word") // How-to suggestion
                suggestions.add("$word examples") // Examples suggestion
            }

            // Add multi-word combinations
            if (queryWords.size > 1) {
                suggestions.add(queryWords.joinToString(" ") + " guide")
                suggestions.add(queryWords.joinToString(" ") + " tutorial")
            }

            return suggestions.take(maxSuggestions)

        } catch (e: Exception) {
            logger.error("Failed to generate search suggestions for: $query", e)
            return emptyList()
        }
    }

    /**
     * Count total searchable chunks
     */
    suspend fun getSearchableChunkCount(): Long {
        return withContext(Dispatchers.IO) {
            chunkRepository.count()
        }
    }

    /**
     * Get search statistics
     */
    suspend fun getSearchStatistics(): Map<String, Any> {
        return withContext(Dispatchers.IO) {
            try {
                val totalDocuments = documentRepository.countByDeletedAtIsNull()
                val totalChunks = chunkRepository.count()
                val totalEmbeddings = embeddingRepository.count()
                val embeddingModels = embeddingRepository.countByModel()

                mapOf(
                    "totalDocuments" to totalDocuments,
                    "totalChunks" to totalChunks,
                    "totalEmbeddings" to totalEmbeddings,
                    "embeddingModels" to embeddingModels.associate {
                        (it[0]?.toString() ?: "unknown") to (it[1]?.toString()?.toLongOrNull() ?: 0L)
                    },
                    "searchCapabilities" to listOf("semantic", "keyword", "hybrid"),
                    "vectorDimension" to EmbeddingService.EXPECTED_DIMENSION
                )
            } catch (e: Exception) {
                logger.error("Failed to get search statistics", e)
                mapOf("error" to (e.message ?: "Unknown error"))
            }
        }
    }
}