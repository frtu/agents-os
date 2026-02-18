"""
Keyword/text search implementation.
"""

import logging
import re
from typing import List, Tuple, Optional, Set
from collections import Counter

from ..models import SearchResult, SearchOptions, ChunkInfo
from ..storage.base import StorageBackend

logger = logging.getLogger(__name__)

class KeywordSearch:
    """Keyword-based text search."""

    def __init__(self, storage_backend: StorageBackend):
        """
        Initialize keyword search.

        Args:
            storage_backend: Storage backend
        """
        self.storage = storage_backend

    async def search(
        self,
        query: str,
        options: Optional[SearchOptions] = None
    ) -> List[SearchResult]:
        """
        Search for content using keyword matching.

        Args:
            query: Search query
            options: Search options

        Returns:
            List of search results
        """
        if not options:
            options = SearchOptions()

        try:
            # Use storage backend's keyword search if available
            chunk_results = await self.storage.search_keyword(
                query,
                limit=options.max_results * 2,  # Get more to account for filtering
                min_score=0.0  # We'll filter later
            )

            # Convert to search results and apply additional scoring
            search_results = []
            for chunk_info, base_score in chunk_results:
                # Get file info for the chunk
                file_info = await self.storage.get_file(chunk_info.file_id)
                if not file_info:
                    logger.warning(f"File not found for chunk {chunk_info.id}")
                    continue

                # Enhanced relevance scoring
                enhanced_score = self._calculate_relevance_score(
                    query, chunk_info.text, base_score
                )

                if enhanced_score >= options.min_score:
                    # Generate highlighted excerpt
                    excerpt = self._create_excerpt(query, chunk_info.text)

                    search_result = SearchResult(
                        file_id=chunk_info.file_id,
                        file_path=file_info.path,
                        text=chunk_info.text,
                        score=enhanced_score,
                        start_char=chunk_info.start_char,
                        end_char=chunk_info.end_char,
                        excerpt=excerpt,
                        metadata={
                            "chunk_id": chunk_info.id,
                            "file_metadata": file_info.metadata,
                            "chunk_metadata": chunk_info.metadata,
                            "search_type": "keyword",
                            "base_score": base_score
                        }
                    )

                    search_results.append(search_result)

            # Sort by score and limit results
            search_results.sort(key=lambda x: x.score, reverse=True)
            search_results = search_results[:options.max_results]

            logger.debug(f"Keyword search found {len(search_results)} results for query: {query[:50]}...")
            return search_results

        except Exception as e:
            logger.error(f"Keyword search failed: {e}")
            raise

    def _calculate_relevance_score(self, query: str, text: str, base_score: float) -> float:
        """
        Calculate enhanced relevance score.

        Args:
            query: Search query
            text: Document text
            base_score: Base score from storage backend

        Returns:
            Enhanced relevance score
        """
        query_lower = query.lower()
        text_lower = text.lower()

        # Extract query terms
        query_terms = self._extract_terms(query_lower)
        if not query_terms:
            return base_score

        # Calculate various scoring factors
        factors = {}

        # Exact phrase match
        factors['exact_phrase'] = 2.0 if query_lower in text_lower else 0.0

        # Term frequency
        text_terms = self._extract_terms(text_lower)
        term_frequencies = Counter(text_terms)
        total_terms = len(text_terms)

        tf_score = 0.0
        for term in query_terms:
            tf = term_frequencies.get(term, 0)
            if tf > 0:
                tf_score += tf / total_terms

        factors['term_frequency'] = tf_score

        # Term coverage (how many query terms appear)
        matching_terms = sum(1 for term in query_terms if term in text_lower)
        factors['term_coverage'] = matching_terms / len(query_terms)

        # Position bonus (terms appearing early in text get bonus)
        position_bonus = 0.0
        for term in query_terms:
            pos = text_lower.find(term)
            if pos != -1:
                # Bonus decreases with position (normalized by text length)
                position_bonus += max(0.0, 1.0 - (pos / len(text_lower)))

        factors['position_bonus'] = position_bonus / len(query_terms)

        # Length penalty (prefer shorter matches)
        factors['length_penalty'] = max(0.1, 1.0 - (len(text) / 5000))

        # Combine factors
        enhanced_score = (
            base_score * 0.4 +
            factors['exact_phrase'] * 0.15 +
            factors['term_frequency'] * 0.2 +
            factors['term_coverage'] * 0.15 +
            factors['position_bonus'] * 0.05 +
            factors['length_penalty'] * 0.05
        )

        return min(1.0, enhanced_score)

    def _extract_terms(self, text: str) -> List[str]:
        """
        Extract search terms from text.

        Args:
            text: Input text

        Returns:
            List of terms
        """
        # Simple tokenization - split on non-word characters
        terms = re.findall(r'\b\w+\b', text.lower())

        # Filter out very short terms
        terms = [term for term in terms if len(term) >= 2]

        return terms

    def _create_excerpt(self, query: str, text: str, max_length: int = 200) -> str:
        """
        Create an excerpt highlighting query terms.

        Args:
            query: Search query
            text: Full text
            max_length: Maximum excerpt length

        Returns:
            Text excerpt with context around query terms
        """
        query_lower = query.lower()
        text_lower = text.lower()

        # Find best position to start excerpt
        best_pos = 0
        best_score = 0

        # Look for query terms in text
        for term in self._extract_terms(query_lower):
            pos = text_lower.find(term)
            if pos != -1:
                # Score based on term importance and position
                score = len(term) / (pos + 1)
                if score > best_score:
                    best_score = score
                    best_pos = pos

        # Create excerpt around best position
        start = max(0, best_pos - max_length // 3)
        end = min(len(text), start + max_length)

        # Adjust to word boundaries
        if start > 0:
            # Find previous space
            while start > 0 and text[start] != ' ':
                start -= 1
            start += 1

        if end < len(text):
            # Find next space
            while end < len(text) and text[end] != ' ':
                end += 1

        excerpt = text[start:end].strip()

        # Add ellipsis if truncated
        if start > 0:
            excerpt = "..." + excerpt
        if end < len(text):
            excerpt = excerpt + "..."

        return excerpt