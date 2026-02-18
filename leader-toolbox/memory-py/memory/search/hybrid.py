"""
Hybrid search implementation that combines vector and keyword search.
"""

import asyncio
import logging
from typing import List, Dict, Optional, Set
from collections import defaultdict

from ..models import SearchResult, SearchOptions
from ..storage.base import StorageBackend
from ..embeddings.manager import EmbeddingManager
from .vector_search import VectorSearch
from .keyword_search import KeywordSearch

logger = logging.getLogger(__name__)

class HybridSearch:
    """
    Hybrid search that combines vector similarity and keyword matching.
    """

    def __init__(
        self,
        storage_backend: StorageBackend,
        embedding_manager: EmbeddingManager
    ):
        """
        Initialize hybrid search.

        Args:
            storage_backend: Storage backend
            embedding_manager: Embedding manager
        """
        self.storage = storage_backend
        self.embeddings = embedding_manager
        self.vector_search = VectorSearch(storage_backend, embedding_manager)
        self.keyword_search = KeywordSearch(storage_backend)

    async def search(
        self,
        query: str,
        options: Optional[SearchOptions] = None
    ) -> List[SearchResult]:
        """
        Perform hybrid search combining vector and keyword results.

        Args:
            query: Search query
            options: Search options

        Returns:
            Merged and ranked search results
        """
        if not options:
            options = SearchOptions()

        # Determine search mode
        if options.mode == "vector":
            return await self.vector_search.search(query, options)
        elif options.mode == "keyword":
            return await self.keyword_search.search(query, options)
        elif options.mode == "hybrid":
            return await self._hybrid_search(query, options)
        else:
            raise ValueError(f"Unknown search mode: {options.mode}")

    async def _hybrid_search(
        self,
        query: str,
        options: SearchOptions
    ) -> List[SearchResult]:
        """
        Perform hybrid search.

        Args:
            query: Search query
            options: Search options

        Returns:
            Merged search results
        """
        try:
            # Get more results from each search to improve merging
            candidate_multiplier = 3
            expanded_options = SearchOptions(
                mode=options.mode,
                max_results=options.max_results * candidate_multiplier,
                min_score=max(0.1, options.min_score - 0.2),  # Lower threshold for candidates
                sources=options.sources,
                vector_weight=options.vector_weight,
                keyword_weight=options.keyword_weight
            )

            # Run vector and keyword searches in parallel
            vector_results, keyword_results = await asyncio.gather(
                self.vector_search.search(query, expanded_options),
                self.keyword_search.search(query, expanded_options)
            )

            logger.debug(f"Vector search: {len(vector_results)} results, "
                        f"Keyword search: {len(keyword_results)} results")

            # Merge results
            merged_results = self._merge_results(
                vector_results,
                keyword_results,
                options.vector_weight or 0.7,
                options.keyword_weight or 0.3
            )

            # Filter by minimum score and limit results
            filtered_results = [
                result for result in merged_results
                if result.score >= options.min_score
            ]

            final_results = filtered_results[:options.max_results]

            logger.debug(f"Hybrid search produced {len(final_results)} final results")
            return final_results

        except Exception as e:
            logger.error(f"Hybrid search failed: {e}")
            # Fallback to vector search only
            try:
                return await self.vector_search.search(query, options)
            except:
                # Last resort: keyword search
                return await self.keyword_search.search(query, options)

    def _merge_results(
        self,
        vector_results: List[SearchResult],
        keyword_results: List[SearchResult],
        vector_weight: float,
        keyword_weight: float
    ) -> List[SearchResult]:
        """
        Merge vector and keyword search results.

        Args:
            vector_results: Results from vector search
            keyword_results: Results from keyword search
            vector_weight: Weight for vector scores
            keyword_weight: Weight for keyword scores

        Returns:
            Merged and ranked results
        """
        # Create result map using file_id + start_char as key
        result_map: Dict[str, SearchResult] = {}
        vector_scores: Dict[str, float] = {}
        keyword_scores: Dict[str, float] = {}

        # Process vector results
        for result in vector_results:
            key = f"{result.file_id}:{result.start_char}"
            result_map[key] = result
            vector_scores[key] = result.score

        # Process keyword results
        for result in keyword_results:
            key = f"{result.file_id}:{result.start_char}"

            if key in result_map:
                # Merge with existing result
                existing = result_map[key]

                # Use the better excerpt if keyword search provides highlights
                if hasattr(result, 'excerpt') and result.excerpt and '...' in result.excerpt:
                    existing.excerpt = result.excerpt

                # Merge metadata
                if 'keyword_score' not in existing.metadata:
                    existing.metadata.update({
                        'keyword_score': result.score,
                        'vector_score': vector_scores.get(key, 0.0)
                    })

            else:
                # Add new result
                result_map[key] = result
                vector_scores[key] = 0.0

            keyword_scores[key] = result.score

        # Calculate combined scores
        final_results = []
        for key, result in result_map.items():
            vector_score = vector_scores.get(key, 0.0)
            keyword_score = keyword_scores.get(key, 0.0)

            # Combined score using weighted average
            combined_score = (
                vector_score * vector_weight +
                keyword_score * keyword_weight
            )

            # Apply bonus for results that appear in both searches
            if vector_score > 0 and keyword_score > 0:
                combined_score *= 1.1  # 10% bonus for appearing in both

            # Update result with combined score
            result.score = min(1.0, combined_score)
            result.metadata.update({
                'search_type': 'hybrid',
                'vector_score': vector_score,
                'keyword_score': keyword_score,
                'combined_score': combined_score,
                'vector_weight': vector_weight,
                'keyword_weight': keyword_weight,
                'appears_in_both': vector_score > 0 and keyword_score > 0
            })

            final_results.append(result)

        # Sort by combined score
        final_results.sort(key=lambda x: x.score, reverse=True)

        return final_results

    async def search_similar_documents(
        self,
        file_id: str,
        options: Optional[SearchOptions] = None
    ) -> List[SearchResult]:
        """
        Find documents similar to the given file.

        Args:
            file_id: ID of the file to find similar documents for
            options: Search options

        Returns:
            List of similar documents
        """
        # Get chunks for the file
        chunks = await self.storage.get_chunks_by_file(file_id)
        if not chunks:
            return []

        # Use the first chunk as query (could be improved to use all chunks)
        query_chunk = chunks[0]
        return await self.search(query_chunk.text, options)

    async def search_with_filters(
        self,
        query: str,
        file_types: Optional[List[str]] = None,
        date_range: Optional[tuple] = None,
        min_score: Optional[float] = None,
        max_results: Optional[int] = None
    ) -> List[SearchResult]:
        """
        Search with additional filters.

        Args:
            query: Search query
            file_types: List of file types to include
            date_range: Tuple of (start_date, end_date)
            min_score: Minimum score threshold
            max_results: Maximum number of results

        Returns:
            Filtered search results
        """
        options = SearchOptions(
            mode="hybrid",
            max_results=max_results or 10,
            min_score=min_score or 0.3
        )

        results = await self.search(query, options)

        # Apply additional filters
        filtered_results = []
        for result in results:
            # Filter by file type
            if file_types:
                file_ext = result.file_path.split('.')[-1].lower()
                if file_ext not in [ft.lower().lstrip('.') for ft in file_types]:
                    continue

            # Filter by date range (if metadata contains date information)
            if date_range:
                # This would require date metadata in files
                # Implementation depends on how dates are stored
                pass

            filtered_results.append(result)

        return filtered_results