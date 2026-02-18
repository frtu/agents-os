"""
Voyage AI embedding provider.
"""

from typing import List, Optional
import numpy as np
import logging
import asyncio

from .base import EmbeddingProvider

logger = logging.getLogger(__name__)

class VoyageProvider(EmbeddingProvider):
    """Voyage AI embedding provider."""

    def __init__(
        self,
        model: str = "voyage-4-large",
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize Voyage provider.

        Args:
            model: Voyage embedding model name
            api_key: Voyage API key
            base_url: Custom API base URL
            **kwargs: Additional configuration
        """
        super().__init__(model, **kwargs)
        self.api_key = api_key
        self.base_url = base_url or "https://api.voyageai.com/v1"
        self._client = None
        self._dimensions = None

    @property
    def name(self) -> str:
        """Provider name."""
        return "voyage"

    @property
    def dimensions(self) -> int:
        """Embedding dimensions."""
        if self._dimensions is None:
            # Default dimensions for Voyage models
            model_dims = {
                "voyage-4-large": 1024,
                "voyage-4-multilingual": 1024,
                "voyage-3": 1024,
                "voyage-3-large": 1024,
                "voyage-2": 1024
            }
            self._dimensions = model_dims.get(self.model, 1024)
        return self._dimensions

    @property
    def max_tokens(self) -> int:
        """Maximum tokens per input."""
        # Voyage models typically handle 32000 tokens
        return 32000

    @property
    def supports_batching(self) -> bool:
        """Whether provider supports batching."""
        return True

    def _get_client(self):
        """Get Voyage client."""
        if self._client is not None:
            return self._client

        try:
            import voyageai

            # Get API key from environment if not provided
            api_key = self.api_key
            if not api_key:
                import os
                api_key = os.getenv("VOYAGE_API_KEY")

            if not api_key:
                raise ValueError("Voyage API key not found")

            self._client = voyageai.Client(api_key=api_key, base_url=self.base_url)
            logger.info("Voyage client initialized")
            return self._client

        except ImportError:
            raise ImportError("voyageai package not installed. Install with: pip install voyageai")
        except Exception as e:
            logger.error(f"Failed to initialize Voyage client: {e}")
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

        client = self._get_client()

        try:
            # Run in thread pool since Voyage client is synchronous
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: client.embed(
                    texts=texts,
                    model=self.model,
                    input_type="document"
                )
            )

            embeddings = []
            for embedding_data in response.embeddings:
                embedding = np.array(embedding_data, dtype=np.float32)
                embeddings.append(self.normalize_embedding(embedding))

            # Update dimensions if we got different size
            if embeddings and self._dimensions != len(embeddings[0]):
                self._dimensions = len(embeddings[0])
                logger.info(f"Updated dimensions to {self._dimensions}")

            return embeddings

        except Exception as e:
            logger.error(f"Failed to generate Voyage embeddings: {e}")
            raise

    async def is_available(self) -> bool:
        """
        Check if provider is available and working.

        Returns:
            True if provider is available
        """
        try:
            # Try to create client and make a simple request
            client = self._get_client()

            # Test with a simple embedding
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: client.embed(
                    texts=["test"],
                    model=self.model,
                    input_type="document"
                )
            )
            return True

        except Exception as e:
            logger.warning(f"Voyage provider not available: {e}")
            return False

    def estimate_tokens(self, text: str) -> int:
        """
        Estimate token count for text.

        Voyage has generous token limits.
        """
        # Conservative estimation
        return min(len(text) // 4, self.max_tokens)