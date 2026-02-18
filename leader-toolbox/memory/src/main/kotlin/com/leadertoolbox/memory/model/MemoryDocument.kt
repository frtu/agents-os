package com.leadertoolbox.memory.model

import com.fasterxml.jackson.annotation.JsonIgnore
import jakarta.persistence.*
import org.hibernate.annotations.CreationTimestamp
import org.hibernate.annotations.JdbcTypeCode
import org.hibernate.annotations.UpdateTimestamp
import org.hibernate.type.SqlTypes
import java.time.OffsetDateTime
import java.util.*

/**
 * Memory Document Entity
 *
 * Represents a document stored in the memory system with metadata,
 * content hashing, and flexible JSON metadata support.
 */
@Entity
@Table(
    name = "memory_documents",
    indexes = [
        Index(name = "idx_memory_documents_created_at", columnList = "created_at"),
        Index(name = "idx_memory_documents_content_type", columnList = "content_type"),
        Index(name = "idx_memory_documents_title_gin", columnList = "title") // GIN index created in SQL
    ]
)
data class MemoryDocument(
    @Id
    @Column(columnDefinition = "uuid")
    val id: UUID = UUID.randomUUID(),

    @Column(name = "title", length = 500, nullable = false)
    val title: String,

    @Column(name = "content_type", length = 50, nullable = false)
    val contentType: String = "text/plain",

    @Column(name = "source_path", columnDefinition = "TEXT")
    val sourcePath: String? = null,

    @Column(name = "source_url", columnDefinition = "TEXT")
    val sourceUrl: String? = null,

    @Column(name = "content_hash", length = 64, nullable = false)
    val contentHash: String,

    @Column(name = "content_length", nullable = false)
    val contentLength: Int,

    @JdbcTypeCode(SqlTypes.JSON)
    @Column(name = "metadata", columnDefinition = "jsonb")
    val metadata: Map<String, @JvmSuppressWildcards Any> = emptyMap(),

    @CreationTimestamp
    @Column(name = "created_at", nullable = false)
    val createdAt: OffsetDateTime = OffsetDateTime.now(),

    @UpdateTimestamp
    @Column(name = "updated_at", nullable = false)
    val updatedAt: OffsetDateTime = OffsetDateTime.now(),

    @Column(name = "deleted_at")
    val deletedAt: OffsetDateTime? = null
) {
    // Relationships
    @OneToMany(mappedBy = "document", cascade = [CascadeType.ALL], fetch = FetchType.LAZY)
    @JsonIgnore
    val chunks: List<MemoryChunk> = mutableListOf()

    // Note: Tags relationship handled in service layer due to polymorphic nature

    // Computed properties
    val isDeleted: Boolean
        get() = deletedAt != null

    /**
     * Check if this document has a valid source
     */
    fun hasValidSource(): Boolean = sourcePath != null || sourceUrl != null

    /**
     * Get a display name for this document
     */
    fun getDisplayName(): String = title.ifBlank {
        sourcePath?.substringAfterLast('/') ?: sourceUrl?.substringAfterLast('/') ?: "Untitled Document"
    }

    /**
     * Get content type category (text, image, document, etc.)
     */
    fun getContentCategory(): String = contentType.substringBefore('/')

    companion object {
        const val MAX_TITLE_LENGTH = 500
        const val MAX_CONTENT_TYPE_LENGTH = 50
        const val CONTENT_HASH_LENGTH = 64

        /**
         * Create a MemoryDocument from raw content
         */
        fun fromContent(
            title: String,
            content: String,
            contentType: String = "text/plain",
            sourcePath: String? = null,
            sourceUrl: String? = null,
            metadata: Map<String, Any> = emptyMap()
        ): MemoryDocument {
            val contentHash = generateContentHash(content)
            return MemoryDocument(
                title = title.take(MAX_TITLE_LENGTH),
                contentType = contentType.take(MAX_CONTENT_TYPE_LENGTH),
                sourcePath = sourcePath,
                sourceUrl = sourceUrl,
                contentHash = contentHash,
                contentLength = content.length,
                metadata = metadata
            )
        }

        /**
         * Generate SHA-256 hash for content
         */
        private fun generateContentHash(content: String): String {
            return java.security.MessageDigest.getInstance("SHA-256")
                .digest(content.toByteArray())
                .joinToString("") { "%02x".format(it) }
        }
    }
}