"""
SQLite storage backend with vector search support.
"""

import sqlite3
import json
import hashlib
import logging
from pathlib import Path
from typing import List, Dict, Optional, Any, Tuple
import numpy as np
from datetime import datetime
import uuid

from .base import StorageBackend
from ..models import FileInfo, ChunkInfo

logger = logging.getLogger(__name__)

class SQLiteBackend(StorageBackend):
    """SQLite-based storage backend with FTS5 support and optional vector search."""

    def __init__(self, db_path: str = ":memory:", enable_vector: bool = True):
        """
        Initialize SQLite backend.

        Args:
            db_path: Path to SQLite database file or ":memory:" for in-memory
            enable_vector: Whether to try to enable vector search extensions
        """
        self.db_path = db_path
        self.enable_vector = enable_vector
        self.connection: Optional[sqlite3.Connection] = None
        self.has_vector_support = False

    async def initialize(self) -> None:
        """Initialize the SQLite database and create schema."""
        try:
            # Create database directory if needed
            if self.db_path != ":memory:":
                Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

            # Open connection
            self.connection = sqlite3.connect(self.db_path, check_same_thread=False)
            self.connection.row_factory = sqlite3.Row  # Enable dict-like access
            self.connection.execute("PRAGMA foreign_keys = ON")  # Enable foreign keys

            # Try to load vector extension
            if self.enable_vector:
                try:
                    # Try to load sqlite-vec extension (if available)
                    self.connection.enable_load_extension(True)
                    self.connection.load_extension("sqlite_vec")
                    self.has_vector_support = True
                    logger.info("Vector search extension loaded successfully")
                except Exception as e:
                    logger.warning(f"Vector extension not available: {e}")
                    self.has_vector_support = False

            # Create schema
            await self._create_schema()

            logger.info(f"SQLite backend initialized at {self.db_path}")

        except Exception as e:
            logger.error(f"Failed to initialize SQLite backend: {e}")
            raise

    async def close(self) -> None:
        """Close the database connection."""
        if self.connection:
            self.connection.close()
            self.connection = None

    async def _create_schema(self) -> None:
        """Create the database schema."""
        cursor = self.connection.cursor()

        # Metadata table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS meta (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)

        # Files table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS files (
                id TEXT PRIMARY KEY,
                path TEXT UNIQUE NOT NULL,
                hash TEXT NOT NULL,
                size INTEGER NOT NULL,
                mtime REAL NOT NULL,
                metadata TEXT DEFAULT '{}',
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL
            )
        """)

        # Chunks table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chunks (
                rowid INTEGER PRIMARY KEY AUTOINCREMENT,
                id TEXT UNIQUE NOT NULL,
                file_id TEXT NOT NULL,
                text TEXT NOT NULL,
                embedding BLOB,
                start_char INTEGER NOT NULL,
                end_char INTEGER NOT NULL,
                metadata TEXT DEFAULT '{}',
                created_at REAL NOT NULL,
                FOREIGN KEY (file_id) REFERENCES files(id) ON DELETE CASCADE
            )
        """)

        # Full-text search table
        cursor.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING fts5(
                text,
                content='chunks',
                content_rowid='rowid'
            )
        """)

        # Embedding cache table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS embedding_cache (
                hash TEXT PRIMARY KEY,
                provider TEXT NOT NULL,
                model TEXT NOT NULL,
                embedding BLOB NOT NULL,
                created_at REAL NOT NULL
            )
        """)

        # Indexes for better performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_files_path ON files(path)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_files_hash ON files(hash)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_chunks_file_id ON chunks(file_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_embedding_cache_provider_model ON embedding_cache(provider, model)")

        # Vector search table (if supported)
        if self.has_vector_support:
            # Get embedding dimension from first embedding or use default
            dimension = 384  # Default for sentence-transformers all-MiniLM-L6-v2
            try:
                cursor.execute(f"""
                    CREATE VIRTUAL TABLE IF NOT EXISTS chunks_vec USING vec0(
                        embedding float[{dimension}]
                    )
                """)
                logger.info(f"Vector search table created with dimension {dimension}")
            except Exception as e:
                logger.warning(f"Failed to create vector table: {e}")
                self.has_vector_support = False

        self.connection.commit()

    # File operations

    async def add_file(self, file_info: FileInfo) -> str:
        """Add a file to storage."""
        cursor = self.connection.cursor()

        cursor.execute("""
            INSERT OR REPLACE INTO files (id, path, hash, size, mtime, metadata, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            file_info.id,
            file_info.path,
            file_info.hash,
            file_info.size,
            file_info.mtime,
            json.dumps(file_info.metadata),
            file_info.created_at.timestamp(),
            file_info.updated_at.timestamp()
        ))

        self.connection.commit()
        return file_info.id

    async def get_file(self, file_id: str) -> Optional[FileInfo]:
        """Get file information by ID."""
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM files WHERE id = ?", (file_id,))
        row = cursor.fetchone()

        if row:
            return self._row_to_file_info(row)
        return None

    async def get_file_by_path(self, path: str) -> Optional[FileInfo]:
        """Get file information by path."""
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM files WHERE path = ?", (path,))
        row = cursor.fetchone()

        if row:
            return self._row_to_file_info(row)
        return None

    async def list_files(self, limit: Optional[int] = None, offset: int = 0) -> List[FileInfo]:
        """List all files."""
        cursor = self.connection.cursor()

        query = "SELECT * FROM files ORDER BY updated_at DESC"
        params = []

        if limit:
            query += " LIMIT ? OFFSET ?"
            params.extend([limit, offset])

        cursor.execute(query, params)
        rows = cursor.fetchall()

        return [self._row_to_file_info(row) for row in rows]

    async def update_file(self, file_info: FileInfo) -> bool:
        """Update file information."""
        cursor = self.connection.cursor()

        cursor.execute("""
            UPDATE files
            SET path = ?, hash = ?, size = ?, mtime = ?, metadata = ?, updated_at = ?
            WHERE id = ?
        """, (
            file_info.path,
            file_info.hash,
            file_info.size,
            file_info.mtime,
            json.dumps(file_info.metadata),
            datetime.now().timestamp(),
            file_info.id
        ))

        self.connection.commit()
        return cursor.rowcount > 0

    async def delete_file(self, file_id: str) -> bool:
        """Delete a file and all its chunks."""
        cursor = self.connection.cursor()

        # Delete file (chunks will be deleted by foreign key cascade)
        cursor.execute("DELETE FROM files WHERE id = ?", (file_id,))

        self.connection.commit()
        return cursor.rowcount > 0

    # Chunk operations

    async def add_chunk(self, chunk_info: ChunkInfo, embedding: Optional[np.ndarray] = None) -> str:
        """Add a chunk to storage."""
        cursor = self.connection.cursor()

        # Serialize embedding if provided
        embedding_blob = None
        if embedding is not None:
            embedding_blob = embedding.tobytes()

        cursor.execute("""
            INSERT INTO chunks (id, file_id, text, embedding, start_char, end_char, metadata, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            chunk_info.id,
            chunk_info.file_id,
            chunk_info.text,
            embedding_blob,
            chunk_info.start_char,
            chunk_info.end_char,
            json.dumps(chunk_info.metadata),
            chunk_info.created_at.timestamp()
        ))

        # Get the rowid of the inserted chunk
        chunk_rowid = cursor.lastrowid

        # Add to FTS index
        cursor.execute("INSERT INTO chunks_fts(rowid, text) VALUES (?, ?)",
                      (chunk_rowid, chunk_info.text))

        # Add to vector index if supported
        if self.has_vector_support and embedding is not None:
            try:
                cursor.execute("INSERT INTO chunks_vec(rowid, embedding) VALUES (?, ?)",
                              (chunk_rowid, embedding.tobytes()))
            except Exception as e:
                logger.warning(f"Failed to insert into vector index: {e}")

        self.connection.commit()
        return chunk_info.id

    async def get_chunk(self, chunk_id: str) -> Optional[ChunkInfo]:
        """Get chunk information by ID."""
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM chunks WHERE id = ?", (chunk_id,))
        row = cursor.fetchone()

        if row:
            return self._row_to_chunk_info(row)
        return None

    async def get_chunks_by_file(self, file_id: str) -> List[ChunkInfo]:
        """Get all chunks for a file."""
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM chunks WHERE file_id = ? ORDER BY start_char", (file_id,))
        rows = cursor.fetchall()

        return [self._row_to_chunk_info(row) for row in rows]

    async def update_chunk_embedding(self, chunk_id: str, embedding: np.ndarray) -> bool:
        """Update chunk embedding."""
        cursor = self.connection.cursor()

        embedding_blob = embedding.tobytes()
        cursor.execute("UPDATE chunks SET embedding = ? WHERE id = ?", (embedding_blob, chunk_id))

        # Update vector index if supported
        if self.has_vector_support:
            try:
                cursor.execute("UPDATE chunks_vec SET embedding = ? WHERE rowid = ?",
                              (embedding_blob, chunk_id))
            except Exception as e:
                logger.warning(f"Failed to update vector index: {e}")

        self.connection.commit()
        return cursor.rowcount > 0

    async def delete_chunks_by_file(self, file_id: str) -> int:
        """Delete all chunks for a file."""
        cursor = self.connection.cursor()

        # Get chunk rowids first
        cursor.execute("SELECT rowid FROM chunks WHERE file_id = ?", (file_id,))
        chunk_rowids = [row[0] for row in cursor.fetchall()]

        # Delete from FTS index
        for chunk_rowid in chunk_rowids:
            cursor.execute("DELETE FROM chunks_fts WHERE rowid = ?", (chunk_rowid,))

        # Delete from vector index if supported
        if self.has_vector_support:
            for chunk_rowid in chunk_rowids:
                try:
                    cursor.execute("DELETE FROM chunks_vec WHERE rowid = ?", (chunk_rowid,))
                except Exception as e:
                    logger.warning(f"Failed to delete from vector index: {e}")

        # Delete chunks
        cursor.execute("DELETE FROM chunks WHERE file_id = ?", (file_id,))

        deleted_count = cursor.rowcount
        self.connection.commit()
        return deleted_count

    # Search operations

    async def search_vector(
        self,
        query_embedding: np.ndarray,
        limit: int = 10,
        min_score: float = 0.0
    ) -> List[Tuple[ChunkInfo, float]]:
        """Search for similar chunks using vector similarity."""
        cursor = self.connection.cursor()
        results = []

        if self.has_vector_support:
            # Use vector extension for fast search
            try:
                cursor.execute("""
                    SELECT c.*, distance
                    FROM chunks_vec v
                    JOIN chunks c ON c.id = v.rowid
                    WHERE v.embedding MATCH ?
                    ORDER BY distance
                    LIMIT ?
                """, (query_embedding.tobytes(), limit))

                for row in cursor.fetchall():
                    chunk_info = self._row_to_chunk_info(row)
                    # Convert distance to similarity score (0-1)
                    score = max(0.0, 1.0 - row['distance'])

                    if score >= min_score:
                        results.append((chunk_info, score))

            except Exception as e:
                logger.warning(f"Vector search failed: {e}")
                # Fall back to brute force
                results = await self._search_vector_brute_force(query_embedding, limit, min_score)
        else:
            # Brute force similarity search
            results = await self._search_vector_brute_force(query_embedding, limit, min_score)

        return results

    async def _search_vector_brute_force(
        self,
        query_embedding: np.ndarray,
        limit: int,
        min_score: float
    ) -> List[Tuple[ChunkInfo, float]]:
        """Brute force vector similarity search."""
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM chunks WHERE embedding IS NOT NULL")

        results = []
        for row in cursor.fetchall():
            # Deserialize embedding
            embedding_blob = row['embedding']
            if embedding_blob:
                embedding = np.frombuffer(embedding_blob, dtype=np.float32)

                # Compute similarity
                similarity = self.compute_cosine_similarity(query_embedding, embedding)

                if similarity >= min_score:
                    chunk_info = self._row_to_chunk_info(row)
                    results.append((chunk_info, similarity))

        # Sort by similarity and limit results
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:limit]

    async def search_keyword(
        self,
        query: str,
        limit: int = 10,
        min_score: float = 0.0
    ) -> List[Tuple[ChunkInfo, float]]:
        """Search for chunks using keyword/text search."""
        cursor = self.connection.cursor()

        try:
            # Use FTS5 for fast text search
            cursor.execute("""
                SELECT c.*, bm25(chunks_fts) as score
                FROM chunks_fts
                JOIN chunks c ON c.rowid = chunks_fts.rowid
                WHERE chunks_fts MATCH ?
                ORDER BY score
                LIMIT ?
            """, (query, limit))

            results = []
            for row in cursor.fetchall():
                chunk_info = self._row_to_chunk_info(row)
                # Normalize BM25 score to 0-1 range (rough approximation)
                score = max(0.0, min(1.0, (-row['score'] + 10) / 10))

                if score >= min_score:
                    results.append((chunk_info, score))

            return results

        except Exception as e:
            logger.warning(f"FTS search failed: {e}")
            # Fallback to simple text search
            return await self._search_keyword_simple(query, limit, min_score)

    async def _search_keyword_simple(
        self,
        query: str,
        limit: int,
        min_score: float
    ) -> List[Tuple[ChunkInfo, float]]:
        """Simple keyword search fallback."""
        cursor = self.connection.cursor()

        # Simple LIKE search
        search_pattern = f"%{query}%"
        cursor.execute("""
            SELECT * FROM chunks
            WHERE text LIKE ?
            ORDER BY length(text)
            LIMIT ?
        """, (search_pattern, limit))

        results = []
        for row in cursor.fetchall():
            chunk_info = self._row_to_chunk_info(row)
            # Simple relevance score based on query term frequency
            score = min(1.0, chunk_info.text.lower().count(query.lower()) / 10.0)

            if score >= min_score:
                results.append((chunk_info, score))

        return results

    # Embedding cache operations

    async def get_cached_embedding(
        self,
        text_hash: str,
        provider: str,
        model: str
    ) -> Optional[np.ndarray]:
        """Get cached embedding."""
        cursor = self.connection.cursor()
        cursor.execute("""
            SELECT embedding FROM embedding_cache
            WHERE hash = ? AND provider = ? AND model = ?
        """, (text_hash, provider, model))

        row = cursor.fetchone()
        if row and row['embedding']:
            return np.frombuffer(row['embedding'], dtype=np.float32)
        return None

    async def cache_embedding(
        self,
        text_hash: str,
        provider: str,
        model: str,
        embedding: np.ndarray
    ) -> None:
        """Cache an embedding."""
        cursor = self.connection.cursor()

        cursor.execute("""
            INSERT OR REPLACE INTO embedding_cache (hash, provider, model, embedding, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (text_hash, provider, model, embedding.tobytes(), datetime.now().timestamp()))

        self.connection.commit()

    # Statistics and status

    async def get_stats(self) -> Dict[str, Any]:
        """Get storage statistics."""
        cursor = self.connection.cursor()

        stats = {}

        # File count
        cursor.execute("SELECT COUNT(*) as count FROM files")
        stats['total_files'] = cursor.fetchone()['count']

        # Chunk count
        cursor.execute("SELECT COUNT(*) as count FROM chunks")
        stats['total_chunks'] = cursor.fetchone()['count']

        # Embeddings count
        cursor.execute("SELECT COUNT(*) as count FROM chunks WHERE embedding IS NOT NULL")
        stats['total_embeddings'] = cursor.fetchone()['count']

        # Cache size
        cursor.execute("SELECT COUNT(*) as count FROM embedding_cache")
        stats['cache_size'] = cursor.fetchone()['count']

        # Storage size (approximate)
        if self.db_path != ":memory:":
            try:
                stats['storage_size_mb'] = Path(self.db_path).stat().st_size / (1024 * 1024)
            except:
                stats['storage_size_mb'] = 0.0
        else:
            stats['storage_size_mb'] = 0.0

        # Vector support
        stats['has_vector_support'] = self.has_vector_support

        return stats

    async def health_check(self) -> bool:
        """Check if storage backend is healthy."""
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            return True
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False

    # Helper methods

    def _row_to_file_info(self, row: sqlite3.Row) -> FileInfo:
        """Convert database row to FileInfo object."""
        return FileInfo(
            id=row['id'],
            path=row['path'],
            hash=row['hash'],
            size=row['size'],
            mtime=row['mtime'],
            metadata=json.loads(row['metadata'] or '{}'),
            created_at=datetime.fromtimestamp(row['created_at']),
            updated_at=datetime.fromtimestamp(row['updated_at'])
        )

    def _row_to_chunk_info(self, row: sqlite3.Row) -> ChunkInfo:
        """Convert database row to ChunkInfo object."""
        return ChunkInfo(
            id=row['id'],
            file_id=row['file_id'],
            text=row['text'],
            start_char=row['start_char'],
            end_char=row['end_char'],
            metadata=json.loads(row['metadata'] or '{}'),
            created_at=datetime.fromtimestamp(row['created_at'])
        )