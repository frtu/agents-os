"""
In-memory storage backend that wraps the existing leader-toolbox memory system.

Provides compatibility with the existing embeddings_store and metadatas approach.
"""

import uuid
import hashlib
import logging
from typing import List, Dict, Optional, Any, Tuple
import numpy as np
from datetime import datetime

from .base import StorageBackend
from ..models import FileInfo, ChunkInfo

# Import the existing global state from the main app
try:
    from backend.fastapi_chat import embeddings_store, metadatas, index, model
except ImportError:
    # Fallback for testing or standalone usage
    embeddings_store = []
    metadatas = []
    index = None
    model = None

logger = logging.getLogger(__name__)

class MemoryBackend(StorageBackend):
    """
    In-memory storage backend that integrates with existing leader-toolbox system.

    This backend provides a bridge between the new memory system interface
    and the existing in-memory data structures.
    """

    def __init__(self):
        """Initialize memory backend."""
        # Local state for additional metadata not in the original system
        self.files: Dict[str, FileInfo] = {}
        self.chunks: Dict[str, ChunkInfo] = {}
        self.chunk_embeddings: Dict[str, np.ndarray] = {}
        self.embedding_cache: Dict[str, np.ndarray] = {}

        # Index mapping from chunk ID to position in global arrays
        self.chunk_to_global_index: Dict[str, int] = {}
        self.initialized = False

    async def initialize(self) -> None:
        """Initialize the memory backend."""
        # Sync with existing global state if available
        await self._sync_from_global_state()
        self.initialized = True
        logger.info("Memory backend initialized")

    async def close(self) -> None:
        """Close the backend (no-op for memory backend)."""
        pass

    async def _sync_from_global_state(self) -> None:
        """Sync data from global embeddings_store and metadatas."""
        global embeddings_store, metadatas

        for i, (embedding, metadata) in enumerate(zip(embeddings_store, metadatas)):
            # Create file info if not exists
            source_id = metadata.get('source_id', str(uuid.uuid4()))
            file_path = metadata.get('title', f'document_{source_id}')

            if source_id not in self.files:
                file_info = FileInfo(
                    id=source_id,
                    path=file_path,
                    hash=hashlib.md5(metadata.get('full', '').encode()).hexdigest(),
                    size=len(metadata.get('full', '')),
                    mtime=datetime.now().timestamp(),
                    metadata={'title': metadata.get('title', ''), 'type': 'legacy'},
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
                self.files[source_id] = file_info

            # Create chunk info
            chunk_id = f"chunk_{i}"
            chunk_info = ChunkInfo(
                id=chunk_id,
                file_id=source_id,
                text=metadata.get('full', ''),
                start_char=0,
                end_char=len(metadata.get('full', '')),
                metadata={
                    'title': metadata.get('title', ''),
                    'excerpt': metadata.get('excerpt', ''),
                    'legacy_index': i
                },
                created_at=datetime.now()
            )

            self.chunks[chunk_id] = chunk_info
            self.chunk_embeddings[chunk_id] = np.array(embedding)
            self.chunk_to_global_index[chunk_id] = i

    # File operations

    async def add_file(self, file_info: FileInfo) -> str:
        """Add a file to storage."""
        self.files[file_info.id] = file_info
        return file_info.id

    async def get_file(self, file_id: str) -> Optional[FileInfo]:
        """Get file information by ID."""
        return self.files.get(file_id)

    async def get_file_by_path(self, path: str) -> Optional[FileInfo]:
        """Get file information by path."""
        for file_info in self.files.values():
            if file_info.path == path:
                return file_info
        return None

    async def list_files(self, limit: Optional[int] = None, offset: int = 0) -> List[FileInfo]:
        """List all files."""
        files = list(self.files.values())
        files.sort(key=lambda f: f.updated_at, reverse=True)

        if limit:
            return files[offset:offset + limit]
        return files[offset:]

    async def update_file(self, file_info: FileInfo) -> bool:
        """Update file information."""
        if file_info.id in self.files:
            file_info.updated_at = datetime.now()
            self.files[file_info.id] = file_info
            return True
        return False

    async def delete_file(self, file_id: str) -> bool:
        """Delete a file and all its chunks."""
        if file_id not in self.files:
            return False

        # Delete associated chunks
        chunks_to_delete = [cid for cid, chunk in self.chunks.items() if chunk.file_id == file_id]
        for chunk_id in chunks_to_delete:
            await self._delete_chunk_from_global(chunk_id)

        del self.files[file_id]
        return True

    # Chunk operations

    async def add_chunk(self, chunk_info: ChunkInfo, embedding: Optional[np.ndarray] = None) -> str:
        """Add a chunk to storage."""
        global embeddings_store, metadatas

        self.chunks[chunk_info.id] = chunk_info

        if embedding is not None:
            self.chunk_embeddings[chunk_info.id] = embedding

            # Add to global state for compatibility
            embeddings_store.append(embedding.tolist())
            metadata = {
                'source_id': chunk_info.file_id,
                'title': chunk_info.metadata.get('title', ''),
                'excerpt': chunk_info.text[:400],
                'full': chunk_info.text
            }
            metadatas.append(metadata)

            # Update index mapping
            self.chunk_to_global_index[chunk_info.id] = len(embeddings_store) - 1

            # Invalidate FAISS index if it exists
            global index
            index = None

        return chunk_info.id

    async def get_chunk(self, chunk_id: str) -> Optional[ChunkInfo]:
        """Get chunk information by ID."""
        return self.chunks.get(chunk_id)

    async def get_chunks_by_file(self, file_id: str) -> List[ChunkInfo]:
        """Get all chunks for a file."""
        chunks = [chunk for chunk in self.chunks.values() if chunk.file_id == file_id]
        chunks.sort(key=lambda c: c.start_char)
        return chunks

    async def update_chunk_embedding(self, chunk_id: str, embedding: np.ndarray) -> bool:
        """Update chunk embedding."""
        if chunk_id not in self.chunks:
            return False

        global embeddings_store, index

        self.chunk_embeddings[chunk_id] = embedding

        # Update global state
        if chunk_id in self.chunk_to_global_index:
            global_index = self.chunk_to_global_index[chunk_id]
            embeddings_store[global_index] = embedding.tolist()
            # Invalidate FAISS index
            index = None

        return True

    async def delete_chunks_by_file(self, file_id: str) -> int:
        """Delete all chunks for a file."""
        chunks_to_delete = [cid for cid, chunk in self.chunks.items() if chunk.file_id == file_id]

        for chunk_id in chunks_to_delete:
            await self._delete_chunk_from_global(chunk_id)

        return len(chunks_to_delete)

    async def _delete_chunk_from_global(self, chunk_id: str) -> None:
        """Delete chunk from global state and local mappings."""
        global embeddings_store, metadatas, index

        if chunk_id in self.chunk_to_global_index:
            global_index = self.chunk_to_global_index[chunk_id]

            # Remove from global arrays (expensive operation)
            del embeddings_store[global_index]
            del metadatas[global_index]

            # Update all indices
            for cid, idx in self.chunk_to_global_index.items():
                if idx > global_index:
                    self.chunk_to_global_index[cid] = idx - 1

            del self.chunk_to_global_index[chunk_id]

            # Invalidate FAISS index
            index = None

        # Remove from local state
        if chunk_id in self.chunks:
            del self.chunks[chunk_id]
        if chunk_id in self.chunk_embeddings:
            del self.chunk_embeddings[chunk_id]

    # Search operations

    async def search_vector(
        self,
        query_embedding: np.ndarray,
        limit: int = 10,
        min_score: float = 0.0
    ) -> List[Tuple[ChunkInfo, float]]:
        """Search for similar chunks using vector similarity."""
        results = []

        # Use existing FAISS index if available
        global index, embeddings_store, metadatas
        from backend.fastapi_chat import ensure_index

        if len(embeddings_store) == 0:
            return results

        try:
            # Ensure FAISS index is built
            ensure_index()

            if index is not None:
                # Use FAISS search
                distances, indices = index.search(query_embedding.reshape(1, -1), limit)

                for i, (distance, idx) in enumerate(zip(distances[0], indices[0])):
                    if idx == -1:  # Invalid result
                        continue

                    # Convert distance to similarity score
                    score = max(0.0, 1.0 / (1.0 + distance))

                    if score >= min_score:
                        # Find chunk by global index
                        chunk_info = self._find_chunk_by_global_index(idx)
                        if chunk_info:
                            results.append((chunk_info, score))
            else:
                # Fallback to numpy cosine similarity
                results = await self._search_vector_numpy(query_embedding, limit, min_score)

        except Exception as e:
            logger.warning(f"FAISS search failed: {e}")
            # Fallback to numpy
            results = await self._search_vector_numpy(query_embedding, limit, min_score)

        return results

    async def _search_vector_numpy(
        self,
        query_embedding: np.ndarray,
        limit: int,
        min_score: float
    ) -> List[Tuple[ChunkInfo, float]]:
        """Fallback vector search using numpy."""
        results = []

        for chunk_id, embedding in self.chunk_embeddings.items():
            similarity = self.compute_cosine_similarity(query_embedding, embedding)

            if similarity >= min_score:
                chunk_info = self.chunks.get(chunk_id)
                if chunk_info:
                    results.append((chunk_info, similarity))

        # Sort by similarity
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:limit]

    async def search_keyword(
        self,
        query: str,
        limit: int = 10,
        min_score: float = 0.0
    ) -> List[Tuple[ChunkInfo, float]]:
        """Search for chunks using keyword/text search."""
        results = []
        query_lower = query.lower()

        for chunk_info in self.chunks.values():
            text_lower = chunk_info.text.lower()

            # Simple relevance scoring
            if query_lower in text_lower:
                # Score based on term frequency and text length
                term_freq = text_lower.count(query_lower)
                score = min(1.0, term_freq / max(1, len(text_lower.split()) / 100))

                if score >= min_score:
                    results.append((chunk_info, score))

        # Sort by score
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:limit]

    # Embedding cache operations

    async def get_cached_embedding(
        self,
        text_hash: str,
        provider: str,
        model: str
    ) -> Optional[np.ndarray]:
        """Get cached embedding."""
        cache_key = f"{provider}:{model}:{text_hash}"
        return self.embedding_cache.get(cache_key)

    async def cache_embedding(
        self,
        text_hash: str,
        provider: str,
        model: str,
        embedding: np.ndarray
    ) -> None:
        """Cache an embedding."""
        cache_key = f"{provider}:{model}:{text_hash}"
        self.embedding_cache[cache_key] = embedding

    # Statistics and status

    async def get_stats(self) -> Dict[str, Any]:
        """Get storage statistics."""
        return {
            'total_files': len(self.files),
            'total_chunks': len(self.chunks),
            'total_embeddings': len(self.chunk_embeddings),
            'cache_size': len(self.embedding_cache),
            'storage_size_mb': 0.0,  # In-memory has no persistent storage
            'has_vector_support': True,  # FAISS support via existing system
            'global_embeddings_count': len(embeddings_store),
            'global_metadatas_count': len(metadatas)
        }

    async def health_check(self) -> bool:
        """Check if storage backend is healthy."""
        return self.initialized

    # Helper methods

    def _find_chunk_by_global_index(self, global_index: int) -> Optional[ChunkInfo]:
        """Find chunk by its global index."""
        for chunk_id, idx in self.chunk_to_global_index.items():
            if idx == global_index:
                return self.chunks.get(chunk_id)
        return None