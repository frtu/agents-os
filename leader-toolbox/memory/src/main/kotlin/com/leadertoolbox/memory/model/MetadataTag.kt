package com.leadertoolbox.memory.model

import jakarta.persistence.*
import org.hibernate.annotations.CreationTimestamp
import java.time.OffsetDateTime
import java.util.*

/**
 * Metadata Tag Entity
 *
 * Provides a flexible tagging system for documents and chunks,
 * enabling categorization, filtering, and organization.
 */
@Entity
@Table(
    name = "metadata_tags",
    indexes = [
        Index(name = "idx_metadata_tags_name", columnList = "tag_name"),
        Index(name = "idx_metadata_tags_type_target", columnList = "target_type, target_id"),
        Index(name = "idx_metadata_tags_name_type", columnList = "tag_name, target_type")
    ],
    uniqueConstraints = [
        UniqueConstraint(name = "uk_tag_target", columnNames = ["tag_name", "target_type", "target_id"])
    ]
)
data class MetadataTag(
    @Id
    @Column(columnDefinition = "uuid")
    val id: UUID = UUID.randomUUID(),

    @Column(name = "tag_name", length = 100, nullable = false)
    val tagName: String,

    @Column(name = "tag_value", columnDefinition = "TEXT")
    val tagValue: String? = null,

    @Column(name = "tag_type", length = 50, nullable = false)
    val tagType: String = "general",

    @Enumerated(EnumType.STRING)
    @Column(name = "target_type", length = 20, nullable = false)
    val targetType: TargetType,

    @Column(name = "target_id", nullable = false, columnDefinition = "uuid")
    val targetId: UUID,

    @CreationTimestamp
    @Column(name = "created_at", nullable = false)
    val createdAt: OffsetDateTime = OffsetDateTime.now()
) {
    // Note: Polymorphic relationship to target handled in service layer
    // target can be either MemoryDocument or MemoryChunk based on targetType

    /**
     * Check if this is a simple tag (no value)
     */
    val isSimpleTag: Boolean
        get() = tagValue.isNullOrBlank()

    /**
     * Check if this is a key-value tag
     */
    val isKeyValueTag: Boolean
        get() = !tagValue.isNullOrBlank()

    /**
     * Get display text for this tag
     */
    fun getDisplayText(): String {
        return if (isKeyValueTag) {
            "$tagName: $tagValue"
        } else {
            tagName
        }
    }

    /**
     * Check if tag matches a search pattern
     */
    fun matches(pattern: String, ignoreCase: Boolean = true): Boolean {
        val searchPattern = if (ignoreCase) pattern.lowercase() else pattern
        val tagText = if (ignoreCase) getDisplayText().lowercase() else getDisplayText()
        return tagText.contains(searchPattern)
    }

    enum class TargetType {
        DOCUMENT,
        CHUNK
    }

    companion object {
        const val MAX_TAG_NAME_LENGTH = 100
        const val MAX_TAG_TYPE_LENGTH = 50

        /**
         * Common tag types
         */
        object Types {
            const val GENERAL = "general"
            const val CATEGORY = "category"
            const val PRIORITY = "priority"
            const val STATUS = "status"
            const val SOURCE = "source"
            const val AUTHOR = "author"
            const val LANGUAGE = "language"
            const val FORMAT = "format"
            const val TOPIC = "topic"
            const val CUSTOM = "custom"
        }

        /**
         * Create a simple tag (name only)
         */
        fun createSimpleTag(
            tagName: String,
            targetType: TargetType,
            targetId: UUID,
            tagType: String = Types.GENERAL
        ): MetadataTag {
            return MetadataTag(
                tagName = tagName.take(MAX_TAG_NAME_LENGTH),
                targetType = targetType,
                targetId = targetId,
                tagType = tagType.take(MAX_TAG_TYPE_LENGTH)
            )
        }

        /**
         * Create a key-value tag
         */
        fun createKeyValueTag(
            tagName: String,
            tagValue: String,
            targetType: TargetType,
            targetId: UUID,
            tagType: String = Types.GENERAL
        ): MetadataTag {
            return MetadataTag(
                tagName = tagName.take(MAX_TAG_NAME_LENGTH),
                tagValue = tagValue,
                targetType = targetType,
                targetId = targetId,
                tagType = tagType.take(MAX_TAG_TYPE_LENGTH)
            )
        }

        /**
         * Create tags for common document properties
         */
        fun createDocumentTags(
            documentId: UUID,
            category: String? = null,
            priority: String? = null,
            author: String? = null,
            language: String? = null,
            customTags: Map<String, String> = emptyMap()
        ): List<MetadataTag> {
            val tags = mutableListOf<MetadataTag>()

            category?.let {
                tags.add(createKeyValueTag("category", it, TargetType.DOCUMENT, documentId, Types.CATEGORY))
            }

            priority?.let {
                tags.add(createKeyValueTag("priority", it, TargetType.DOCUMENT, documentId, Types.PRIORITY))
            }

            author?.let {
                tags.add(createKeyValueTag("author", it, TargetType.DOCUMENT, documentId, Types.AUTHOR))
            }

            language?.let {
                tags.add(createKeyValueTag("language", it, TargetType.DOCUMENT, documentId, Types.LANGUAGE))
            }

            customTags.forEach { (key, value) ->
                tags.add(createKeyValueTag(key, value, TargetType.DOCUMENT, documentId, Types.CUSTOM))
            }

            return tags
        }

        /**
         * Create tags for chunk-specific properties
         */
        fun createChunkTags(
            chunkId: UUID,
            contentType: String? = null,
            topic: String? = null,
            customTags: Map<String, String> = emptyMap()
        ): List<MetadataTag> {
            val tags = mutableListOf<MetadataTag>()

            contentType?.let {
                tags.add(createKeyValueTag("content_type", it, TargetType.CHUNK, chunkId, Types.FORMAT))
            }

            topic?.let {
                tags.add(createKeyValueTag("topic", it, TargetType.CHUNK, chunkId, Types.TOPIC))
            }

            customTags.forEach { (key, value) ->
                tags.add(createKeyValueTag(key, value, TargetType.CHUNK, chunkId, Types.CUSTOM))
            }

            return tags
        }

        /**
         * Parse tag string in format "name:value" or just "name"
         */
        fun parseTagString(
            tagString: String,
            targetType: TargetType,
            targetId: UUID,
            tagType: String = Types.GENERAL
        ): MetadataTag {
            val parts = tagString.split(":", limit = 2)
            return if (parts.size == 2) {
                createKeyValueTag(
                    tagName = parts[0].trim(),
                    tagValue = parts[1].trim(),
                    targetType = targetType,
                    targetId = targetId,
                    tagType = tagType
                )
            } else {
                createSimpleTag(
                    tagName = parts[0].trim(),
                    targetType = targetType,
                    targetId = targetId,
                    tagType = tagType
                )
            }
        }

        /**
         * Batch create tags from string list
         */
        fun parseTagStrings(
            tagStrings: List<String>,
            targetType: TargetType,
            targetId: UUID,
            defaultTagType: String = Types.GENERAL
        ): List<MetadataTag> {
            return tagStrings.mapNotNull { tagString ->
                if (tagString.isNotBlank()) {
                    parseTagString(tagString.trim(), targetType, targetId, defaultTagType)
                } else null
            }
        }
    }
}

/**
 * Tag Query Helper
 *
 * Provides helper functions for tag-based queries and filters.
 */
object TagQueryHelper {
    /**
     * Build tag filter for documents
     */
    fun buildDocumentTagFilter(tags: Map<String, String>): String {
        return tags.entries.joinToString(" AND ") { (key, value) ->
            "EXISTS (SELECT 1 FROM metadata_tags mt WHERE mt.target_type = 'DOCUMENT' " +
                    "AND mt.target_id = md.id AND mt.tag_name = '$key' AND mt.tag_value = '$value')"
        }
    }

    /**
     * Build tag filter for chunks
     */
    fun buildChunkTagFilter(tags: Map<String, String>): String {
        return tags.entries.joinToString(" AND ") { (key, value) ->
            "EXISTS (SELECT 1 FROM metadata_tags mt WHERE mt.target_type = 'CHUNK' " +
                    "AND mt.target_id = mc.id AND mt.tag_name = '$key' AND mt.tag_value = '$value')"
        }
    }

    /**
     * Extract tag map from tag list
     */
    fun extractTagMap(tags: List<MetadataTag>): Map<String, String?> {
        return tags.associate { tag ->
            tag.tagName to tag.tagValue
        }
    }

    /**
     * Group tags by type
     */
    fun groupByType(tags: List<MetadataTag>): Map<String, List<MetadataTag>> {
        return tags.groupBy { it.tagType }
    }

    /**
     * Filter tags by type
     */
    fun filterByType(tags: List<MetadataTag>, type: String): List<MetadataTag> {
        return tags.filter { it.tagType == type }
    }
}