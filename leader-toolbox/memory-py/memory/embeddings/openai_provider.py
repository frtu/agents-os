"""
OpenAI embedding provider.
"""

from typing import List, Optional
import numpy as np
import logging
import asyncio

from .base import EmbeddingProvider

logger = logging.getLogger(__name__)

class OpenAIProvider(EmbeddingProvider):
    """OpenAI embedding provider."""

    def __init__(
        self,
        model: str = "text-embedding-3-small",
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize OpenAI provider.

        Args:
            model: OpenAI embedding model name
            api_key: OpenAI API key
            base_url: Custom API base URL
            **kwargs: Additional configuration
        """
        super().__init__(model, **kwargs)
        self.api_key = api_key
        self.base_url = base_url
        self._client = None
        self._dimensions = None

    @property
    def name(self) -> str:
        """Provider name."""
        return "openai"

    @property
    def dimensions(self) -> int:
        """Embedding dimensions."""
        if self._dimensions is None:
            # Default dimensions for common models
            model_dims = {
                "text-embedding-3-small": 1536,
                "text-embedding-3-large": 3072,
                "text-embedding-ada-002": 1536
            }
            self._dimensions = model_dims.get(self.model, 1536)
        return self._dimensions

    @property
    def max_tokens(self) -> int:
        """Maximum tokens per input."""
        # OpenAI embedding models typically handle 8191 tokens
        return 8191

    @property
    def supports_batching(self) -> bool:
        """Whether provider supports batching."""
        return True

    def _get_client(self):
        """Get OpenAI client."""
        if self._client is not None:
            return self._client

        try:
            import openai

            # Get API key from environment if not provided
            api_key = self.api_key
            if not api_key:
                import os
                api_key = os.getenv("OPENAI_API_KEY")

            if not api_key:
                raise ValueError("OpenAI API key not found")

            client_kwargs = {"api_key": api_key}
            if self.base_url:
                client_kwargs["base_url"] = self.base_url

            self._client = openai.OpenAI(**client_kwargs)
            logger.info("OpenAI client initialized")
            return self._client

        except ImportError:
            raise ImportError("openai package not installed. Install with: pip install openai")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")
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
            # Run in thread pool since OpenAI client is synchronous
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: client.embeddings.create(
                    model=self.model,
                    input=texts,
                    encoding_format="float"
                )
            )

            embeddings = []
            for data in response.data:
                embedding = np.array(data.embedding, dtype=np.float32)
                embeddings.append(self.normalize_embedding(embedding))

            # Update dimensions if we got different size
            if embeddings and self._dimensions != len(embeddings[0]):
                self._dimensions = len(embeddings[0])
                logger.info(f"Updated dimensions to {self._dimensions}")

            return embeddings

        except Exception as e:
            logger.error(f"Failed to generate OpenAI embeddings: {e}")
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
                lambda: client.embeddings.create(
                    model=self.model,
                    input=["test"],
                    encoding_format="float"
                )
            )
            return True

        except Exception as e:
            logger.warning(f"OpenAI provider not available: {e}")
            return False

    def estimate_tokens(self, text: str) -> int:
        """
        Estimate token count for text.

        Uses OpenAI's approximate tokenization.
        """
        try:
            import tiktoken

            # Get encoding for the model
            encoding = tiktoken.encoding_for_model(self.model)
            return len(encoding.encode(text))

        except ImportError:
            # Fallback to simple estimation
            return min(len(text) // 4, self.max_tokens)
        except Exception:
            # Fallback for unknown models
            return min(len(text) // 4, self.max_tokens)