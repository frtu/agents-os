"""
Base storage backend interface.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any, Tuple
import numpy as np
from datetime import datetime

from ..models import FileInfo, ChunkInfo, SearchResult, EmbeddingCacheEntry

class StorageBackend(ABC):
    """Abstract base class for storage backends."""

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the storage backend."""
        pass

    @abstractmethod
    async def close(self) -> None:
        """Close the storage backend and clean up resources."""
        pass

    # File operations

    @abstractmethod
    async def add_file(self, file_info: FileInfo) -> str:
        """
        Add a file to storage.

        Args:
            file_info: File information

        Returns:
            File ID
        """
        pass

    @abstractmethod
    async def get_file(self, file_id: str) -> Optional[FileInfo]:
        """
        Get file information by ID.

        Args:
            file_id: File ID

        Returns:
            File information or None if not found
        """
        pass

    @abstractmethod
    async def get_file_by_path(self, path: str) -> Optional[FileInfo]:
        """
        Get file information by path.

        Args:
            path: File path

        Returns:
            File information or None if not found
        """
        pass

    @abstractmethod
    async def list_files(self, limit: Optional[int] = None, offset: int = 0) -> List[FileInfo]:
        """
        List all files.

        Args:
            limit: Maximum number of files to return
            offset: Number of files to skip

        Returns:
            List of file information
        """
        pass

    @abstractmethod
    async def update_file(self, file_info: FileInfo) -> bool:
        """
        Update file information.

        Args:
            file_info: Updated file information

        Returns:
            True if updated, False if not found
        """
        pass

    @abstractmethod
    async def delete_file(self, file_id: str) -> bool:
        """
        Delete a file and all its chunks.

        Args:
            file_id: File ID

        Returns:
            True if deleted, False if not found
        """
        pass

    # Chunk operations

    @abstractmethod
    async def add_chunk(self, chunk_info: ChunkInfo, embedding: Optional[np.ndarray] = None) -> str:
        """
        Add a chunk to storage.

        Args:
            chunk_info: Chunk information
            embedding: Optional embedding vector

        Returns:
            Chunk ID
        """
        pass

    @abstractmethod
    async def get_chunk(self, chunk_id: str) -> Optional[ChunkInfo]:
        """
        Get chunk information by ID.

        Args:
            chunk_id: Chunk ID

        Returns:
            Chunk information or None if not found
        """
        pass

    @abstractmethod
    async def get_chunks_by_file(self, file_id: str) -> List[ChunkInfo]:
        """
        Get all chunks for a file.

        Args:
            file_id: File ID

        Returns:
            List of chunk information
        """
        pass

    @abstractmethod
    async def update_chunk_embedding(self, chunk_id: str, embedding: np.ndarray) -> bool:
        """
        Update chunk embedding.

        Args:
            chunk_id: Chunk ID
            embedding: Embedding vector

        Returns:
            True if updated, False if not found
        """
        pass

    @abstractmethod
    async def delete_chunks_by_file(self, file_id: str) -> int:
        """
        Delete all chunks for a file.

        Args:
            file_id: File ID

        Returns:
            Number of chunks deleted
        """
        pass

    # Search operations

    @abstractmethod
    async def search_vector(
        self,
        query_embedding: np.ndarray,
        limit: int = 10,
        min_score: float = 0.0
    ) -> List[Tuple[ChunkInfo, float]]:
        """
        Search for similar chunks using vector similarity.

        Args:
            query_embedding: Query embedding vector
            limit: Maximum number of results
            min_score: Minimum similarity score

        Returns:
            List of (chunk_info, score) tuples
        """
        pass

    @abstractmethod
    async def search_keyword(
        self,
        query: str,
        limit: int = 10,
        min_score: float = 0.0
    ) -> List[Tuple[ChunkInfo, float]]:
        """
        Search for chunks using keyword/text search.

        Args:
            query: Search query
            limit: Maximum number of results
            min_score: Minimum relevance score

        Returns:
            List of (chunk_info, score) tuples
        """
        pass

    # Embedding cache operations

    @abstractmethod
    async def get_cached_embedding(
        self,
        text_hash: str,
        provider: str,
        model: str
    ) -> Optional[np.ndarray]:
        """
        Get cached embedding.

        Args:
            text_hash: Hash of the text
            provider: Embedding provider name
            model: Model name

        Returns:
            Cached embedding or None if not found
        """
        pass

    @abstractmethod
    async def cache_embedding(
        self,
        text_hash: str,
        provider: str,
        model: str,
        embedding: np.ndarray
    ) -> None:
        """
        Cache an embedding.

        Args:
            text_hash: Hash of the text
            provider: Embedding provider name
            model: Model name
            embedding: Embedding vector
        """
        pass

    # Statistics and status

    @abstractmethod
    async def get_stats(self) -> Dict[str, Any]:
        """
        Get storage statistics.

        Returns:
            Dictionary with statistics
        """
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """
        Check if storage backend is healthy.

        Returns:
            True if healthy, False otherwise
        """
        pass

    # Utility methods

    def compute_cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """
        Compute cosine similarity between two vectors.

        Args:
            vec1: First vector
            vec2: Second vector

        Returns:
            Cosine similarity score (0-1)
        """
        # Normalize vectors
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        # Compute cosine similarity
        similarity = np.dot(vec1, vec2) / (norm1 * norm2)

        # Ensure result is in [0, 1] range
        return max(0.0, min(1.0, (similarity + 1.0) / 2.0))