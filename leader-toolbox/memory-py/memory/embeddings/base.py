"""
Base embedding provider interface.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
import numpy as np
import hashlib
import logging

logger = logging.getLogger(__name__)

class EmbeddingProvider(ABC):
    """Abstract base class for embedding providers."""

    def __init__(self, model: str, **kwargs):
        """
        Initialize embedding provider.

        Args:
            model: Model name/identifier
            **kwargs: Provider-specific configuration
        """
        self.model = model
        self.config = kwargs

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name."""
        pass

    @property
    @abstractmethod
    def dimensions(self) -> int:
        """Embedding dimensions."""
        pass

    @property
    @abstractmethod
    def max_tokens(self) -> int:
        """Maximum tokens per input."""
        pass

    @property
    @abstractmethod
    def supports_batching(self) -> bool:
        """Whether provider supports batching."""
        pass

    @abstractmethod
    async def embed(self, texts: List[str]) -> List[np.ndarray]:
        """
        Generate embeddings for texts.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        pass

    @abstractmethod
    async def is_available(self) -> bool:
        """
        Check if provider is available and working.

        Returns:
            True if provider is available
        """
        pass

    async def embed_single(self, text: str) -> np.ndarray:
        """
        Generate embedding for a single text.

        Args:
            text: Text to embed

        Returns:
            Embedding vector
        """
        embeddings = await self.embed([text])
        return embeddings[0]

    def estimate_tokens(self, text: str) -> int:
        """
        Estimate token count for text.

        Args:
            text: Input text

        Returns:
            Estimated token count
        """
        # Simple estimation: roughly 4 characters per token
        return len(text) // 4

    def compute_text_hash(self, text: str) -> str:
        """
        Compute hash for text (for caching).

        Args:
            text: Input text

        Returns:
            Text hash
        """
        return hashlib.sha256(text.encode()).hexdigest()

    def normalize_embedding(self, embedding: np.ndarray) -> np.ndarray:
        """
        Normalize embedding vector.

        Args:
            embedding: Input embedding

        Returns:
            Normalized embedding
        """
        norm = np.linalg.norm(embedding)
        if norm == 0:
            return embedding
        return embedding / norm

    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on provider.

        Returns:
            Health status information
        """
        try:
            available = await self.is_available()

            if available:
                # Test with a small embedding
                test_embedding = await self.embed_single("test")
                actual_dimensions = len(test_embedding)

                return {
                    "status": "healthy",
                    "available": True,
                    "dimensions": actual_dimensions,
                    "dimensions_match": actual_dimensions == self.dimensions,
                    "model": self.model
                }
            else:
                return {
                    "status": "unavailable",
                    "available": False,
                    "error": "Provider not available",
                    "model": self.model
                }

        except Exception as e:
            logger.error(f"Health check failed for {self.name}: {e}")
            return {
                "status": "error",
                "available": False,
                "error": str(e),
                "model": self.model
            }

    def __str__(self) -> str:
        return f"{self.name}({self.model})"

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(model='{self.model}', dimensions={self.dimensions})"