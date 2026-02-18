package com.leadertoolbox.memory.service

import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import org.slf4j.LoggerFactory
import org.springframework.cache.annotation.Cacheable
import org.springframework.stereotype.Service
import org.springframework.web.reactive.function.client.WebClient
import org.springframework.web.reactive.function.client.awaitBody
import java.security.MessageDigest
import kotlin.math.sqrt

/**
 * Embedding Service
 *
 * Provides vector embeddings for text using the all-MiniLM-L6-v2 model.
 * Supports both local and remote embedding generation with caching.
 */
@Service
class EmbeddingService(
    private val webClient: WebClient.Builder
) {
    private val logger = LoggerFactory.getLogger(EmbeddingService::class.java)

    // HuggingFace Inference API endpoint for all-MiniLM-L6-v2
    private val huggingfaceClient = webClient
        .baseUrl("https://api-inference.huggingface.co")
        .defaultHeader("Authorization", "Bearer \${HUGGINGFACE_API_KEY}")
        .build()

    /**
     * Generate embedding for a single text
     */
    @Cacheable("embeddings", key = "#text.hashCode()")
    suspend fun generateEmbedding(text: String): FloatArray {
        return withContext(Dispatchers.IO) {
            try {
                generateEmbeddingViaHuggingFace(text)
            } catch (e: Exception) {
                logger.warn("HuggingFace API failed, falling back to local embedding", e)
                generateLocalEmbedding(text)
            }
        }
    }

    /**
     * Generate embeddings for multiple texts (batch processing)
     */
    suspend fun generateEmbeddings(texts: List<String>): List<FloatArray> {
        return withContext(Dispatchers.IO) {
            // For small batches, process individually to leverage caching
            if (texts.size <= 5) {
                texts.map { generateEmbedding(it) }
            } else {
                // For larger batches, try batch API first
                try {
                    generateEmbeddingsBatchViaHuggingFace(texts)
                } catch (e: Exception) {
                    logger.warn("Batch embedding failed, falling back to individual processing", e)
                    texts.map { generateEmbedding(it) }
                }
            }
        }
    }

    /**
     * Generate embedding via HuggingFace Inference API
     */
    private suspend fun generateEmbeddingViaHuggingFace(text: String): FloatArray {
        val request = HuggingFaceEmbeddingRequest(
            inputs = text,
            options = HuggingFaceOptions(waitForModel = true)
        )

        val response = huggingfaceClient
            .post()
            .uri("/pipeline/feature-extraction/sentence-transformers/all-MiniLM-L6-v2")
            .bodyValue(request)
            .retrieve()
            .awaitBody<Array<FloatArray>>()

        return response.first() // HuggingFace returns array of arrays
    }

    /**
     * Generate embeddings in batch via HuggingFace
     */
    private suspend fun generateEmbeddingsBatchViaHuggingFace(texts: List<String>): List<FloatArray> {
        val request = HuggingFaceBatchEmbeddingRequest(
            inputs = texts,
            options = HuggingFaceOptions(waitForModel = true)
        )

        val response = huggingfaceClient
            .post()
            .uri("/pipeline/feature-extraction/sentence-transformers/all-MiniLM-L6-v2")
            .bodyValue(request)
            .retrieve()
            .awaitBody<Array<Array<FloatArray>>>()

        return response.map { it.first() } // Extract first (and only) embedding from each
    }

    /**
     * Generate local embedding (fallback using simple TF-IDF + dimensionality reduction)
     */
    private fun generateLocalEmbedding(text: String): FloatArray {
        logger.debug("Generating local embedding for text: ${text.take(100)}...")

        // This is a simplified local embedding for fallback purposes
        // In production, you might want to use a proper local embedding model

        // Create a simple hash-based embedding
        val words = text.lowercase()
            .replace(Regex("[^a-z0-9\\s]"), "")
            .split("\\s+")
            .filter { it.isNotBlank() }

        // Create a 384-dimension vector (matching all-MiniLM-L6-v2)
        val embedding = FloatArray(384) { 0.0f }

        // Simple hash-based feature extraction
        words.forEachIndexed { index, word ->
            val hash = word.hashCode()
            val position1 = (hash.toUInt() % 384u).toInt()
            val position2 = ((hash shr 16).toUInt() % 384u).toInt()

            embedding[position1] += 1.0f / (index + 1) // Position weighting
            embedding[position2] += 0.5f / (index + 1)
        }

        // Add content length feature
        val lengthFeature = (text.length.toFloat() / 1000.0f).coerceAtMost(1.0f)
        embedding[0] = lengthFeature

        // Normalize to unit vector
        return normalizeVector(embedding)
    }

    /**
     * Calculate cosine similarity between two embeddings
     */
    fun cosineSimilarity(embedding1: FloatArray, embedding2: FloatArray): Float {
        if (embedding1.size != embedding2.size) {
            throw IllegalArgumentException("Embeddings must have the same dimension")
        }

        var dotProduct = 0.0f
        var norm1 = 0.0f
        var norm2 = 0.0f

        for (i in embedding1.indices) {
            dotProduct += embedding1[i] * embedding2[i]
            norm1 += embedding1[i] * embedding1[i]
            norm2 += embedding2[i] * embedding2[i]
        }

        return if (norm1 > 0 && norm2 > 0) {
            dotProduct / (sqrt(norm1) * sqrt(norm2))
        } else {
            0.0f
        }
    }

    /**
     * Calculate L2 (Euclidean) distance between embeddings
     */
    fun l2Distance(embedding1: FloatArray, embedding2: FloatArray): Float {
        if (embedding1.size != embedding2.size) {
            throw IllegalArgumentException("Embeddings must have the same dimension")
        }

        var sumSquares = 0.0f
        for (i in embedding1.indices) {
            val diff = embedding1[i] - embedding2[i]
            sumSquares += diff * diff
        }

        return sqrt(sumSquares)
    }

    /**
     * Normalize vector to unit length
     */
    fun normalizeVector(vector: FloatArray): FloatArray {
        val magnitude = sqrt(vector.map { it * it }.sum())
        return if (magnitude > 0) {
            vector.map { it / magnitude }.toFloatArray()
        } else {
            vector
        }
    }

    /**
     * Get cache key for text (useful for debugging)
     */
    fun getCacheKey(text: String): String {
        return MessageDigest.getInstance("SHA-256")
            .digest(text.toByteArray())
            .joinToString("") { "%02x".format(it) }
    }

    /**
     * Validate embedding dimension
     */
    fun validateEmbedding(embedding: FloatArray): Boolean {
        return embedding.size == EXPECTED_DIMENSION && embedding.all { it.isFinite() }
    }

    /**
     * Get embedding statistics
     */
    fun getEmbeddingStats(embedding: FloatArray): EmbeddingStats {
        val magnitude = sqrt(embedding.map { it * it }.sum())
        val mean = embedding.average().toFloat()
        val variance = embedding.map { (it - mean) * (it - mean) }.average().toFloat()
        val min = embedding.minOrNull() ?: 0.0f
        val max = embedding.maxOrNull() ?: 0.0f

        return EmbeddingStats(
            dimension = embedding.size,
            magnitude = magnitude,
            mean = mean,
            variance = variance,
            min = min,
            max = max,
            isNormalized = (magnitude - 1.0f).let { kotlin.math.abs(it) < 0.01f }
        )
    }

    companion object {
        const val EXPECTED_DIMENSION = 384
        const val MODEL_NAME = "all-MiniLM-L6-v2"
    }

    // DTOs for HuggingFace API
    private data class HuggingFaceEmbeddingRequest(
        val inputs: String,
        val options: HuggingFaceOptions = HuggingFaceOptions()
    )

    private data class HuggingFaceBatchEmbeddingRequest(
        val inputs: List<String>,
        val options: HuggingFaceOptions = HuggingFaceOptions()
    )

    private data class HuggingFaceOptions(
        val waitForModel: Boolean = true,
        val useCache: Boolean = true
    )

    data class EmbeddingStats(
        val dimension: Int,
        val magnitude: Float,
        val mean: Float,
        val variance: Float,
        val min: Float,
        val max: Float,
        val isNormalized: Boolean
    )
}