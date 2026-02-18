"""
Google Gemini embedding provider.
"""

from typing import List, Optional
import numpy as np
import logging
import asyncio

from .base import EmbeddingProvider

logger = logging.getLogger(__name__)

class GeminiProvider(EmbeddingProvider):
    """Google Gemini embedding provider."""

    def __init__(
        self,
        model: str = "gemini-embedding-001",
        api_key: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize Gemini provider.

        Args:
            model: Gemini embedding model name
            api_key: Google API key
            **kwargs: Additional configuration
        """
        super().__init__(model, **kwargs)
        self.api_key = api_key
        self._client = None
        self._dimensions = None

    @property
    def name(self) -> str:
        """Provider name."""
        return "gemini"

    @property
    def dimensions(self) -> int:
        """Embedding dimensions."""
        if self._dimensions is None:
            # Default dimensions for Gemini models
            model_dims = {
                "gemini-embedding-001": 768,
                "embedding-001": 768
            }
            self._dimensions = model_dims.get(self.model, 768)
        return self._dimensions

    @property
    def max_tokens(self) -> int:
        """Maximum tokens per input."""
        # Gemini embedding models typically handle 2048 tokens
        return 2048

    @property
    def supports_batching(self) -> bool:
        """Whether provider supports batching."""
        return True

    def _get_client(self):
        """Get Gemini client."""
        if self._client is not None:
            return self._client

        try:
            import google.generativeai as genai

            # Get API key from environment if not provided
            api_key = self.api_key
            if not api_key:
                import os
                api_key = os.getenv("GOOGLE_API_KEY")

            if not api_key:
                raise ValueError("Google API key not found")

            genai.configure(api_key=api_key)
            self._client = genai
            logger.info("Gemini client initialized")
            return self._client

        except ImportError:
            raise ImportError("google-generativeai package not installed. Install with: pip install google-generativeai")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini client: {e}")
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
            embeddings = []

            # Process texts individually (Gemini API doesn't support batching the same way)
            for text in texts:
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(
                    None,
                    lambda t=text: client.embed_content(
                        model=self.model,
                        content=t,
                        task_type="retrieval_document"
                    )
                )

                embedding = np.array(response['embedding'], dtype=np.float32)
                embeddings.append(self.normalize_embedding(embedding))

            # Update dimensions if we got different size
            if embeddings and self._dimensions != len(embeddings[0]):
                self._dimensions = len(embeddings[0])
                logger.info(f"Updated dimensions to {self._dimensions}")

            return embeddings

        except Exception as e:
            logger.error(f"Failed to generate Gemini embeddings: {e}")
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
                lambda: client.embed_content(
                    model=self.model,
                    content="test",
                    task_type="retrieval_document"
                )
            )
            return True

        except Exception as e:
            logger.warning(f"Gemini provider not available: {e}")
            return False

    def estimate_tokens(self, text: str) -> int:
        """
        Estimate token count for text.

        Uses simple estimation for Gemini.
        """
        # Gemini uses similar tokenization to other models
        return min(len(text) // 4, self.max_tokens)