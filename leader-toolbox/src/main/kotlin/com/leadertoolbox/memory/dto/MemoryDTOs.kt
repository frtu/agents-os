package com.leadertoolbox.memory.dto

import com.leadertoolbox.memory.model.*
import jakarta.validation.constraints.*
import java.time.OffsetDateTime
import java.util.*

// ==================== REQUEST DTOs ====================

data class DocumentIngestRequest(
    @field:NotBlank(message = "Title cannot be blank")
    @field:Size(max = 500, message = "Title cannot exceed 500 characters")
    val title: String,

    @field:NotBlank(message = "Content cannot be blank")
    @field:Size(min = 10, message = "Content must be at least 10 characters")
    val content: String,

    @field:Size(max = 50, message = "Content type cannot exceed 50 characters")
    val contentType: String = "text/plain",

    val sourcePath: String? = null,
    val sourceUrl: String? = null,
    val metadata: Map<String, Any> = emptyMap(),

    @field:Min(value = 100, message = "Chunk size must be at least 100")
    @field:Max(value = 5000, message = "Chunk size cannot exceed 5000")
    val chunkSize: Int = 1000,

    @field:Min(value = 50, message = "Chunk overlap must be at least 50")
    @field:Max(value = 1000, message = "Chunk overlap cannot exceed 1000")
    val chunkOverlap: Int = 200
)

data class MemorySearchRequest(
    @field:NotBlank(message = "Query cannot be blank")
    @field:Size(min = 1, max = 1000, message = "Query must be between 1 and 1000 characters")
    val query: String,

    val sessionId: UUID? = null,
    val userId: String? = null,

    @field:Min(value = 1, message = "Max results must be at least 1")
    @field:Max(value = 50, message = "Max results cannot exceed 50")
    val maxResults: Int = 10,

    @field:DecimalMin(value = "0.0", message = "Min score must be at least 0.0")
    @field:DecimalMax(value = "1.0", message = "Min score cannot exceed 1.0")
    val minScore: Double = 0.3,

    val searchType: SearchType = SearchType.HYBRID,
    val includeContent: Boolean = false,
    val filters: Map<String, String> = emptyMap()
)

enum class SearchType {
    SEMANTIC,   // Vector similarity only
    KEYWORD,    // Text search only
    HYBRID      // Combined approach
}

data class CreateSessionRequest(
    @field:Size(max = 100, message = "User ID cannot exceed 100 characters")
    val userId: String? = null,

    @field:Size(max = 200, message = "Session name cannot exceed 200 characters")
    val sessionName: String? = null,

    val contextData: Map<String, Any> = emptyMap(),
    val expiresIn: java.time.Duration? = null
)

data class UpdateSessionContextRequest(
    val contextData: Map<String, Any>
)

// ==================== RESPONSE DTOs ====================

data class MemoryDocumentResponse(
    val id: UUID,
    val title: String,
    val contentType: String,
    val sourcePath: String?,
    val sourceUrl: String?,
    val contentHash: String,
    val contentLength: Int,
    val chunkCount: Int,
    val metadata: Map<String, Any>,
    val createdAt: OffsetDateTime,
    val updatedAt: OffsetDateTime
) {
    companion object {
        fun fromEntity(document: MemoryDocument, chunkCount: Int = 0): MemoryDocumentResponse {
            return MemoryDocumentResponse(
                id = document.id,
                title = document.title,
                contentType = document.contentType,
                sourcePath = document.sourcePath,
                sourceUrl = document.sourceUrl,
                contentHash = document.contentHash,
                contentLength = document.contentLength,
                chunkCount = chunkCount,
                metadata = document.metadata,
                createdAt = document.createdAt,
                updatedAt = document.updatedAt
            )
        }
    }
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
    val source: String? = null,
    val lineRange: String? = null,
    val metadata: Map<String, Any> = emptyMap()
)

data class MemorySearchResponse(
    val results: List<MemorySearchResult>,
    val totalResults: Int,
    val query: String,
    val searchType: String,
    val executionTimeMs: Int,
    val suggestions: List<String> = emptyList()
)

data class ChunkDetailResponse(
    val chunkId: UUID,
    val documentId: UUID,
    val chunkIndex: Int,
    val content: String,
    val tokenCount: Int,
    val charStartPos: Int,
    val charEndPos: Int,
    val documentTitle: String,
    val contentType: String,
    val hasEmbedding: Boolean,
    val embeddingModel: String? = null,
    val metadata: Map<String, Any> = emptyMap()
) {
    companion object {
        fun fromEntities(
            chunk: MemoryChunk,
            document: MemoryDocument?,
            embedding: ChunkEmbedding?
        ): ChunkDetailResponse {
            return ChunkDetailResponse(
                chunkId = chunk.id,
                documentId = chunk.documentId,
                chunkIndex = chunk.chunkIndex,
                content = chunk.content,
                tokenCount = chunk.tokenCount,
                charStartPos = chunk.charStartPos,
                charEndPos = chunk.charEndPos,
                documentTitle = document?.title ?: "Unknown",
                contentType = document?.contentType ?: "unknown",
                hasEmbedding = embedding != null,
                embeddingModel = embedding?.modelName,
                metadata = chunk.metadata + (document?.metadata ?: emptyMap())
            )
        }
    }
}

data class MemorySessionResponse(
    val id: UUID,
    val userId: String?,
    val sessionName: String?,
    val contextData: Map<String, Any>,
    val lastAccessedAt: OffsetDateTime,
    val createdAt: OffsetDateTime,
    val expiresAt: OffsetDateTime?,
    val isActive: Boolean
) {
    companion object {
        fun fromEntity(session: MemorySession): MemorySessionResponse {
            return MemorySessionResponse(
                id = session.id,
                userId = session.userId,
                sessionName = session.sessionName,
                contextData = session.contextData,
                lastAccessedAt = session.lastAccessedAt,
                createdAt = session.createdAt,
                expiresAt = session.expiresAt,
                isActive = session.isActive
            )
        }
    }
}

data class HealthResponse(
    val status: String,
    val documentCount: Int,
    val chunkCount: Int,
    val embeddingCount: Int,
    val averageQueryTimeMs: Double,
    val elasticsearchHealthy: Boolean,
    val postgresHealthy: Boolean = true,
    val cacheStatus: String = "healthy",
    val timestamp: OffsetDateTime
)

data class PagedResponse<T>(
    val content: List<T>,
    val page: Int,
    val size: Int,
    val totalElements: Long,
    val totalPages: Int,
    val first: Boolean,
    val last: Boolean,
    val numberOfElements: Int = content.size,
    val empty: Boolean = content.isEmpty()
)

// ==================== ANALYTICS DTOs ====================

data class SearchAnalyticsResponse(
    val sessionId: UUID,
    val totalQueries: Int,
    val averageExecutionTimeMs: Double,
    val averageResultCount: Double,
    val successRate: Double,
    val mostCommonQueryType: String,
    val recentQueries: List<RecentQueryInfo>
)

data class RecentQueryInfo(
    val query: String,
    val queryType: String,
    val resultCount: Int,
    val executionTimeMs: Int,
    val timestamp: OffsetDateTime
)

data class SystemAnalyticsResponse(
    val period: AnalyticsPeriod,
    val totalQueries: Int,
    val uniqueSessions: Int,
    val averageExecutionTimeMs: Double,
    val successRate: Double,
    val topQueries: List<PopularQuery>,
    val queryTypeDistribution: Map<String, Int>,
    val performanceMetrics: PerformanceMetrics
)

data class PopularQuery(
    val query: String,
    val count: Int,
    val averageScore: Double,
    val averageExecutionTimeMs: Double
)

data class PerformanceMetrics(
    val fastQueries: Int,      // < 1s
    val moderateQueries: Int,  // 1-5s
    val slowQueries: Int,      // > 5s
    val averageResultsPerQuery: Double,
    val cacheHitRate: Double
)

data class AnalyticsPeriod(
    val startDate: OffsetDateTime,
    val endDate: OffsetDateTime,
    val durationDays: Int
)

// ==================== ERROR DTOs ====================

data class ErrorResponse(
    val error: String,
    val message: String,
    val timestamp: OffsetDateTime = OffsetDateTime.now(),
    val path: String? = null,
    val details: Map<String, Any> = emptyMap()
)

data class ValidationErrorResponse(
    val error: String = "Validation Failed",
    val message: String,
    val timestamp: OffsetDateTime = OffsetDateTime.now(),
    val fieldErrors: List<FieldError>
)

data class FieldError(
    val field: String,
    val rejectedValue: Any?,
    val message: String
)

// ==================== UTILITY DTOs ====================

data class BulkIngestRequest(
    val documents: List<DocumentIngestRequest>,
    val batchSize: Int = 10,
    val continueOnError: Boolean = true
)

data class BulkIngestResponse(
    val totalDocuments: Int,
    val successfulIngests: Int,
    val failedIngests: Int,
    val results: List<BulkIngestResult>
)

data class BulkIngestResult(
    val index: Int,
    val title: String,
    val success: Boolean,
    val documentId: UUID? = null,
    val error: String? = null
)

data class ExportRequest(
    val format: ExportFormat = ExportFormat.JSON,
    val includeContent: Boolean = false,
    val dateRange: DateRange? = null,
    val documentIds: List<UUID> = emptyList()
)

enum class ExportFormat {
    JSON, CSV, MARKDOWN
}

data class DateRange(
    val startDate: OffsetDateTime,
    val endDate: OffsetDateTime
)

data class ExportResponse(
    val downloadUrl: String,
    val fileName: String,
    val fileSize: Long,
    val format: ExportFormat,
    val expiresAt: OffsetDateTime
)

// ==================== OPENCLAW COMPATIBILITY DTOs ====================

/**
 * OpenClaw-compatible chat request
 * Provides backward compatibility with OpenClaw's chat API
 */
data class ChatRequest(
    val message: String,
    val sessionId: String? = null,
    val userId: String? = null,
    val maxResults: Int = 6,
    val minScore: Double = 0.35
)

/**
 * OpenClaw-compatible chat response
 * Provides backward compatibility with OpenClaw's chat API
 */
data class ChatResponse(
    val text: String,
    val citations: List<Citation>,
    val usedKbIds: List<String>,
    val kbVersion: String = "1.0"
)

data class Citation(
    val source: String,
    val excerpt: String,
    val score: Double,
    val lineRange: String? = null
)

/**
 * OpenClaw-compatible ingest request
 */
data class IngestTextRequest(
    val name: String,
    val content: String,
    val metadata: Map<String, Any> = emptyMap()
)

/**
 * OpenClaw-compatible status response
 */
data class StatusResponse(
    val backend: String = "leader-toolbox",
    val documentsIndexed: Int,
    val chunksIndexed: Int,
    val embeddingsGenerated: Int,
    val searchCapabilities: List<String> = listOf("semantic", "keyword", "hybrid"),
    val health: String
)