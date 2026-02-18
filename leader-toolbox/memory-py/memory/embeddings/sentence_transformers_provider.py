"""
SentenceTransformers embedding provider.

Integrates with the existing sentence-transformers model in the leader-toolbox.
"""

from typing import List, Optional
import numpy as np
import logging

from .base import EmbeddingProvider

logger = logging.getLogger(__name__)

class SentenceTransformersProvider(EmbeddingProvider):
    """SentenceTransformers embedding provider."""

    def __init__(self, model: str = "all-MiniLM-L6-v2", **kwargs):
        """
        Initialize SentenceTransformers provider.

        Args:
            model: SentenceTransformers model name
            **kwargs: Additional configuration
        """
        super().__init__(model, **kwargs)
        self._model = None
        self._dimensions = None

    @property
    def name(self) -> str:
        """Provider name."""
        return "sentence_transformers"

    @property
    def dimensions(self) -> int:
        """Embedding dimensions."""
        if self._dimensions is None:
            self._load_model()
        return self._dimensions

    @property
    def max_tokens(self) -> int:
        """Maximum tokens per input."""
        # Most sentence transformer models handle around 512 tokens
        return 512

    @property
    def supports_batching(self) -> bool:
        """Whether provider supports batching."""
        return True

    def _load_model(self):
        """Load the SentenceTransformers model."""
        if self._model is not None:
            return

        try:
            # Try to use existing model from the main app
            try:
                from backend.fastapi_chat import model as existing_model
                if existing_model is not None and hasattr(existing_model, 'encode'):
                    self._model = existing_model
                    logger.info("Using existing SentenceTransformers model from main app")
                else:
                    raise ImportError("No existing model found")
            except ImportError:
                # Create new model instance
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer(self.model)
                logger.info(f"Created new SentenceTransformers model: {self.model}")

            # Get model dimensions
            test_embedding = self._model.encode(["test"], convert_to_numpy=True, show_progress_bar=False)
            self._dimensions = test_embedding.shape[1]
            logger.info(f"Model dimensions: {self._dimensions}")

        except Exception as e:
            logger.error(f"Failed to load SentenceTransformers model: {e}")
            raise

    async def embed(self, texts: List[str]) -> List[np.ndarray]:
        """
        Generate embeddings for texts.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        if not texts:
            return []

        self._load_model()

        try:
            # Use the model to generate embeddings
            embeddings = self._model.encode(
                texts,
                convert_to_numpy=True,
                show_progress_bar=False,
                batch_size=self.config.get('batch_size', 32)
            )

            # Convert to list of numpy arrays
            if len(texts) == 1:
                embeddings = embeddings.reshape(1, -1)

            return [self.normalize_embedding(emb) for emb in embeddings]

        except Exception as e:
            logger.error(f"Failed to generate embeddings: {e}")
            raise

    async def is_available(self) -> bool:
        """
        Check if provider is available and working.

        Returns:
            True if provider is available
        """
        try:
            self._load_model()
            return self._model is not None
        except Exception:
            return False

    def estimate_tokens(self, text: str) -> int:
        """
        Estimate token count for text.

        For sentence transformers, we use a simple heuristic.
        """
        # Rough estimation: 4 chars per token for most languages
        return min(len(text) // 4, self.max_tokens)