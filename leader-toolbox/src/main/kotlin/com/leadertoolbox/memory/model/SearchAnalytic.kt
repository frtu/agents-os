package com.leadertoolbox.memory.model

import com.fasterxml.jackson.annotation.JsonIgnore
import jakarta.persistence.*
import org.hibernate.annotations.CreationTimestamp
import java.time.OffsetDateTime
import java.util.*

/**
 * Search Analytics Entity
 *
 * Tracks search queries, performance metrics, and usage patterns
 * for the memory system to enable optimization and insights.
 */
@Entity
@Table(
    name = "search_analytics",
    indexes = [
        Index(name = "idx_search_analytics_session", columnList = "session_id"),
        Index(name = "idx_search_analytics_query_type", columnList = "query_type"),
        Index(name = "idx_search_analytics_created_at", columnList = "created_at")
    ]
)
data class SearchAnalytic(
    @Id
    @Column(columnDefinition = "uuid")
    val id: UUID = UUID.randomUUID(),

    @Column(name = "session_id", columnDefinition = "uuid")
    val sessionId: UUID? = null,

    @Column(name = "query_text", nullable = false, columnDefinition = "TEXT")
    val queryText: String,

    @Enumerated(EnumType.STRING)
    @Column(name = "query_type", length = 20, nullable = false)
    val queryType: QueryType,

    @Column(name = "result_count", nullable = false)
    val resultCount: Int = 0,

    @Column(name = "execution_time_ms", nullable = false)
    val executionTimeMs: Int,

    @Column(name = "top_score")
    val topScore: Float? = null,

    @CreationTimestamp
    @Column(name = "created_at", nullable = false)
    val createdAt: OffsetDateTime = OffsetDateTime.now()
) {
    // Relationships
    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "session_id", insertable = false, updatable = false)
    @JsonIgnore
    val session: MemorySession? = null

    // Computed properties
    val executionTimeSeconds: Double
        get() = executionTimeMs / 1000.0

    val hasResults: Boolean
        get() = resultCount > 0

    val isSlowQuery: Boolean
        get() = executionTimeMs > SLOW_QUERY_THRESHOLD_MS

    val isHighQualityResults: Boolean
        get() = topScore?.let { it >= HIGH_QUALITY_SCORE_THRESHOLD } ?: false

    /**
     * Check if this query was successful (returned results in reasonable time)
     */
    fun isSuccessful(): Boolean {
        return hasResults && !isSlowQuery
    }

    /**
     * Get performance rating (1-5 stars)
     */
    fun getPerformanceRating(): Int {
        return when {
            !hasResults -> 1
            isSlowQuery -> 2
            executionTimeMs > MODERATE_QUERY_THRESHOLD_MS -> 3
            topScore?.let { it >= HIGH_QUALITY_SCORE_THRESHOLD } == true -> 5
            else -> 4
        }
    }

    /**
     * Get query complexity estimate based on length and content
     */
    fun getComplexityEstimate(): QueryComplexity {
        val wordCount = queryText.split("\\s+".toRegex()).size
        val hasSpecialChars = queryText.contains(Regex("[\"'\\*\\+\\-\\(\\)\\[\\]]"))

        return when {
            wordCount > 20 || hasSpecialChars -> QueryComplexity.HIGH
            wordCount > 10 -> QueryComplexity.MEDIUM
            wordCount > 5 -> QueryComplexity.MODERATE
            else -> QueryComplexity.LOW
        }
    }

    enum class QueryType {
        SEMANTIC,   // Vector similarity search
        KEYWORD,    // Text-based search
        HYBRID      // Combined semantic + keyword
    }

    enum class QueryComplexity {
        LOW, MODERATE, MEDIUM, HIGH
    }

    companion object {
        const val SLOW_QUERY_THRESHOLD_MS = 5000      // 5 seconds
        const val MODERATE_QUERY_THRESHOLD_MS = 2000  // 2 seconds
        const val HIGH_QUALITY_SCORE_THRESHOLD = 0.8f

        /**
         * Create search analytic record
         */
        fun create(
            sessionId: UUID? = null,
            queryText: String,
            queryType: QueryType,
            resultCount: Int,
            executionTimeMs: Int,
            topScore: Float? = null
        ): SearchAnalytic {
            return SearchAnalytic(
                sessionId = sessionId,
                queryText = queryText,
                queryType = queryType,
                resultCount = resultCount,
                executionTimeMs = executionTimeMs,
                topScore = topScore
            )
        }

        /**
         * Create from search execution
         */
        fun fromSearchExecution(
            sessionId: UUID? = null,
            queryText: String,
            queryType: QueryType,
            results: List<Any>,
            startTime: Long,
            topScore: Float? = null
        ): SearchAnalytic {
            val executionTime = (System.currentTimeMillis() - startTime).toInt()
            return create(
                sessionId = sessionId,
                queryText = queryText,
                queryType = queryType,
                resultCount = results.size,
                executionTimeMs = executionTime,
                topScore = topScore
            )
        }
    }
}

/**
 * Search Analytics Service Helper
 *
 * Provides utility functions for analyzing search patterns and performance.
 */
object SearchAnalyticsHelper {

    /**
     * Calculate average query performance metrics
     */
    data class PerformanceMetrics(
        val avgExecutionTimeMs: Double,
        val avgResultCount: Double,
        val avgTopScore: Double?,
        val successRate: Double,
        val slowQueryRate: Double,
        val totalQueries: Int
    )

    /**
     * Query pattern analysis
     */
    data class QueryPatterns(
        val mostCommonQueryType: SearchAnalytic.QueryType,
        val avgQueryLength: Double,
        val mostCommonWords: List<Pair<String, Int>>,
        val queryComplexityDistribution: Map<SearchAnalytic.QueryComplexity, Int>
    )

    /**
     * Calculate performance metrics from analytics
     */
    fun calculatePerformanceMetrics(analytics: List<SearchAnalytic>): PerformanceMetrics {
        if (analytics.isEmpty()) {
            return PerformanceMetrics(0.0, 0.0, null, 0.0, 0.0, 0)
        }

        val avgExecutionTime = analytics.map { it.executionTimeMs }.average()
        val avgResultCount = analytics.map { it.resultCount }.average()
        val scoresWithValues = analytics.mapNotNull { it.topScore }
        val avgTopScore = if (scoresWithValues.isNotEmpty()) {
            scoresWithValues.average()
        } else null

        val successCount = analytics.count { it.isSuccessful() }
        val successRate = successCount.toDouble() / analytics.size

        val slowQueryCount = analytics.count { it.isSlowQuery }
        val slowQueryRate = slowQueryCount.toDouble() / analytics.size

        return PerformanceMetrics(
            avgExecutionTimeMs = avgExecutionTime,
            avgResultCount = avgResultCount,
            avgTopScore = avgTopScore,
            successRate = successRate,
            slowQueryRate = slowQueryRate,
            totalQueries = analytics.size
        )
    }

    /**
     * Analyze query patterns
     */
    fun analyzeQueryPatterns(analytics: List<SearchAnalytic>): QueryPatterns {
        if (analytics.isEmpty()) {
            return QueryPatterns(
                SearchAnalytic.QueryType.HYBRID,
                0.0,
                emptyList(),
                emptyMap()
            )
        }

        // Most common query type
        val queryTypeCounts = analytics.groupingBy { it.queryType }.eachCount()
        val mostCommonQueryType = queryTypeCounts.maxByOrNull { it.value }?.key
            ?: SearchAnalytic.QueryType.HYBRID

        // Average query length
        val avgQueryLength = analytics.map { it.queryText.length }.average()

        // Most common words (excluding common stop words)
        val stopWords = setOf("the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by")
        val allWords = analytics.flatMap { analytic ->
            analytic.queryText.lowercase()
                .split("\\s+".toRegex())
                .filter { it.isNotBlank() && it !in stopWords }
        }
        val wordCounts = allWords.groupingBy { it }.eachCount()
        val mostCommonWords = wordCounts.toList()
            .sortedByDescending { it.second }
            .take(10)

        // Query complexity distribution
        val complexityDistribution = analytics
            .map { it.getComplexityEstimate() }
            .groupingBy { it }
            .eachCount()

        return QueryPatterns(
            mostCommonQueryType = mostCommonQueryType,
            avgQueryLength = avgQueryLength,
            mostCommonWords = mostCommonWords,
            queryComplexityDistribution = complexityDistribution
        )
    }

    /**
     * Get performance insights and recommendations
     */
    fun getPerformanceInsights(metrics: PerformanceMetrics): List<String> {
        val insights = mutableListOf<String>()

        if (metrics.slowQueryRate > 0.2) {
            insights.add("High slow query rate (${String.format("%.1f", metrics.slowQueryRate * 100)}%) - consider optimizing indexes")
        }

        if (metrics.avgResultCount < 1.0) {
            insights.add("Low average result count - query matching may need improvement")
        }

        if (metrics.successRate < 0.7) {
            insights.add("Low success rate (${String.format("%.1f", metrics.successRate * 100)}%) - review query processing")
        }

        if (metrics.avgExecutionTimeMs > SearchAnalytic.SLOW_QUERY_THRESHOLD_MS) {
            insights.add("High average execution time - database optimization recommended")
        }

        if (metrics.avgTopScore != null && metrics.avgTopScore < 0.5) {
            insights.add("Low average relevance scores - embedding model or chunking strategy may need adjustment")
        }

        if (insights.isEmpty()) {
            insights.add("Search performance looks good!")
        }

        return insights
    }

    /**
     * Generate performance report
     */
    fun generatePerformanceReport(analytics: List<SearchAnalytic>): Map<String, Any> {
        val metrics = calculatePerformanceMetrics(analytics)
        val patterns = analyzeQueryPatterns(analytics)
        val insights = getPerformanceInsights(metrics)

        return mapOf(
            "period" to mapOf(
                "start" to (analytics.minByOrNull { it.createdAt }?.createdAt),
                "end" to (analytics.maxByOrNull { it.createdAt }?.createdAt),
                "total_queries" to analytics.size
            ),
            "performance" to mapOf(
                "avg_execution_time_ms" to metrics.avgExecutionTimeMs,
                "avg_result_count" to metrics.avgResultCount,
                "avg_top_score" to metrics.avgTopScore,
                "success_rate" to metrics.successRate,
                "slow_query_rate" to metrics.slowQueryRate
            ),
            "patterns" to mapOf(
                "most_common_query_type" to patterns.mostCommonQueryType,
                "avg_query_length" to patterns.avgQueryLength,
                "top_words" to patterns.mostCommonWords.take(5),
                "complexity_distribution" to patterns.queryComplexityDistribution
            ),
            "insights" to insights
        )
    }
}