package com.leadertoolbox.memory.model

import com.fasterxml.jackson.annotation.JsonIgnore
import jakarta.persistence.*
import org.hibernate.annotations.CreationTimestamp
import org.hibernate.annotations.JdbcTypeCode
import org.hibernate.type.SqlTypes
import java.time.OffsetDateTime
import java.util.*

/**
 * Memory Session Entity
 *
 * Tracks user sessions and conversation context for the memory system.
 * Provides session-scoped memory and context management.
 */
@Entity
@Table(
    name = "memory_sessions",
    indexes = [
        Index(name = "idx_memory_sessions_user_id", columnList = "user_id"),
        Index(name = "idx_memory_sessions_last_accessed", columnList = "last_accessed_at")
    ]
)
data class MemorySession(
    @Id
    @Column(columnDefinition = "uuid")
    val id: UUID = UUID.randomUUID(),

    @Column(name = "user_id", length = 100)
    val userId: String? = null,

    @Column(name = "session_name", length = 200)
    val sessionName: String? = null,

    @JdbcTypeCode(SqlTypes.JSON)
    @Column(name = "context_data", columnDefinition = "jsonb")
    val contextData: Map<String, @JvmSuppressWildcards Any> = emptyMap(),

    @Column(name = "last_accessed_at", nullable = false)
    val lastAccessedAt: OffsetDateTime = OffsetDateTime.now(),

    @CreationTimestamp
    @Column(name = "created_at", nullable = false)
    val createdAt: OffsetDateTime = OffsetDateTime.now(),

    @Column(name = "expires_at")
    val expiresAt: OffsetDateTime? = null
) {
    // Relationships
    @OneToMany(mappedBy = "session", cascade = [CascadeType.ALL], fetch = FetchType.LAZY)
    @JsonIgnore
    val searchAnalytics: List<SearchAnalytic> = mutableListOf()

    // Computed properties
    val isExpired: Boolean
        get() = expiresAt?.isBefore(OffsetDateTime.now()) == true

    val isActive: Boolean
        get() = !isExpired

    val durationSinceCreation: java.time.Duration
        get() = java.time.Duration.between(createdAt, OffsetDateTime.now())

    val durationSinceLastAccess: java.time.Duration
        get() = java.time.Duration.between(lastAccessedAt, OffsetDateTime.now())

    /**
     * Get a display name for this session
     */
    fun getDisplayName(): String {
        return sessionName?.takeIf { it.isNotBlank() }
            ?: userId?.let { "Session for $it" }
            ?: "Anonymous Session ${id.toString().take(8)}"
    }

    /**
     * Check if session belongs to a specific user
     */
    fun belongsToUser(userId: String): Boolean {
        return this.userId == userId
    }

    /**
     * Get context value by key with type casting
     */
    @Suppress("UNCHECKED_CAST")
    fun <T> getContextValue(key: String): T? {
        return contextData[key] as? T
    }

    /**
     * Get context value with default
     */
    fun <T> getContextValue(key: String, default: T): T {
        return getContextValue<T>(key) ?: default
    }

    /**
     * Check if session should be cleaned up (inactive for too long)
     */
    fun shouldCleanup(inactivityThreshold: java.time.Duration = java.time.Duration.ofDays(30)): Boolean {
        return durationSinceLastAccess > inactivityThreshold || isExpired
    }

    companion object {
        const val MAX_SESSION_NAME_LENGTH = 200
        const val MAX_USER_ID_LENGTH = 100

        /**
         * Create a new session for a user
         */
        fun createForUser(
            userId: String,
            sessionName: String? = null,
            contextData: Map<String, Any> = emptyMap(),
            expiresIn: java.time.Duration? = null
        ): MemorySession {
            val expiresAt = expiresIn?.let { OffsetDateTime.now().plus(it) }
            return MemorySession(
                userId = userId.take(MAX_USER_ID_LENGTH),
                sessionName = sessionName?.take(MAX_SESSION_NAME_LENGTH),
                contextData = contextData,
                expiresAt = expiresAt
            )
        }

        /**
         * Create an anonymous session
         */
        fun createAnonymous(
            sessionName: String? = null,
            contextData: Map<String, Any> = emptyMap(),
            expiresIn: java.time.Duration? = java.time.Duration.ofDays(7)
        ): MemorySession {
            val expiresAt = expiresIn?.let { OffsetDateTime.now().plus(it) }
            return MemorySession(
                sessionName = sessionName?.take(MAX_SESSION_NAME_LENGTH),
                contextData = contextData,
                expiresAt = expiresAt
            )
        }

        /**
         * Update session with new context data
         */
        fun MemorySession.withUpdatedContext(
            additionalContext: Map<String, Any>
        ): MemorySession {
            val mergedContext = this.contextData.toMutableMap().apply {
                putAll(additionalContext)
            }
            return this.copy(
                contextData = mergedContext,
                lastAccessedAt = OffsetDateTime.now()
            )
        }

        /**
         * Touch session to update last accessed time
         */
        fun MemorySession.touch(): MemorySession {
            return this.copy(lastAccessedAt = OffsetDateTime.now())
        }
    }
}

/**
 * Memory Session Context Helper
 *
 * Provides typed access to common context data keys.
 */
object MemorySessionContext {
    const val CONVERSATION_HISTORY = "conversation_history"
    const val PREFERENCES = "user_preferences"
    const val SEARCH_FILTERS = "search_filters"
    const val LAST_SEARCH_QUERY = "last_search_query"
    const val ACTIVE_DOCUMENTS = "active_documents"
    const val SEARCH_SCOPE = "search_scope"
    const val UI_STATE = "ui_state"

    /**
     * Get conversation history from session context
     */
    fun MemorySession.getConversationHistory(): List<Map<String, Any>> {
        return getContextValue(CONVERSATION_HISTORY) ?: emptyList()
    }

    /**
     * Get user preferences from session context
     */
    fun MemorySession.getUserPreferences(): Map<String, Any> {
        return getContextValue(PREFERENCES) ?: emptyMap()
    }

    /**
     * Get active document IDs from session context
     */
    fun MemorySession.getActiveDocuments(): List<String> {
        return getContextValue(ACTIVE_DOCUMENTS) ?: emptyList()
    }

    /**
     * Get last search query from session context
     */
    fun MemorySession.getLastSearchQuery(): String? {
        return getContextValue(LAST_SEARCH_QUERY)
    }
}