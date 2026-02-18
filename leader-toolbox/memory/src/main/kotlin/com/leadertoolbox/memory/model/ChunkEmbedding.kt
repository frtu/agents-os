package com.leadertoolbox.memory.model

import com.fasterxml.jackson.annotation.JsonIgnore
import jakarta.persistence.*
import org.hibernate.annotations.CreationTimestamp
import java.time.OffsetDateTime
import java.util.*
import org.hibernate.annotations.JdbcTypeCode
import org.hibernate.type.SqlTypes

/**
 * Chunk Embedding Entity
 *
 * Stores vector embeddings for memory chunks, supporting both PostgreSQL arrays
 * and pgvector formats for optimized vector operations.
 */
@Entity
@Table(
    name = "chunk_embeddings",
    indexes = [
        Index(name = "idx_chunk_embeddings_model", columnList = "model_name")
    ]
)
data class ChunkEmbedding(
    @Id
    @Column(name = "chunk_id", columnDefinition = "uuid")
    val chunkId: UUID,

    @Column(name = "embedding_vector", nullable = false, columnDefinition = "real[]")
    val embeddingVector: FloatArray,

    @JdbcTypeCode(SqlTypes.ARRAY)
    @Column(name = "model_name", length = 100, nullable = false)
    val modelName: String = DEFAULT_MODEL_NAME,

    @Column(name = "vector_dimension", nullable = false)
    val vectorDimension: Int = DEFAULT_VECTOR_DIMENSION,

    @CreationTimestamp
    @Column(name = "created_at", nullable = false)
    val createdAt: OffsetDateTime = OffsetDateTime.now()
) {
    // Relationships
    @OneToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "chunk_id")
    @JsonIgnore
    val chunk: MemoryChunk? = null

    // Computed properties
    val magnitude: Double by lazy {
        kotlin.math.sqrt(embeddingVector.map { it.toDouble() * it }.sum())
    }

    val normalizedVector: FloatArray by lazy {
        val mag = magnitude.toFloat()
        if (mag > 0) embeddingVector.map { it / mag }.toFloatArray()
        else embeddingVector
    }

    /**
     * Calculate cosine similarity with another embedding
     */
    fun cosineSimilarity(other: ChunkEmbedding): Double {
        return cosineSimilarity(other.embeddingVector)
    }

    /**
     * Calculate cosine similarity with a vector
     */
    fun cosineSimilarity(otherVector: FloatArray): Double {
        if (embeddingVector.size != otherVector.size) {
            throw IllegalArgumentException(
                "Vector dimensions don't match: ${embeddingVector.size} vs ${otherVector.size}"
            )
        }

        var dotProduct = 0.0
        var norm1 = 0.0
        var norm2 = 0.0

        for (i in embeddingVector.indices) {
            dotProduct += embeddingVector[i] * otherVector[i]
            norm1 += embeddingVector[i] * embeddingVector[i]
            norm2 += otherVector[i] * otherVector[i]
        }

        return if (norm1 > 0 && norm2 > 0) {
            dotProduct / (kotlin.math.sqrt(norm1) * kotlin.math.sqrt(norm2))
        } else {
            0.0
        }
    }

    /**
     * Calculate L2 (Euclidean) distance with another embedding
     */
    fun l2Distance(other: ChunkEmbedding): Double {
        return l2Distance(other.embeddingVector)
    }

    /**
     * Calculate L2 distance with a vector
     */
    fun l2Distance(otherVector: FloatArray): Double {
        if (embeddingVector.size != otherVector.size) {
            throw IllegalArgumentException(
                "Vector dimensions don't match: ${embeddingVector.size} vs ${otherVector.size}"
            )
        }

        var sumSquares = 0.0
        for (i in embeddingVector.indices) {
            val diff = embeddingVector[i] - otherVector[i]
            sumSquares += diff * diff
        }

        return kotlin.math.sqrt(sumSquares)
    }

    /**
     * Validate that the embedding has the correct dimension
     */
    fun isValidDimension(): Boolean {
        return embeddingVector.size == vectorDimension
    }

    /**
     * Check if this embedding is for a specific model
     */
    fun isFromModel(modelName: String): Boolean {
        return this.modelName.equals(modelName, ignoreCase = true)
    }

    override fun equals(other: Any?): Boolean {
        if (this === other) return true
        if (javaClass != other?.javaClass) return false

        other as ChunkEmbedding

        if (chunkId != other.chunkId) return false
        if (!embeddingVector.contentEquals(other.embeddingVector)) return false
        if (modelName != other.modelName) return false
        if (vectorDimension != other.vectorDimension) return false

        return true
    }

    override fun hashCode(): Int {
        var result = chunkId.hashCode()
        result = 31 * result + embeddingVector.contentHashCode()
        result = 31 * result + modelName.hashCode()
        result = 31 * result + vectorDimension
        return result
    }

    override fun toString(): String {
        return "ChunkEmbedding(chunkId=$chunkId, modelName='$modelName', dimension=$vectorDimension, " +
                "magnitude=${String.format("%.4f", magnitude)})"
    }

    companion object {
        const val DEFAULT_MODEL_NAME = "all-MiniLM-L6-v2"
        const val DEFAULT_VECTOR_DIMENSION = 384

        /**
         * Create embedding from vector array
         */
        fun fromVector(
            chunkId: UUID,
            vector: FloatArray,
            modelName: String = DEFAULT_MODEL_NAME
        ): ChunkEmbedding {
            return ChunkEmbedding(
                chunkId = chunkId,
                embeddingVector = vector,
                modelName = modelName,
                vectorDimension = vector.size
            )
        }

        /**
         * Create embedding from list of doubles
         */
        fun fromDoubleList(
            chunkId: UUID,
            vector: List<Double>,
            modelName: String = DEFAULT_MODEL_NAME
        ): ChunkEmbedding {
            return fromVector(
                chunkId = chunkId,
                vector = vector.map { it.toFloat() }.toFloatArray(),
                modelName = modelName
            )
        }

        /**
         * Validate vector dimensions for the default model
         */
        fun validateDimension(vector: FloatArray, expectedDimension: Int = DEFAULT_VECTOR_DIMENSION): Boolean {
            return vector.size == expectedDimension
        }

        /**
         * Normalize a vector to unit length
         */
        fun normalize(vector: FloatArray): FloatArray {
            val magnitude = kotlin.math.sqrt(vector.map { it.toDouble() * it }.sum()).toFloat()
            return if (magnitude > 0) {
                vector.map { it / magnitude }.toFloatArray()
            } else {
                vector
            }
        }

        /**
         * Calculate batch cosine similarities
         */
        fun batchCosineSimilarity(
            queryVector: FloatArray,
            embeddings: List<ChunkEmbedding>
        ): List<Pair<UUID, Double>> {
            return embeddings.map { embedding ->
                embedding.chunkId to embedding.cosineSimilarity(queryVector)
            }.sortedByDescending { it.second }
        }
    }
}