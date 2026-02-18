"""
Vector similarity search implementation.
"""

import logging
from typing import List, Tuple, Optional
import numpy as np

from ..models import SearchResult, SearchOptions, ChunkInfo
from ..storage.base import StorageBackend
from ..embeddings.manager import EmbeddingManager

logger = logging.getLogger(__name__)

class VectorSearch:
    """Vector similarity search using embeddings."""

    def __init__(
        self,
        storage_backend: StorageBackend,
        embedding_manager: EmbeddingManager
    ):
        """
        Initialize vector search.

        Args:
            storage_backend: Storage backend
            embedding_manager: Embedding manager
        """
        self.storage = storage_backend
        self.embeddings = embedding_manager

    async def search(
        self,
        query: str,
        options: Optional[SearchOptions] = None
    ) -> List[SearchResult]:
        """
        Search for similar content using vector similarity.

        Args:
            query: Search query
            options: Search options

        Returns:
            List of search results
        """
        if not options:
            options = SearchOptions()

        try:
            # Generate query embedding
            query_embedding = await self.embeddings.embed_single(query)

            # Search storage backend
            chunk_results = await self.storage.search_vector(
                query_embedding,
                limit=options.max_results,
                min_score=options.min_score
            )

            # Convert to search results
            search_results = []
            for chunk_info, score in chunk_results:
                # Get file info for the chunk
                file_info = await self.storage.get_file(chunk_info.file_id)
                if not file_info:
                    logger.warning(f"File not found for chunk {chunk_info.id}")
                    continue

                # Create search result
                search_result = SearchResult(
                    file_id=chunk_info.file_id,
                    file_path=file_info.path,
                    text=chunk_info.text,
                    score=score,
                    start_char=chunk_info.start_char,
                    end_char=chunk_info.end_char,
                    metadata={
                        "chunk_id": chunk_info.id,
                        "file_metadata": file_info.metadata,
                        "chunk_metadata": chunk_info.metadata,
                        "search_type": "vector"
                    }
                )

                search_results.append(search_result)

            logger.debug(f"Vector search found {len(search_results)} results for query: {query[:50]}...")
            return search_results

        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            raise

    async def search_similar_to_text(
        self,
        text: str,
        options: Optional[SearchOptions] = None
    ) -> List[SearchResult]:
        """
        Find content similar to the given text.

        Args:
            text: Text to find similar content for
            options: Search options

        Returns:
            List of search results
        """
        return await self.search(text, options)