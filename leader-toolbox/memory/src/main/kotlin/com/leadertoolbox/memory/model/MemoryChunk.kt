package com.leadertoolbox.memory.model

import com.fasterxml.jackson.annotation.JsonIgnore
import jakarta.persistence.*
import org.hibernate.annotations.CreationTimestamp
import org.hibernate.annotations.JdbcTypeCode
import org.hibernate.type.SqlTypes
import java.time.OffsetDateTime
import java.util.*

/**
 * Memory Chunk Entity
 *
 * Represents a text chunk extracted from a document with position tracking,
 * token counting, and content hashing for change detection.
 */
@Entity
@Table(
    name = "memory_chunks",
    indexes = [
        Index(name = "idx_memory_chunks_document_id", columnList = "document_id"),
        Index(name = "idx_memory_chunks_content_hash", columnList = "content_hash"),
        Index(name = "idx_chunks_document_chunk_index", columnList = "document_id, chunk_index")
    ],
    uniqueConstraints = [
        UniqueConstraint(name = "uk_document_chunk", columnNames = ["document_id", "chunk_index"])
    ]
)
data class MemoryChunk(
    @Id
    @Column(columnDefinition = "uuid")
    val id: UUID = UUID.randomUUID(),

    @Column(name = "document_id", nullable = false, columnDefinition = "uuid")
    val documentId: UUID,

    @Column(name = "chunk_index", nullable = false)
    val chunkIndex: Int,

    @Column(name = "content", nullable = false, columnDefinition = "TEXT")
    val content: String,

    @Column(name = "token_count", nullable = false)
    val tokenCount: Int,

    @Column(name = "char_start_pos", nullable = false)
    val charStartPos: Int,

    @Column(name = "char_end_pos", nullable = false)
    val charEndPos: Int,

    @Column(name = "content_hash", length = 64, nullable = false)
    val contentHash: String,

    @JdbcTypeCode(SqlTypes.JSON)
    @Column(name = "metadata", columnDefinition = "jsonb")
    val metadata: Map<String, @JvmSuppressWildcards Any> = emptyMap(),

    @CreationTimestamp
    @Column(name = "created_at", nullable = false)
    val createdAt: OffsetDateTime = OffsetDateTime.now()
) {
    // Relationships
    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "document_id", insertable = false, updatable = false)
    @JsonIgnore
    val document: MemoryDocument? = null

    @OneToOne(mappedBy = "chunk", cascade = [CascadeType.ALL], fetch = FetchType.LAZY)
    @JsonIgnore
    val embedding: ChunkEmbedding? = null

    // Note: Tags relationship handled in service layer due to polymorphic nature

    // Computed properties
    val length: Int
        get() = charEndPos - charStartPos

    val excerpt: String
        get() = content.take(400) + if (content.length > 400) "..." else ""

    /**
     * Check if this chunk has embeddings
     */
    fun hasEmbedding(): Boolean = embedding != null

    /**
     * Get relative position in document (0.0 to 1.0)
     */
    fun getRelativePosition(): Double {
        return if (charEndPos > 0) charStartPos.toDouble() / charEndPos else 0.0
    }

    /**
     * Check if chunk content has changed based on hash
     */
    fun hasContentChanged(newContent: String): Boolean {
        return contentHash != generateContentHash(newContent)
    }

    companion object {
        const val DEFAULT_EXCERPT_LENGTH = 400

        /**
         * Create a MemoryChunk from text content
         */
        fun fromContent(
            documentId: UUID,
            chunkIndex: Int,
            content: String,
            charStartPos: Int,
            charEndPos: Int,
            tokenCount: Int = estimateTokenCount(content),
            metadata: Map<String, Any> = emptyMap()
        ): MemoryChunk {
            val contentHash = generateContentHash(content)
            return MemoryChunk(
                documentId = documentId,
                chunkIndex = chunkIndex,
                content = content,
                tokenCount = tokenCount,
                charStartPos = charStartPos,
                charEndPos = charEndPos,
                contentHash = contentHash,
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

        /**
         * Estimate token count based on character count
         * This is a rough approximation: ~4 characters per token for English
         */
        private fun estimateTokenCount(content: String): Int {
            // Simple heuristic: split by whitespace and punctuation
            val words = content.split(Regex("\\s+|[,.!?;:]")).filter { it.isNotBlank() }
            return maxOf(words.size, content.length / 4)
        }

        /**
         * Create chunks from a larger text
         */
        fun createChunks(
            documentId: UUID,
            content: String,
            chunkSize: Int = 1000,
            overlap: Int = 200
        ): List<MemoryChunk> {
            if (content.length <= chunkSize) {
                return listOf(
                    fromContent(
                        documentId = documentId,
                        chunkIndex = 0,
                        content = content,
                        charStartPos = 0,
                        charEndPos = content.length
                    )
                )
            }

            val chunks = mutableListOf<MemoryChunk>()
            var currentPos = 0
            var chunkIndex = 0

            while (currentPos < content.length) {
                val endPos = minOf(currentPos + chunkSize, content.length)

                // Try to end at a natural boundary (sentence, paragraph, or at least word boundary)
                val adjustedEndPos = if (endPos < content.length) {
                    findNaturalBreakpoint(content, currentPos, endPos)
                } else {
                    endPos
                }

                val chunkContent = content.substring(currentPos, adjustedEndPos)

                chunks.add(
                    fromContent(
                        documentId = documentId,
                        chunkIndex = chunkIndex,
                        content = chunkContent,
                        charStartPos = currentPos,
                        charEndPos = adjustedEndPos
                    )
                )

                currentPos = adjustedEndPos - overlap
                if (currentPos <= chunks.lastOrNull()?.charStartPos ?: -1) {
                    currentPos = adjustedEndPos // Avoid infinite loop
                }
                chunkIndex++
            }

            return chunks
        }

        /**
         * Find a natural breakpoint for chunk boundaries
         */
        private fun findNaturalBreakpoint(content: String, start: Int, maxEnd: Int): Int {
            // Look for paragraph break first
            val paragraphBreak = content.lastIndexOf("\n\n", maxEnd)
            if (paragraphBreak > start) return paragraphBreak

            // Look for sentence end
            val sentenceEnd = content.lastIndexOfAny(charArrayOf('.', '!', '?'), maxEnd)
            if (sentenceEnd > start && sentenceEnd < maxEnd - 10) return sentenceEnd + 1

            // Look for word boundary
            val wordBoundary = content.lastIndexOf(' ', maxEnd)
            if (wordBoundary > start) return wordBoundary

            // If no natural boundary found, use max end
            return maxEnd
        }
    }
}