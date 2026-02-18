"""
Tests for the memory system.

Basic test suite to verify memory system functionality.
"""

import pytest
import asyncio
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

from memory import MemoryManager, MemoryConfig
from memory.models import SearchOptions, FileInfo, ChunkInfo
from memory.storage import MemoryBackend, SQLiteBackend
from memory.embeddings import SentenceTransformersProvider, EmbeddingManager
from memory.processing import TextChunker, FileProcessor

class TestMemorySystem:
    """Test cases for the memory system."""

    @pytest.fixture
    async def temp_dir(self):
        """Create temporary directory for tests."""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        shutil.rmtree(temp_dir)

    @pytest.fixture
    async def memory_config(self, temp_dir):
        """Create test memory configuration."""
        return MemoryConfig(
            backend="memory",
            embeddings=MemoryConfig.EmbeddingConfig(
                provider="sentence_transformers",
                model="all-MiniLM-L6-v2",
                cache_embeddings=True
            ),
            search=MemoryConfig.SearchConfig(
                max_results=5,
                min_score=0.1,
                hybrid_enabled=True
            ),
            chunking=MemoryConfig.ChunkingConfig(
                chunk_size_chars=100,
                chunk_overlap_chars=20
            ),
            files=MemoryConfig.FileConfig(
                watch_directories=[str(temp_dir)],
                auto_sync=False
            )
        )

    @pytest.fixture
    async def memory_manager(self, memory_config):
        """Create and initialize memory manager."""
        manager = MemoryManager(memory_config)
        await manager.initialize()
        yield manager
        await manager.close()

    async def test_memory_manager_initialization(self, memory_config):
        """Test memory manager initialization."""
        manager = MemoryManager(memory_config)

        assert not manager.is_initialized

        await manager.initialize()
        assert manager.is_initialized
        assert manager.storage is not None
        assert manager.embeddings is not None
        assert manager.search is not None
        assert manager.file_processor is not None

        await manager.close()

    async def test_text_ingestion(self, memory_manager):
        """Test text ingestion."""
        test_text = "This is a test document about machine learning and artificial intelligence."

        file_id = await memory_manager.ingest_text(
            test_text,
            metadata={"title": "Test Document", "category": "test"}
        )

        assert file_id is not None

        # Verify file was stored
        file_info = await memory_manager.storage.get_file(file_id)
        assert file_info is not None
        assert file_info.metadata["title"] == "Test Document"

        # Verify chunks were created
        chunks = await memory_manager.storage.get_chunks_by_file(file_id)
        assert len(chunks) > 0
        assert all(chunk.text for chunk in chunks)

    async def test_file_ingestion(self, memory_manager, temp_dir):
        """Test file ingestion."""
        # Create test file
        test_file = temp_dir / "test.md"
        test_content = "# Test Document\n\nThis is a test markdown file with some content about Python programming."
        test_file.write_text(test_content)

        file_id = await memory_manager.ingest_file(
            test_file,
            metadata={"source": "test"}
        )

        assert file_id is not None

        # Verify file was stored
        file_info = await memory_manager.storage.get_file(file_id)
        assert file_info is not None
        assert file_info.path == str(test_file)

        # Verify chunks were created
        chunks = await memory_manager.storage.get_chunks_by_file(file_id)
        assert len(chunks) > 0

    async def test_search_functionality(self, memory_manager):
        """Test search functionality."""
        # Ingest test documents
        docs = [
            "Python is a programming language used for web development.",
            "Machine learning algorithms can process large datasets.",
            "FastAPI is a modern web framework for building APIs with Python."
        ]

        file_ids = []
        for i, doc in enumerate(docs):
            file_id = await memory_manager.ingest_text(
                doc,
                metadata={"title": f"Document {i+1}"}
            )
            file_ids.append(file_id)

        # Test vector search
        results = await memory_manager.search(
            "Python programming",
            SearchOptions(mode="vector", max_results=2, min_score=0.1)
        )

        assert len(results) > 0
        assert any("Python" in result.text for result in results)

        # Test keyword search
        results = await memory_manager.search(
            "machine learning",
            SearchOptions(mode="keyword", max_results=2, min_score=0.1)
        )

        assert len(results) > 0
        assert any("machine learning" in result.text.lower() for result in results)

        # Test hybrid search
        results = await memory_manager.search(
            "web development",
            SearchOptions(mode="hybrid", max_results=3, min_score=0.1)
        )

        assert len(results) > 0

    async def test_system_status(self, memory_manager):
        """Test system status reporting."""
        # Ingest some content
        await memory_manager.ingest_text("Test content for status check.")

        status = await memory_manager.get_status()

        assert status.is_healthy
        assert status.total_files >= 1
        assert status.total_chunks >= 1
        assert len(status.embedding_providers) > 0
        assert status.backend == "memory"

class TestTextChunker:
    """Test cases for text chunking."""

    def test_basic_chunking(self):
        """Test basic text chunking."""
        chunker = TextChunker(chunk_size_chars=50, chunk_overlap_chars=10)

        text = "This is a test document. " * 10  # ~250 chars
        chunks = chunker.chunk_text(text)

        assert len(chunks) > 1
        assert all(chunk.length <= 60 for chunk in chunks)  # Allow some tolerance
        assert all(chunk.start_char < chunk.end_char for chunk in chunks)

        # Check overlap
        if len(chunks) > 1:
            # Verify chunks are properly ordered
            for i in range(len(chunks) - 1):
                assert chunks[i].end_char > chunks[i+1].start_char  # Overlap exists

    def test_empty_text(self):
        """Test chunking empty text."""
        chunker = TextChunker()
        chunks = chunker.chunk_text("")
        assert len(chunks) == 0

        chunks = chunker.chunk_text("   \n\n  ")
        assert len(chunks) == 0

    def test_short_text(self):
        """Test chunking text shorter than chunk size."""
        chunker = TextChunker(chunk_size_chars=100)
        text = "Short text."

        chunks = chunker.chunk_text(text)

        assert len(chunks) == 1
        assert chunks[0].text == text
        assert chunks[0].start_char == 0
        assert chunks[0].end_char == len(text)

class TestEmbeddingManager:
    """Test cases for embedding management."""

    @pytest.fixture
    async def embedding_manager(self):
        """Create embedding manager for tests."""
        manager = EmbeddingManager(
            primary_provider="sentence_transformers",
            fallback_provider="sentence_transformers",
            sentence_transformers={"model": "all-MiniLM-L6-v2", "batch_size": 2}
        )
        await manager.initialize()
        yield manager

    async def test_single_embedding(self, embedding_manager):
        """Test single text embedding."""
        text = "This is a test sentence."
        embedding = await embedding_manager.embed_single(text)

        assert embedding is not None
        assert len(embedding.shape) == 1
        assert embedding.shape[0] > 0

    async def test_batch_embedding(self, embedding_manager):
        """Test batch embedding."""
        texts = [
            "First test sentence.",
            "Second test sentence.",
            "Third test sentence."
        ]

        embeddings = await embedding_manager.embed(texts)

        assert len(embeddings) == len(texts)
        assert all(emb.shape[0] > 0 for emb in embeddings)

    async def test_empty_input(self, embedding_manager):
        """Test embedding with empty input."""
        embeddings = await embedding_manager.embed([])
        assert len(embeddings) == 0

    async def test_provider_status(self, embedding_manager):
        """Test provider status reporting."""
        status = await embedding_manager.get_provider_status()

        assert "sentence_transformers" in status
        assert status["sentence_transformers"]["available"]
        assert status["sentence_transformers"]["dimensions"] > 0

class TestStorageBackends:
    """Test cases for storage backends."""

    @pytest.fixture
    async def memory_backend(self):
        """Create memory backend for tests."""
        backend = MemoryBackend()
        await backend.initialize()
        yield backend
        await backend.close()

    @pytest.fixture
    async def sqlite_backend(self):
        """Create SQLite backend for tests."""
        backend = SQLiteBackend(":memory:")
        await backend.initialize()
        yield backend
        await backend.close()

    async def test_file_operations(self, memory_backend):
        """Test file CRUD operations."""
        file_info = FileInfo(
            id="test-file-1",
            path="/test/path.txt",
            hash="test-hash",
            size=100,
            mtime=datetime.now().timestamp(),
            metadata={"test": "data"},
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        # Add file
        file_id = await memory_backend.add_file(file_info)
        assert file_id == file_info.id

        # Get file
        retrieved = await memory_backend.get_file(file_id)
        assert retrieved is not None
        assert retrieved.id == file_info.id
        assert retrieved.path == file_info.path

        # Update file
        file_info.size = 200
        updated = await memory_backend.update_file(file_info)
        assert updated

        # List files
        files = await memory_backend.list_files()
        assert len(files) == 1

        # Delete file
        deleted = await memory_backend.delete_file(file_id)
        assert deleted

        # Verify deletion
        retrieved = await memory_backend.get_file(file_id)
        assert retrieved is None

    async def test_chunk_operations(self, memory_backend):
        """Test chunk operations."""
        # First create a file
        file_info = FileInfo(
            id="test-file-2",
            path="/test/chunks.txt",
            hash="chunk-hash",
            size=50,
            mtime=datetime.now().timestamp(),
            metadata={},
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        await memory_backend.add_file(file_info)

        # Create chunk
        chunk_info = ChunkInfo(
            id="test-chunk-1",
            file_id=file_info.id,
            text="This is a test chunk.",
            start_char=0,
            end_char=22,
            metadata={},
            created_at=datetime.now()
        )

        # Add chunk
        chunk_id = await memory_backend.add_chunk(chunk_info)
        assert chunk_id == chunk_info.id

        # Get chunk
        retrieved = await memory_backend.get_chunk(chunk_id)
        assert retrieved is not None
        assert retrieved.text == chunk_info.text

        # Get chunks by file
        chunks = await memory_backend.get_chunks_by_file(file_info.id)
        assert len(chunks) == 1

    async def test_health_check(self, memory_backend):
        """Test backend health check."""
        healthy = await memory_backend.health_check()
        assert healthy

    async def test_stats(self, memory_backend):
        """Test statistics retrieval."""
        stats = await memory_backend.get_stats()
        assert isinstance(stats, dict)
        assert "total_files" in stats
        assert "total_chunks" in stats

# Test runner
if __name__ == "__main__":
    pytest.main([__file__, "-v"])