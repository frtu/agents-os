"""
Main Memory Manager that coordinates all memory system components.
"""

import asyncio
import logging
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
from datetime import datetime

from .config import MemoryConfig, load_memory_config, get_api_key
from .models import (
    SearchResult, SearchOptions, MemoryStatus, SyncStats,
    FileInfo, ChunkInfo, ProviderStatus
)
from .storage import StorageBackend, SQLiteBackend, MemoryBackend
from .embeddings import EmbeddingManager
from .search import HybridSearch
from .processing import FileProcessor, FileWatcher, SimpleFileWatcher

logger = logging.getLogger(__name__)

class MemoryManager:
    """
    Main memory system coordinator.

    Manages storage, embeddings, search, and file processing.
    """

    def __init__(self, config: Optional[MemoryConfig] = None):
        """
        Initialize memory manager.

        Args:
            config: Memory configuration. If None, loads from default location.
        """
        self.config = config or load_memory_config()
        self.storage: Optional[StorageBackend] = None
        self.embeddings: Optional[EmbeddingManager] = None
        self.search_engine: Optional[HybridSearch] = None
        self.file_processor: Optional[FileProcessor] = None
        self.file_watcher: Optional[Union[FileWatcher, SimpleFileWatcher]] = None

        self.is_initialized = False
        self.last_sync: Optional[datetime] = None
        self.sync_in_progress = False

    async def initialize(self) -> None:
        """Initialize all components."""
        if self.is_initialized:
            return

        logger.info("Initializing memory system...")

        try:
            # Initialize storage backend
            await self._init_storage()

            # Initialize embedding manager
            await self._init_embeddings()

            # Initialize search
            await self._init_search()

            # Initialize file processor
            self._init_file_processor()

            # Initialize file watcher if auto-sync is enabled
            if self.config.files.auto_sync:
                await self._init_file_watcher()

            self.is_initialized = True
            logger.info("Memory system initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize memory system: {e}")
            await self.close()
            raise

    async def close(self) -> None:
        """Close all components and clean up."""
        logger.info("Closing memory system...")

        if self.file_watcher:
            try:
                await self.file_watcher.stop_watching()
            except Exception as e:
                logger.warning(f"Error stopping file watcher: {e}")

        if self.storage:
            try:
                await self.storage.close()
            except Exception as e:
                logger.warning(f"Error closing storage: {e}")

        self.is_initialized = False
        logger.info("Memory system closed")

    async def _init_storage(self) -> None:
        """Initialize storage backend."""
        if self.config.backend == "sqlite":
            self.storage = SQLiteBackend(
                db_path=self.config.storage_path,
                enable_vector=True
            )
        elif self.config.backend == "memory":
            self.storage = MemoryBackend()
        else:
            raise ValueError(f"Unknown backend: {self.config.backend}")

        await self.storage.initialize()
        logger.info(f"Storage backend initialized: {self.config.backend}")

    async def _init_embeddings(self) -> None:
        """Initialize embedding manager."""
        # Prepare provider configurations
        provider_configs = {}

        # Sentence transformers config
        provider_configs["sentence_transformers"] = {
            "model": self.config.embeddings.model,
            "batch_size": self.config.embeddings.batch_size
        }

        # OpenAI config
        if self.config.embeddings.openai:
            api_key = get_api_key("openai", self.config)
            if api_key:
                provider_configs["openai"] = {
                    "model": self.config.embeddings.openai.get("model", "text-embedding-3-small"),
                    "api_key": api_key,
                    "base_url": self.config.embeddings.openai.get("base_url")
                }

        # Gemini config
        if self.config.embeddings.gemini:
            api_key = get_api_key("gemini", self.config)
            if api_key:
                provider_configs["gemini"] = {
                    "model": self.config.embeddings.gemini.get("model", "gemini-embedding-001"),
                    "api_key": api_key
                }

        # Voyage config
        if self.config.embeddings.voyage:
            api_key = get_api_key("voyage", self.config)
            if api_key:
                provider_configs["voyage"] = {
                    "model": self.config.embeddings.voyage.get("model", "voyage-4-large"),
                    "api_key": api_key
                }

        self.embeddings = EmbeddingManager(
            primary_provider=self.config.embeddings.provider,
            fallback_provider=self.config.embeddings.fallback_provider,
            cache_enabled=self.config.embeddings.cache_embeddings,
            storage_backend=self.storage if self.config.embeddings.cache_embeddings else None,
            **provider_configs
        )

        await self.embeddings.initialize()
        logger.info("Embedding manager initialized")

    async def _init_search(self) -> None:
        """Initialize search system."""
        logger.debug(f"Initializing search with storage={self.storage} embeddings={self.embeddings}")
        self.search_engine = HybridSearch(self.storage, self.embeddings)
        logger.info(f"Search system initialized: search_engine={self.search_engine}")

    def _init_file_processor(self) -> None:
        """Initialize file processor."""
        self.file_processor = FileProcessor(
            chunk_size_chars=self.config.chunking.chunk_size_chars,
            chunk_overlap_chars=self.config.chunking.chunk_overlap_chars,
            max_file_size_mb=self.config.files.max_file_size_mb,
            supported_extensions=[
                ext if ext.startswith('.') else f'.{ext}'
                for ext in self.config.files.file_patterns
                if not '*' in ext
            ] or None
        )
        logger.info("File processor initialized")

    async def _init_file_watcher(self) -> None:
        """Initialize file watcher."""
        try:
            # Try to use advanced file watcher
            self.file_watcher = FileWatcher(
                debounce_seconds=1.5,
                supported_extensions=[
                    ext if ext.startswith('.') else f'.{ext}'
                    for ext in self.config.files.file_patterns
                    if not '*' in ext
                ]
            )

            # Start watching configured directories
            watch_paths = [Path(d) for d in self.config.files.watch_directories if Path(d).exists()]
            if watch_paths:
                await self.file_watcher.start_watching(watch_paths, self._on_files_changed)
                logger.info(f"File watcher started for {len(watch_paths)} directories")

        except ImportError:
            logger.warning("watchdog not available, using simple file watcher")
            # Fallback to simple polling watcher
            self.file_watcher = SimpleFileWatcher(
                poll_interval_seconds=self.config.files.sync_interval_seconds,
                supported_extensions=[
                    ext if ext.startswith('.') else f'.{ext}'
                    for ext in self.config.files.file_patterns
                    if not '*' in ext
                ]
            )

            watch_paths = [Path(d) for d in self.config.files.watch_directories if Path(d).exists()]
            if watch_paths:
                await self.file_watcher.start_watching(watch_paths, self._on_files_changed)
                logger.info(f"Simple file watcher started for {len(watch_paths)} directories")

    async def _on_files_changed(self, changed_files: List[Path]) -> None:
        """Handle file change events."""
        logger.info(f"Processing {len(changed_files)} changed files")

        try:
            # Filter for existing files (ignore deletions for now)
            existing_files = [f for f in changed_files if f.exists()]

            if existing_files:
                stats = await self._sync_files(existing_files)
                logger.info(f"Sync completed: {stats.files_processed} files processed, "
                           f"{stats.chunks_created} chunks created")

        except Exception as e:
            logger.error(f"Error processing file changes: {e}")

    # Public API methods

    async def search(self, query: str, options: Optional[SearchOptions] = None) -> List[SearchResult]:
        """
        Search for content in memory.

        Args:
            query: Search query
            options: Search options

        Returns:
            List of search results
        """
        if not self.is_initialized:
            await self.initialize()

        if not options:
            options = SearchOptions(
                mode="hybrid" if self.config.search.hybrid_enabled else "vector",
                max_results=self.config.search.max_results,
                min_score=self.config.search.min_score,
                vector_weight=self.config.search.vector_weight,
                keyword_weight=self.config.search.keyword_weight
            )

        # Debug: Check if search_engine is None
        if self.search_engine is None:
            logger.error("search_engine is None! Re-initializing search system...")
            await self._init_search()

        start_time = time.time()
        results = await self.search_engine.search(query, options)
        search_time = (time.time() - start_time) * 1000

        logger.debug(f"Search completed in {search_time:.2f}ms, {len(results)} results")
        return results

    async def ingest_text(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Ingest text content into memory.

        Args:
            text: Text content
            metadata: Optional metadata

        Returns:
            File ID
        """
        if not self.is_initialized:
            await self.initialize()

        start_time = time.time()

        try:
            # Process text
            file_info, chunks = await self.file_processor.process_text(
                text,
                metadata=metadata
            )

            # Store file
            file_id = await self.storage.add_file(file_info)

            # Generate and store embeddings
            embeddings_generated = 0
            for chunk in chunks:
                embedding = await self.embeddings.embed_single(chunk.text)
                await self.storage.add_chunk(chunk, embedding)
                embeddings_generated += 1

            processing_time = (time.time() - start_time) * 1000

            logger.info(f"Ingested text: {len(chunks)} chunks, {embeddings_generated} embeddings "
                       f"in {processing_time:.2f}ms")

            return file_id

        except Exception as e:
            logger.error(f"Failed to ingest text: {e}")
            raise

    async def ingest_file(self, file_path: Union[str, Path], metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Ingest a file into memory.

        Args:
            file_path: Path to file
            metadata: Optional metadata

        Returns:
            File ID
        """
        if not self.is_initialized:
            await self.initialize()

        start_time = time.time()
        file_path = Path(file_path)

        try:
            # Check if file already exists
            existing_file = await self.storage.get_file_by_path(str(file_path))
            if existing_file:
                # Check if file has changed
                if not self.file_processor.is_file_changed(
                    file_path, existing_file.hash, existing_file.mtime
                ):
                    logger.debug(f"File unchanged, skipping: {file_path}")
                    return existing_file.id

                # File changed, delete old chunks
                await self.storage.delete_chunks_by_file(existing_file.id)

            # Process file
            file_info, chunks = await self.file_processor.process_file(file_path, metadata)

            # Store or update file
            if existing_file:
                file_info.id = existing_file.id
                await self.storage.update_file(file_info)
                file_id = file_info.id
            else:
                file_id = await self.storage.add_file(file_info)

            # Generate and store embeddings
            embeddings_generated = 0
            for chunk in chunks:
                embedding = await self.embeddings.embed_single(chunk.text)
                await self.storage.add_chunk(chunk, embedding)
                embeddings_generated += 1

            processing_time = (time.time() - start_time) * 1000

            logger.info(f"Ingested file {file_path}: {len(chunks)} chunks, "
                       f"{embeddings_generated} embeddings in {processing_time:.2f}ms")

            return file_id

        except Exception as e:
            logger.error(f"Failed to ingest file {file_path}: {e}")
            raise

    async def get_file(self, file_id: str, lines: Optional[tuple[int, int]] = None) -> str:
        """
        Get file content by ID.

        Args:
            file_id: File ID
            lines: Optional line range (start, end)

        Returns:
            File content
        """
        if not self.is_initialized:
            await self.initialize()

        file_info = await self.storage.get_file(file_id)
        if not file_info:
            raise ValueError(f"File not found: {file_id}")

        # For now, return the path - could be enhanced to return actual content
        if file_info.path and Path(file_info.path).exists():
            content = Path(file_info.path).read_text()

            if lines:
                start_line, end_line = lines
                content_lines = content.split('\n')
                content = '\n'.join(content_lines[start_line:end_line])

            return content
        else:
            # Return content from chunks
            chunks = await self.storage.get_chunks_by_file(file_id)
            return '\n\n'.join(chunk.text for chunk in chunks)

    async def sync_files(self, paths: Optional[List[str]] = None) -> SyncStats:
        """
        Synchronize files with memory.

        Args:
            paths: Optional list of specific paths to sync

        Returns:
            Sync statistics
        """
        if not self.is_initialized:
            await self.initialize()

        if self.sync_in_progress:
            logger.warning("Sync already in progress")
            return SyncStats(files_processed=0)

        self.sync_in_progress = True
        start_time = time.time()

        try:
            if paths:
                files_to_sync = [Path(p) for p in paths]
            else:
                # Sync all configured directories
                files_to_sync = []
                for dir_path in self.config.files.watch_directories:
                    dir_path = Path(dir_path)
                    if dir_path.exists():
                        files_to_sync.extend(dir_path.rglob('*'))

            # Filter for supported files
            files_to_sync = [
                f for f in files_to_sync
                if f.is_file() and self.file_processor._is_supported_file(f)
            ]

            stats = await self._sync_files(files_to_sync)
            stats.processing_time_ms = (time.time() - start_time) * 1000

            self.last_sync = datetime.now()
            logger.info(f"Sync completed: {stats}")

            return stats

        finally:
            self.sync_in_progress = False

    async def _sync_files(self, files: List[Path]) -> SyncStats:
        """Internal file synchronization."""
        stats = SyncStats()

        for file_path in files:
            try:
                # Check if file is already in storage
                existing_file = await self.storage.get_file_by_path(str(file_path))

                if existing_file:
                    # Check if file changed
                    if self.file_processor.is_file_changed(
                        file_path, existing_file.hash, existing_file.mtime
                    ):
                        await self.ingest_file(file_path)
                        stats.files_updated += 1
                else:
                    # New file
                    await self.ingest_file(file_path)
                    stats.files_added += 1

                stats.files_processed += 1

            except Exception as e:
                logger.warning(f"Failed to sync file {file_path}: {e}")
                stats.errors.append(f"{file_path}: {e}")

        return stats

    async def get_status(self) -> MemoryStatus:
        """
        Get memory system status.

        Returns:
            System status
        """
        if not self.is_initialized:
            return MemoryStatus(
                backend="not_initialized",
                total_files=0,
                total_chunks=0,
                total_embeddings=0,
                storage_size_mb=0.0,
                embedding_providers=[],
                cache_size=0,
                is_healthy=False
            )

        # Get storage stats
        storage_stats = await self.storage.get_stats()

        # Get embedding provider status
        provider_status = await self.embeddings.get_provider_status()

        providers = []
        for name, status in provider_status.items():
            if isinstance(status, dict) and 'name' in status:
                providers.append(ProviderStatus(
                    name=status['name'],
                    model=status['model'],
                    available=status['available'],
                    dimensions=status.get('dimensions'),
                    error=status.get('health', {}).get('error')
                ))

        # Check health
        storage_healthy = await self.storage.health_check()
        embedding_healthy = any(p.available for p in providers)

        return MemoryStatus(
            backend=self.config.backend,
            storage_path=self.config.storage_path if self.config.backend == "sqlite" else None,
            total_files=storage_stats.get('total_files', 0),
            total_chunks=storage_stats.get('total_chunks', 0),
            total_embeddings=storage_stats.get('total_embeddings', 0),
            storage_size_mb=storage_stats.get('storage_size_mb', 0.0),
            embedding_providers=providers,
            cache_size=storage_stats.get('cache_size', 0),
            last_sync=self.last_sync,
            is_healthy=storage_healthy and embedding_healthy
        )