"""
File processing for the memory system.
"""

import os
import hashlib
import mimetypes
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
import uuid

from ..models import FileInfo, ChunkInfo
from .chunker import TextChunker, MarkdownChunker, TextChunk

logger = logging.getLogger(__name__)

class FileProcessor:
    """
    Processes files for ingestion into the memory system.
    """

    def __init__(
        self,
        chunk_size_chars: int = 1000,
        chunk_overlap_chars: int = 200,
        max_file_size_mb: int = 10,
        supported_extensions: Optional[List[str]] = None
    ):
        """
        Initialize file processor.

        Args:
            chunk_size_chars: Target chunk size in characters
            chunk_overlap_chars: Overlap between chunks
            max_file_size_mb: Maximum file size to process
            supported_extensions: List of supported file extensions
        """
        self.chunk_size = chunk_size_chars
        self.overlap = chunk_overlap_chars
        self.max_file_size = max_file_size_mb * 1024 * 1024

        self.supported_extensions = supported_extensions or [
            '.md', '.txt', '.py', '.js', '.ts', '.html', '.css',
            '.json', '.yaml', '.yml', '.xml', '.rst', '.org'
        ]

        # Initialize chunkers
        self.text_chunker = TextChunker(chunk_size_chars, chunk_overlap_chars)
        self.markdown_chunker = MarkdownChunker(
            chunk_size_chars=chunk_size_chars,
            chunk_overlap_chars=chunk_overlap_chars
        )

    async def process_file(self, file_path: Union[str, Path], metadata: Optional[Dict[str, Any]] = None) -> tuple[FileInfo, List[ChunkInfo]]:
        """
        Process a file and create file info and chunks.

        Args:
            file_path: Path to the file
            metadata: Optional metadata

        Returns:
            Tuple of (FileInfo, List[ChunkInfo])
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        if not file_path.is_file():
            raise ValueError(f"Not a file: {file_path}")

        # Check file size
        file_size = file_path.stat().st_size
        if file_size > self.max_file_size:
            raise ValueError(f"File too large: {file_size / (1024*1024):.1f}MB > {self.max_file_size / (1024*1024):.1f}MB")

        # Check if file type is supported
        if not self._is_supported_file(file_path):
            raise ValueError(f"Unsupported file type: {file_path.suffix}")

        logger.info(f"Processing file: {file_path}")

        try:
            # Read file content
            content = self._read_file(file_path)

            # Create file info
            file_info = self._create_file_info(file_path, content, metadata)

            # Create chunks
            chunks = await self._create_chunks(file_info, content)

            logger.info(f"Processed file {file_path}: {len(chunks)} chunks created")
            return file_info, chunks

        except Exception as e:
            logger.error(f"Failed to process file {file_path}: {e}")
            raise

    async def process_text(
        self,
        text: str,
        source_id: Optional[str] = None,
        title: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> tuple[FileInfo, List[ChunkInfo]]:
        """
        Process raw text and create file info and chunks.

        Args:
            text: Text content
            source_id: Optional source identifier
            title: Optional title
            metadata: Optional metadata

        Returns:
            Tuple of (FileInfo, List[ChunkInfo])
        """
        # Create file info for text
        file_id = source_id or str(uuid.uuid4())
        file_path = title or f"text_{file_id}"

        file_info = FileInfo(
            id=file_id,
            path=file_path,
            hash=hashlib.md5(text.encode()).hexdigest(),
            size=len(text),
            mtime=datetime.now().timestamp(),
            metadata={
                'type': 'text',
                'title': title,
                **(metadata or {})
            },
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        # Create chunks
        chunks = await self._create_chunks(file_info, text)

        logger.info(f"Processed text: {len(chunks)} chunks created")
        return file_info, chunks

    def _is_supported_file(self, file_path: Path) -> bool:
        """Check if file type is supported."""
        return file_path.suffix.lower() in self.supported_extensions

    def _read_file(self, file_path: Path) -> str:
        """Read file content as text."""
        # Try different encodings
        encodings = ['utf-8', 'utf-16', 'latin1', 'cp1252']

        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    content = f.read()
                logger.debug(f"Read file {file_path} with encoding {encoding}")
                return content
            except UnicodeDecodeError:
                continue

        raise ValueError(f"Could not decode file {file_path} with any supported encoding")

    def _create_file_info(self, file_path: Path, content: str, metadata: Optional[Dict[str, Any]]) -> FileInfo:
        """Create FileInfo object."""
        stat = file_path.stat()

        file_metadata = {
            'extension': file_path.suffix,
            'mime_type': mimetypes.guess_type(str(file_path))[0],
            'encoding': 'utf-8',  # Assume UTF-8 since we successfully read it
            **(metadata or {})
        }

        return FileInfo(
            id=str(uuid.uuid4()),
            path=str(file_path),
            hash=hashlib.md5(content.encode()).hexdigest(),
            size=len(content),
            mtime=stat.st_mtime,
            metadata=file_metadata,
            created_at=datetime.fromtimestamp(stat.st_ctime),
            updated_at=datetime.fromtimestamp(stat.st_mtime)
        )

    async def _create_chunks(self, file_info: FileInfo, content: str) -> List[ChunkInfo]:
        """Create chunks from file content."""
        # Choose appropriate chunker based on file type
        if file_info.path.endswith('.md'):
            chunker = self.markdown_chunker
        else:
            chunker = self.text_chunker

        # Create chunk metadata
        chunk_metadata = {
            'file_type': file_info.metadata.get('extension', ''),
            'mime_type': file_info.metadata.get('mime_type', ''),
            'source_file': file_info.path
        }

        # Generate text chunks
        text_chunks = chunker.chunk_text(content, chunk_metadata)

        # Convert to ChunkInfo objects
        chunk_infos = []
        for i, text_chunk in enumerate(text_chunks):
            chunk_info = ChunkInfo(
                id=str(uuid.uuid4()),
                file_id=file_info.id,
                text=text_chunk.text,
                start_char=text_chunk.start_char,
                end_char=text_chunk.end_char,
                metadata={
                    'chunk_index': i,
                    'chunk_hash': text_chunk.compute_hash(),
                    **text_chunk.metadata
                },
                created_at=datetime.now()
            )
            chunk_infos.append(chunk_info)

        return chunk_infos

    async def process_directory(
        self,
        directory_path: Union[str, Path],
        patterns: Optional[List[str]] = None,
        recursive: bool = True,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[tuple[FileInfo, List[ChunkInfo]]]:
        """
        Process all supported files in a directory.

        Args:
            directory_path: Path to directory
            patterns: File patterns to match (e.g., ['*.md', '*.txt'])
            recursive: Whether to search subdirectories
            metadata: Optional metadata for all files

        Returns:
            List of (FileInfo, ChunkInfos) tuples
        """
        directory_path = Path(directory_path)

        if not directory_path.exists():
            raise FileNotFoundError(f"Directory not found: {directory_path}")

        if not directory_path.is_dir():
            raise ValueError(f"Not a directory: {directory_path}")

        logger.info(f"Processing directory: {directory_path}")

        results = []
        patterns = patterns or ['*']

        try:
            # Find matching files
            files = []
            for pattern in patterns:
                if recursive:
                    files.extend(directory_path.rglob(pattern))
                else:
                    files.extend(directory_path.glob(pattern))

            # Filter for supported files
            supported_files = [f for f in files if f.is_file() and self._is_supported_file(f)]

            logger.info(f"Found {len(supported_files)} supported files in {directory_path}")

            # Process each file
            for file_path in supported_files:
                try:
                    file_metadata = {
                        'directory': str(directory_path),
                        'relative_path': str(file_path.relative_to(directory_path)),
                        **(metadata or {})
                    }

                    file_info, chunks = await self.process_file(file_path, file_metadata)
                    results.append((file_info, chunks))

                except Exception as e:
                    logger.warning(f"Failed to process file {file_path}: {e}")
                    continue

            logger.info(f"Successfully processed {len(results)} files from {directory_path}")
            return results

        except Exception as e:
            logger.error(f"Failed to process directory {directory_path}: {e}")
            raise

    def get_file_hash(self, file_path: Union[str, Path]) -> str:
        """
        Get file hash without reading full content.

        Args:
            file_path: Path to file

        Returns:
            File hash
        """
        file_path = Path(file_path)
        stat = file_path.stat()

        # Hash based on file path, size, and modification time
        hash_input = f"{file_path}:{stat.st_size}:{stat.st_mtime}"
        return hashlib.md5(hash_input.encode()).hexdigest()

    def is_file_changed(self, file_path: Union[str, Path], stored_hash: str, stored_mtime: float) -> bool:
        """
        Check if file has changed since last processing.

        Args:
            file_path: Path to file
            stored_hash: Previously stored hash
            stored_mtime: Previously stored modification time

        Returns:
            True if file has changed
        """
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                return True

            stat = file_path.stat()

            # Quick check: modification time
            if abs(stat.st_mtime - stored_mtime) > 1:  # 1 second tolerance
                return True

            # Detailed check: hash
            current_hash = self.get_file_hash(file_path)
            return current_hash != stored_hash

        except Exception:
            # If we can't check, assume it changed
            return True