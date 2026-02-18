package com.leadertoolbox.memory.repository

import com.leadertoolbox.memory.model.*
import org.springframework.data.domain.Page
import org.springframework.data.domain.Pageable
import org.springframework.data.jpa.repository.JpaRepository
import org.springframework.data.jpa.repository.Modifying
import org.springframework.data.jpa.repository.Query
import org.springframework.data.repository.query.Param
import org.springframework.stereotype.Repository
import java.time.OffsetDateTime
import java.util.*

@Repository
interface MemoryDocumentRepository : JpaRepository<MemoryDocument, UUID> {

    // Basic queries
    fun findByIdAndDeletedAtIsNull(id: UUID): MemoryDocument?

    fun findByDeletedAtIsNull(pageable: Pageable): Page<MemoryDocument>

    fun findByContentHashAndDeletedAtIsNull(contentHash: String): List<MemoryDocument>

    fun countByDeletedAtIsNull(): Long

    // Search queries
    fun findByTitleContainingIgnoreCaseAndDeletedAtIsNull(
        title: String,
        pageable: Pageable
    ): Page<MemoryDocument>

    @Query("""
        SELECT md FROM MemoryDocument md
        WHERE md.deletedAt IS NULL
        AND (LOWER(md.title) LIKE LOWER(CONCAT('%', :search, '%'))
             OR LOWER(md.sourcePath) LIKE LOWER(CONCAT('%', :search, '%')))
    """)
    fun searchByTitleOrPath(
        @Param("search") search: String,
        pageable: Pageable
    ): Page<MemoryDocument>

    // Content type queries
    fun findByContentTypeAndDeletedAtIsNull(
        contentType: String,
        pageable: Pageable
    ): Page<MemoryDocument>

    // Metadata queries using JSONB
    @Query("""
        SELECT md FROM MemoryDocument md
        WHERE md.deletedAt IS NULL
        AND jsonb_extract_path_text(md.metadata, :key) = :value
    """, nativeQuery = false)
    fun findByMetadata(
        @Param("key") key: String,
        @Param("value") value: String
    ): List<MemoryDocument>

    // Date range queries
    fun findByCreatedAtBetweenAndDeletedAtIsNull(
        startDate: OffsetDateTime,
        endDate: OffsetDateTime,
        pageable: Pageable
    ): Page<MemoryDocument>

    // Bulk operations
    @Modifying
    @Query("UPDATE MemoryDocument md SET md.deletedAt = :deletedAt WHERE md.id IN :ids")
    fun softDeleteByIds(
        @Param("ids") ids: List<UUID>,
        @Param("deletedAt") deletedAt: OffsetDateTime
    ): Int
}

@Repository
interface MemoryChunkRepository : JpaRepository<MemoryChunk, UUID> {

    // Document relationship queries
    fun findByDocumentId(documentId: UUID): List<MemoryChunk>

    fun findByDocumentIdOrderByChunkIndex(documentId: UUID): List<MemoryChunk>

    fun countByDocumentId(documentId: UUID): Long

    // Content queries
    fun findByContentHash(contentHash: String): List<MemoryChunk>

    @Query("""
        SELECT mc FROM MemoryChunk mc
        JOIN mc.document md
        WHERE md.deletedAt IS NULL
        AND LOWER(mc.content) LIKE LOWER(CONCAT('%', :content, '%'))
    """)
    fun searchByContent(@Param("content") content: String): List<MemoryChunk>

    // Chunk position queries
    fun findByDocumentIdAndChunkIndex(documentId: UUID, chunkIndex: Int): MemoryChunk?

    @Query("""
        SELECT mc FROM MemoryChunk mc
        WHERE mc.documentId = :documentId
        AND mc.charStartPos >= :startPos
        AND mc.charEndPos <= :endPos
        ORDER BY mc.chunkIndex
    """)
    fun findByDocumentIdAndPositionRange(
        @Param("documentId") documentId: UUID,
        @Param("startPos") startPos: Int,
        @Param("endPos") endPos: Int
    ): List<MemoryChunk>

    // Token count queries
    @Query("SELECT SUM(mc.tokenCount) FROM MemoryChunk mc WHERE mc.documentId = :documentId")
    fun getTotalTokensByDocumentId(@Param("documentId") documentId: UUID): Long?

    @Query("""
        SELECT mc FROM MemoryChunk mc
        WHERE mc.tokenCount BETWEEN :minTokens AND :maxTokens
    """)
    fun findByTokenCountRange(
        @Param("minTokens") minTokens: Int,
        @Param("maxTokens") maxTokens: Int
    ): List<MemoryChunk>

    // Bulk operations
    @Modifying
    @Query("DELETE FROM MemoryChunk mc WHERE mc.documentId IN :documentIds")
    fun deleteByDocumentIds(@Param("documentIds") documentIds: List<UUID>): Int
}

@Repository
interface ChunkEmbeddingRepository : JpaRepository<ChunkEmbedding, UUID> {

    // Model queries
    fun findByModelName(modelName: String): List<ChunkEmbedding>

    fun countByModelName(modelName: String): Long

    // Vector dimension queries
    fun findByVectorDimension(dimension: Int): List<ChunkEmbedding>

    @Query("""
        SELECT ce FROM ChunkEmbedding ce
        WHERE ce.modelName = :modelName
        AND ce.vectorDimension = :dimension
    """)
    fun findByModelAndDimension(
        @Param("modelName") modelName: String,
        @Param("dimension") dimension: Int
    ): List<ChunkEmbedding>

    // Join queries with chunks and documents
    @Query("""
        SELECT ce FROM ChunkEmbedding ce
        JOIN MemoryChunk mc ON ce.chunkId = mc.id
        JOIN MemoryDocument md ON mc.documentId = md.id
        WHERE md.deletedAt IS NULL
    """)
    fun findAllWithActiveDocuments(): List<ChunkEmbedding>

    @Query("""
        SELECT ce FROM ChunkEmbedding ce
        JOIN MemoryChunk mc ON ce.chunkId = mc.id
        WHERE mc.documentId = :documentId
    """)
    fun findByDocumentId(@Param("documentId") documentId: UUID): List<ChunkEmbedding>

    // Vector similarity search (for databases without pgvector)
    @Query(value = """
        SELECT ce.*,
               cosine_similarity(ce.embedding_vector, :queryVector) as similarity_score
        FROM chunk_embeddings ce
        JOIN memory_chunks mc ON ce.chunk_id = mc.id
        JOIN memory_documents md ON mc.document_id = md.id
        WHERE md.deleted_at IS NULL
        AND cosine_similarity(ce.embedding_vector, :queryVector) >= :minSimilarity
        ORDER BY similarity_score DESC
        LIMIT :maxResults
    """, nativeQuery = true)
    fun findSimilarChunks(
        @Param("queryVector") queryVector: Array<Float>,
        @Param("minSimilarity") minSimilarity: Double,
        @Param("maxResults") maxResults: Int
    ): List<ChunkEmbedding>

    // Optimized vector search using pgvector (if available)
    @Query(value = """
        SELECT ce.*,
               (1 - (ce.embedding_vector_pgv <=> cast(:queryVector as vector(384)))) as similarity_score
        FROM chunk_embeddings ce
        JOIN memory_chunks mc ON ce.chunk_id = mc.id
        JOIN memory_documents md ON mc.document_id = md.id
        WHERE md.deleted_at IS NULL
        AND ce.embedding_vector_pgv IS NOT NULL
        AND (1 - (ce.embedding_vector_pgv <=> cast(:queryVector as vector(384)))) >= :minSimilarity
        ORDER BY ce.embedding_vector_pgv <=> cast(:queryVector as vector(384)) ASC
        LIMIT :maxResults
    """, nativeQuery = true)
    fun findSimilarChunksWithPgVector(
        @Param("queryVector") queryVector: Array<Float>,
        @Param("minSimilarity") minSimilarity: Double,
        @Param("maxResults") maxResults: Int
    ): List<ChunkEmbedding>

    // Statistics queries
    @Query("SELECT AVG(array_length(ce.embeddingVector, 1)) FROM ChunkEmbedding ce")
    fun getAverageVectorDimension(): Double?

    @Query("""
        SELECT ce.modelName, COUNT(ce)
        FROM ChunkEmbedding ce
        GROUP BY ce.modelName
    """)
    fun countByModel(): List<Array<Any>>
}

@Repository
interface MemorySessionRepository : JpaRepository<MemorySession, UUID> {

    // User queries
    fun findByUserId(userId: String): List<MemorySession>

    fun findByUserIdAndExpiresAtAfter(
        userId: String,
        currentTime: OffsetDateTime
    ): List<MemorySession>

    // Active sessions
    @Query("""
        SELECT ms FROM MemorySession ms
        WHERE (ms.expiresAt IS NULL OR ms.expiresAt > :currentTime)
    """)
    fun findActiveSessions(@Param("currentTime") currentTime: OffsetDateTime): List<MemorySession>

    @Query("""
        SELECT ms FROM MemorySession ms
        WHERE ms.userId = :userId
        AND (ms.expiresAt IS NULL OR ms.expiresAt > :currentTime)
    """)
    fun findActiveSessionsByUserId(
        @Param("userId") userId: String,
        @Param("currentTime") currentTime: OffsetDateTime
    ): List<MemorySession>

    // Session cleanup
    @Query("""
        SELECT ms FROM MemorySession ms
        WHERE ms.expiresAt < :currentTime
        OR ms.lastAccessedAt < :inactiveSince
    """)
    fun findExpiredSessions(
        @Param("currentTime") currentTime: OffsetDateTime,
        @Param("inactiveSince") inactiveSince: OffsetDateTime
    ): List<MemorySession>

    @Modifying
    @Query("""
        DELETE FROM MemorySession ms
        WHERE ms.expiresAt < :currentTime
        OR ms.lastAccessedAt < :inactiveSince
    """)
    fun deleteExpiredSessions(
        @Param("currentTime") currentTime: OffsetDateTime,
        @Param("inactiveSince") inactiveSince: OffsetDateTime
    ): Int

    // Context data queries using JSONB
    @Query("""
        SELECT ms FROM MemorySession ms
        WHERE jsonb_extract_path_text(ms.contextData, :key) = :value
    """, nativeQuery = false)
    fun findByContextData(
        @Param("key") key: String,
        @Param("value") value: String
    ): List<MemorySession>

    // Recently accessed sessions
    fun findByLastAccessedAtAfterOrderByLastAccessedAtDesc(
        lastAccessedAfter: OffsetDateTime
    ): List<MemorySession>

    // Session name search
    fun findBySessionNameContainingIgnoreCase(sessionName: String): List<MemorySession>
}

@Repository
interface MetadataTagRepository : JpaRepository<MetadataTag, UUID> {

    // Target queries
    fun findByTargetTypeAndTargetId(
        targetType: MetadataTag.TargetType,
        targetId: UUID
    ): List<MetadataTag>

    // Tag name and type queries
    fun findByTagName(tagName: String): List<MetadataTag>

    fun findByTagNameAndTagType(tagName: String, tagType: String): List<MetadataTag>

    fun findByTagType(tagType: String): List<MetadataTag>

    // Value queries
    fun findByTagNameAndTagValue(tagName: String, tagValue: String): List<MetadataTag>

    @Query("""
        SELECT mt FROM MetadataTag mt
        WHERE mt.tagName = :tagName
        AND mt.tagValue IS NOT NULL
    """)
    fun findByTagNameWithValue(@Param("tagName") tagName: String): List<MetadataTag>

    // Document and chunk specific queries
    @Query("""
        SELECT mt FROM MetadataTag mt
        WHERE mt.targetType = 'DOCUMENT'
        AND mt.targetId = :documentId
    """)
    fun findDocumentTags(@Param("documentId") documentId: UUID): List<MetadataTag>

    @Query("""
        SELECT mt FROM MetadataTag mt
        WHERE mt.targetType = 'CHUNK'
        AND mt.targetId = :chunkId
    """)
    fun findChunkTags(@Param("chunkId") chunkId: UUID): List<MetadataTag>

    // Aggregation queries
    @Query("""
        SELECT mt.tagName, COUNT(mt)
        FROM MetadataTag mt
        GROUP BY mt.tagName
        ORDER BY COUNT(mt) DESC
    """)
    fun getTagUsageStats(): List<Array<Any>>

    @Query("""
        SELECT mt.tagType, COUNT(mt)
        FROM MetadataTag mt
        GROUP BY mt.tagType
    """)
    fun getTagTypeStats(): List<Array<Any>>

    // Search queries
    @Query("""
        SELECT mt FROM MetadataTag mt
        WHERE LOWER(mt.tagName) LIKE LOWER(CONCAT('%', :pattern, '%'))
        OR LOWER(mt.tagValue) LIKE LOWER(CONCAT('%', :pattern, '%'))
    """)
    fun searchTags(@Param("pattern") pattern: String): List<MetadataTag>

    // Bulk operations
    @Modifying
    @Query("DELETE FROM MetadataTag mt WHERE mt.targetType = :targetType AND mt.targetId IN :targetIds")
    fun deleteByTargetTypeAndTargetIds(
        @Param("targetType") targetType: MetadataTag.TargetType,
        @Param("targetIds") targetIds: List<UUID>
    ): Int
}

@Repository
interface SearchAnalyticRepository : JpaRepository<SearchAnalytic, UUID> {

    // Session queries
    fun findBySessionIdOrderByCreatedAtDesc(sessionId: UUID): List<SearchAnalytic>

    fun findBySessionIdAndCreatedAtAfter(
        sessionId: UUID,
        createdAfter: OffsetDateTime
    ): List<SearchAnalytic>

    // Query type statistics
    fun findByQueryType(queryType: SearchAnalytic.QueryType): List<SearchAnalytic>

    @Query("""
        SELECT sa.queryType, COUNT(sa), AVG(sa.executionTimeMs), AVG(sa.resultCount)
        FROM SearchAnalytic sa
        GROUP BY sa.queryType
    """)
    fun getQueryTypeStatistics(): List<Array<Any>>

    // Performance queries
    @Query("""
        SELECT sa FROM SearchAnalytic sa
        WHERE sa.executionTimeMs > :thresholdMs
        ORDER BY sa.executionTimeMs DESC
    """)
    fun findSlowQueries(@Param("thresholdMs") thresholdMs: Int): List<SearchAnalytic>

    @Query("""
        SELECT sa FROM SearchAnalytic sa
        WHERE sa.resultCount = 0
        ORDER BY sa.createdAt DESC
    """)
    fun findQueriesWithNoResults(): List<SearchAnalytic>

    // Time-based queries
    fun findByCreatedAtBetweenOrderByCreatedAtDesc(
        startDate: OffsetDateTime,
        endDate: OffsetDateTime
    ): List<SearchAnalytic>

    fun findTop10ByOrderByCreatedAtDesc(): List<SearchAnalytic>

    // Aggregation queries
    @Query("""
        SELECT DATE(sa.createdAt), COUNT(sa), AVG(sa.executionTimeMs)
        FROM SearchAnalytic sa
        WHERE sa.createdAt >= :startDate
        GROUP BY DATE(sa.createdAt)
        ORDER BY DATE(sa.createdAt) DESC
    """)
    fun getDailyStatistics(@Param("startDate") startDate: OffsetDateTime): List<Array<Any>>

    @Query("""
        SELECT sa.queryText, COUNT(sa), AVG(sa.executionTimeMs), AVG(sa.topScore)
        FROM SearchAnalytic sa
        WHERE sa.createdAt >= :startDate
        GROUP BY sa.queryText
        HAVING COUNT(sa) > 1
        ORDER BY COUNT(sa) DESC
    """)
    fun getPopularQueries(@Param("startDate") startDate: OffsetDateTime): List<Array<Any>>

    // Success rate queries
    @Query("""
        SELECT COUNT(sa) * 100.0 / (SELECT COUNT(*) FROM SearchAnalytic)
        FROM SearchAnalytic sa
        WHERE sa.resultCount > 0
        AND sa.executionTimeMs < :maxExecutionTimeMs
    """)
    fun getSuccessRate(@Param("maxExecutionTimeMs") maxExecutionTimeMs: Int): Double?

    // Cleanup queries
    @Modifying
    @Query("DELETE FROM SearchAnalytic sa WHERE sa.createdAt < :cutoffDate")
    fun deleteOlderThan(@Param("cutoffDate") cutoffDate: OffsetDateTime): Int

    // Advanced analytics
    @Query("""
        SELECT
            AVG(sa.executionTimeMs) as avgExecutionTime,
            AVG(sa.resultCount) as avgResultCount,
            AVG(sa.topScore) as avgTopScore,
            COUNT(sa) as totalQueries,
            COUNT(DISTINCT sa.sessionId) as uniqueSessions
        FROM SearchAnalytic sa
        WHERE sa.createdAt >= :startDate
    """)
    fun getPerformanceMetrics(@Param("startDate") startDate: OffsetDateTime): Array<Any>?
}