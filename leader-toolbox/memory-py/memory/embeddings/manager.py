"""
Embedding manager that handles provider selection and caching.
"""

import hashlib
import logging
from typing import List, Optional, Dict, Any, Union
import numpy as np

from .base import EmbeddingProvider
from .sentence_transformers_provider import SentenceTransformersProvider
from .openai_provider import OpenAIProvider
from .gemini_provider import GeminiProvider
from .voyage_provider import VoyageProvider

logger = logging.getLogger(__name__)

class EmbeddingManager:
    """
    Manages multiple embedding providers with fallback support and caching.
    """

    def __init__(
        self,
        primary_provider: str = "sentence_transformers",
        fallback_provider: str = "sentence_transformers",
        cache_enabled: bool = True,
        storage_backend = None,
        **provider_configs
    ):
        """
        Initialize embedding manager.

        Args:
            primary_provider: Primary provider name
            fallback_provider: Fallback provider name
            cache_enabled: Whether to enable embedding caching
            storage_backend: Storage backend for caching
            **provider_configs: Configuration for each provider
        """
        self.primary_provider_name = primary_provider
        self.fallback_provider_name = fallback_provider
        self.cache_enabled = cache_enabled
        self.storage_backend = storage_backend
        self.provider_configs = provider_configs

        self.providers: Dict[str, EmbeddingProvider] = {}
        self.provider_status: Dict[str, bool] = {}
        self.failure_counts: Dict[str, int] = {}
        self.max_failures = 2

    async def initialize(self) -> None:
        """Initialize embedding providers."""
        # Create providers based on configuration
        providers_to_create = {self.primary_provider_name, self.fallback_provider_name}

        for provider_name in providers_to_create:
            try:
                provider = await self._create_provider(provider_name)
                if provider:
                    self.providers[provider_name] = provider
                    self.provider_status[provider_name] = await provider.is_available()
                    self.failure_counts[provider_name] = 0
                    logger.info(f"Initialized provider: {provider_name} (available: {self.provider_status[provider_name]})")
            except Exception as e:
                logger.error(f"Failed to initialize provider {provider_name}: {e}")
                self.provider_status[provider_name] = False

        # Ensure we have at least one working provider
        if not any(self.provider_status.values()):
            logger.warning("No embedding providers available")

    async def _create_provider(self, provider_name: str) -> Optional[EmbeddingProvider]:
        """Create a provider instance."""
        config = self.provider_configs.get(provider_name, {})

        if provider_name == "sentence_transformers":
            return SentenceTransformersProvider(**config)
        elif provider_name == "openai":
            return OpenAIProvider(**config)
        elif provider_name == "gemini":
            return GeminiProvider(**config)
        elif provider_name == "voyage":
            return VoyageProvider(**config)
        else:
            logger.error(f"Unknown provider: {provider_name}")
            return None

    async def embed(self, texts: List[str]) -> List[np.ndarray]:
        """
        Generate embeddings for texts using the best available provider.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        if not texts:
            return []

        # Try cache first if enabled
        if self.cache_enabled and self.storage_backend:
            cached_results = await self._get_cached_embeddings(texts)
            if cached_results:
                cache_hits, cache_misses = cached_results
                if not cache_misses:
                    # All embeddings found in cache
                    return cache_hits

                # Some embeddings found, generate the rest
                new_embeddings = await self._generate_embeddings([texts[i] for i in cache_misses])
                if new_embeddings:
                    # Cache the new embeddings
                    await self._cache_embeddings([texts[i] for i in cache_misses], new_embeddings)

                    # Merge results in original order
                    result = [None] * len(texts)
                    cache_idx = 0
                    miss_idx = 0

                    for i, text in enumerate(texts):
                        if i in cache_misses:
                            result[i] = new_embeddings[miss_idx]
                            miss_idx += 1
                        else:
                            result[i] = cache_hits[cache_idx]
                            cache_idx += 1

                    return result

        # Generate all embeddings
        embeddings = await self._generate_embeddings(texts)

        # Cache results if enabled
        if embeddings and self.cache_enabled and self.storage_backend:
            await self._cache_embeddings(texts, embeddings)

        return embeddings

    async def _generate_embeddings(self, texts: List[str]) -> List[np.ndarray]:
        """Generate embeddings using available providers."""
        # Try primary provider first
        if self._is_provider_available(self.primary_provider_name):
            try:
                provider = self.providers[self.primary_provider_name]
                embeddings = await provider.embed(texts)
                logger.debug(f"Generated {len(embeddings)} embeddings using {self.primary_provider_name}")
                return embeddings
            except Exception as e:
                logger.warning(f"Primary provider {self.primary_provider_name} failed: {e}")
                await self._record_failure(self.primary_provider_name)

        # Try fallback provider
        if self.fallback_provider_name != self.primary_provider_name and self._is_provider_available(self.fallback_provider_name):
            try:
                provider = self.providers[self.fallback_provider_name]
                embeddings = await provider.embed(texts)
                logger.info(f"Used fallback provider {self.fallback_provider_name}")
                return embeddings
            except Exception as e:
                logger.warning(f"Fallback provider {self.fallback_provider_name} failed: {e}")
                await self._record_failure(self.fallback_provider_name)

        # Try any other available provider
        for provider_name, provider in self.providers.items():
            if provider_name not in {self.primary_provider_name, self.fallback_provider_name} and self._is_provider_available(provider_name):
                try:
                    embeddings = await provider.embed(texts)
                    logger.info(f"Used emergency provider {provider_name}")
                    return embeddings
                except Exception as e:
                    logger.warning(f"Emergency provider {provider_name} failed: {e}")
                    await self._record_failure(provider_name)

        raise RuntimeError("All embedding providers failed")

    def _is_provider_available(self, provider_name: str) -> bool:
        """Check if provider is available."""
        return (
            provider_name in self.providers and
            self.provider_status.get(provider_name, False) and
            self.failure_counts.get(provider_name, 0) < self.max_failures
        )

    async def _record_failure(self, provider_name: str) -> None:
        """Record a failure for a provider."""
        self.failure_counts[provider_name] = self.failure_counts.get(provider_name, 0) + 1
        if self.failure_counts[provider_name] >= self.max_failures:
            logger.warning(f"Provider {provider_name} disabled after {self.max_failures} failures")
            self.provider_status[provider_name] = False

    async def _get_cached_embeddings(self, texts: List[str]) -> Optional[tuple]:
        """
        Get cached embeddings for texts.

        Returns:
            Tuple of (cache_hits, cache_misses_indices) or None
        """
        if not self.storage_backend:
            return None

        primary_provider = self.providers.get(self.primary_provider_name)
        if not primary_provider:
            return None

        cache_hits = []
        cache_misses = []

        for i, text in enumerate(texts):
            text_hash = primary_provider.compute_text_hash(text)
            cached_embedding = await self.storage_backend.get_cached_embedding(
                text_hash,
                primary_provider.name,
                primary_provider.model
            )

            if cached_embedding is not None:
                cache_hits.append(cached_embedding)
            else:
                cache_hits.append(None)
                cache_misses.append(i)

        if not cache_misses:
            # All found in cache
            return cache_hits, []

        # Return hits (with None for misses) and miss indices
        return cache_hits, cache_misses

    async def _cache_embeddings(self, texts: List[str], embeddings: List[np.ndarray]) -> None:
        """Cache embeddings for texts."""
        if not self.storage_backend or len(texts) != len(embeddings):
            return

        primary_provider = self.providers.get(self.primary_provider_name)
        if not primary_provider:
            return

        try:
            for text, embedding in zip(texts, embeddings):
                text_hash = primary_provider.compute_text_hash(text)
                await self.storage_backend.cache_embedding(
                    text_hash,
                    primary_provider.name,
                    primary_provider.model,
                    embedding
                )
        except Exception as e:
            logger.warning(f"Failed to cache embeddings: {e}")

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

    async def get_provider_status(self) -> Dict[str, Any]:
        """
        Get status of all providers.

        Returns:
            Dictionary with provider status information
        """
        status = {}

        for provider_name, provider in self.providers.items():
            health = await provider.health_check()
            status[provider_name] = {
                "name": provider.name,
                "model": provider.model,
                "dimensions": provider.dimensions,
                "max_tokens": provider.max_tokens,
                "supports_batching": provider.supports_batching,
                "available": self.provider_status.get(provider_name, False),
                "failures": self.failure_counts.get(provider_name, 0),
                "health": health
            }

        status["primary"] = self.primary_provider_name
        status["fallback"] = self.fallback_provider_name

        return status

    async def reset_failures(self, provider_name: Optional[str] = None) -> None:
        """
        Reset failure counts for providers.

        Args:
            provider_name: Specific provider to reset, or None for all
        """
        if provider_name:
            self.failure_counts[provider_name] = 0
            if provider_name in self.providers:
                self.provider_status[provider_name] = await self.providers[provider_name].is_available()
        else:
            for provider_name, provider in self.providers.items():
                self.failure_counts[provider_name] = 0
                self.provider_status[provider_name] = await provider.is_available()

        logger.info(f"Reset failure counts for {'all providers' if not provider_name else provider_name}")

    @property
    def dimensions(self) -> int:
        """Get dimensions of the primary provider."""
        primary_provider = self.providers.get(self.primary_provider_name)
        if primary_provider:
            return primary_provider.dimensions
        return 384  # Default fallback