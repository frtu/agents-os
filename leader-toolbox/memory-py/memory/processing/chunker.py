"""
Text chunking functionality that extends the existing leader-toolbox chunker.
"""

import re
import hashlib
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class TextChunk:
    """Represents a chunk of text."""
    text: str
    start_char: int
    end_char: int
    start_line: Optional[int] = None
    end_line: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

    @property
    def length(self) -> int:
        """Length of the chunk in characters."""
        return len(self.text)

    def compute_hash(self) -> str:
        """Compute hash of the chunk text."""
        return hashlib.sha256(self.text.encode()).hexdigest()

class TextChunker:
    """
    Text chunking with overlap support.

    Extends the existing chunk_text functionality from the leader-toolbox.
    """

    def __init__(
        self,
        chunk_size_chars: int = 1000,
        chunk_overlap_chars: int = 200,
        preserve_structure: bool = True
    ):
        """
        Initialize text chunker.

        Args:
            chunk_size_chars: Target chunk size in characters
            chunk_overlap_chars: Overlap between chunks in characters
            preserve_structure: Whether to try to preserve structure (paragraphs, etc.)
        """
        self.chunk_size = chunk_size_chars
        self.overlap = chunk_overlap_chars
        self.preserve_structure = preserve_structure

        if self.overlap >= self.chunk_size:
            raise ValueError("Overlap must be less than chunk size")

    def chunk_text(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> List[TextChunk]:
        """
        Chunk text into overlapping segments.

        Args:
            text: Text to chunk
            metadata: Optional metadata for chunks

        Returns:
            List of text chunks
        """
        if not text.strip():
            return []

        # Use existing chunk_text function if available for compatibility
        try:
            from backend.fastapi_chat import chunk_text as existing_chunk_text

            # Get chunks using existing function
            existing_chunks = existing_chunk_text(text, self.chunk_size, self.overlap)

            # Convert to our TextChunk format
            chunks = []
            current_pos = 0

            for i, chunk_text in enumerate(existing_chunks):
                # Find the position of this chunk in the original text
                start_pos = text.find(chunk_text, current_pos)
                if start_pos == -1:
                    # Fallback: estimate position
                    start_pos = current_pos

                end_pos = start_pos + len(chunk_text)

                chunk = TextChunk(
                    text=chunk_text,
                    start_char=start_pos,
                    end_char=end_pos,
                    metadata=metadata.copy() if metadata else {}
                )

                chunks.append(chunk)
                current_pos = start_pos + len(chunk_text) - self.overlap

            return chunks

        except ImportError:
            # Fallback to our own implementation
            return self._chunk_text_internal(text, metadata)

    def _chunk_text_internal(self, text: str, metadata: Optional[Dict[str, Any]]) -> List[TextChunk]:
        """Internal chunking implementation."""
        chunks = []

        if self.preserve_structure:
            # Try to split on natural boundaries
            chunks = self._chunk_with_structure(text, metadata)

        if not chunks:
            # Fall back to simple sliding window
            chunks = self._chunk_sliding_window(text, metadata)

        return chunks

    def _chunk_with_structure(self, text: str, metadata: Optional[Dict[str, Any]]) -> List[TextChunk]:
        """Chunk text while preserving structure."""
        chunks = []

        # Split into paragraphs first
        paragraphs = re.split(r'\n\s*\n', text)

        current_chunk = ""
        current_start = 0
        text_pos = 0

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            # Find position of this paragraph in original text
            para_start = text.find(para, text_pos)
            if para_start == -1:
                para_start = text_pos
            text_pos = para_start + len(para)

            # Check if adding this paragraph would exceed chunk size
            if len(current_chunk) + len(para) + 2 > self.chunk_size and current_chunk:
                # Create chunk from current content
                chunk_end = current_start + len(current_chunk)
                chunk = TextChunk(
                    text=current_chunk.strip(),
                    start_char=current_start,
                    end_char=chunk_end,
                    metadata=metadata.copy() if metadata else {}
                )
                chunks.append(chunk)

                # Start new chunk with overlap
                overlap_text = self._get_overlap_text(current_chunk)
                overlap_start = max(0, chunk_end - len(overlap_text))

                current_chunk = overlap_text + "\n\n" + para
                current_start = overlap_start
            else:
                # Add paragraph to current chunk
                if current_chunk:
                    current_chunk += "\n\n" + para
                else:
                    current_chunk = para
                    current_start = para_start

        # Add final chunk
        if current_chunk.strip():
            chunk = TextChunk(
                text=current_chunk.strip(),
                start_char=current_start,
                end_char=current_start + len(current_chunk),
                metadata=metadata.copy() if metadata else {}
            )
            chunks.append(chunk)

        return chunks

    def _chunk_sliding_window(self, text: str, metadata: Optional[Dict[str, Any]]) -> List[TextChunk]:
        """Simple sliding window chunking."""
        chunks = []

        for i in range(0, len(text), self.chunk_size - self.overlap):
            end = min(i + self.chunk_size, len(text))
            chunk_text = text[i:end]

            # Try to end at word boundary if possible
            if end < len(text) and not text[end].isspace():
                # Look for previous space within reasonable distance
                for j in range(min(50, len(chunk_text))):
                    if chunk_text[-(j+1)].isspace():
                        chunk_text = chunk_text[:-(j+1)]
                        end = i + len(chunk_text)
                        break

            if chunk_text.strip():
                chunk = TextChunk(
                    text=chunk_text.strip(),
                    start_char=i,
                    end_char=end,
                    metadata=metadata.copy() if metadata else {}
                )
                chunks.append(chunk)

        return chunks

    def _get_overlap_text(self, text: str) -> str:
        """Get overlap text from the end of a chunk."""
        if len(text) <= self.overlap:
            return text

        overlap_text = text[-self.overlap:]

        # Try to start at word boundary
        space_pos = overlap_text.find(' ')
        if space_pos > 0:
            overlap_text = overlap_text[space_pos + 1:]

        return overlap_text

class MarkdownChunker(TextChunker):
    """
    Specialized chunker for Markdown files that respects document structure.
    """

    def __init__(self, **kwargs):
        """Initialize markdown chunker."""
        super().__init__(**kwargs)

    def chunk_text(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> List[TextChunk]:
        """
        Chunk markdown text while respecting structure.

        Args:
            text: Markdown text to chunk
            metadata: Optional metadata for chunks

        Returns:
            List of text chunks
        """
        # Parse markdown structure
        sections = self._parse_markdown_sections(text)

        chunks = []
        current_chunk = ""
        current_start = 0

        for section in sections:
            section_text = section['text']

            # Check if adding this section would exceed chunk size
            if len(current_chunk) + len(section_text) > self.chunk_size and current_chunk:
                # Create chunk from current content
                chunk = TextChunk(
                    text=current_chunk.strip(),
                    start_char=current_start,
                    end_char=current_start + len(current_chunk),
                    metadata={
                        **(metadata or {}),
                        'section_level': section.get('level', 0),
                        'section_title': section.get('title', ''),
                        'chunk_type': 'markdown'
                    }
                )
                chunks.append(chunk)

                # Start new chunk with overlap if the section is large
                if len(section_text) > self.chunk_size:
                    # Split large section
                    section_chunks = self._chunk_large_section(section, metadata)
                    chunks.extend(section_chunks)
                    current_chunk = ""
                    current_start = section['end']
                else:
                    # Start new chunk with this section
                    overlap_text = self._get_overlap_text(current_chunk)
                    current_chunk = overlap_text + "\n\n" + section_text
                    current_start = max(0, section['start'] - len(overlap_text))
            else:
                # Add section to current chunk
                if current_chunk:
                    current_chunk += "\n\n" + section_text
                else:
                    current_chunk = section_text
                    current_start = section['start']

        # Add final chunk
        if current_chunk.strip():
            chunk = TextChunk(
                text=current_chunk.strip(),
                start_char=current_start,
                end_char=current_start + len(current_chunk),
                metadata=metadata.copy() if metadata else {}
            )
            chunks.append(chunk)

        return chunks

    def _parse_markdown_sections(self, text: str) -> List[Dict[str, Any]]:
        """Parse markdown into sections."""
        sections = []
        lines = text.split('\n')

        current_section = []
        current_title = ""
        current_level = 0
        section_start = 0
        char_pos = 0

        for i, line in enumerate(lines):
            line_start = char_pos
            char_pos += len(line) + 1  # +1 for newline

            # Check for heading
            heading_match = re.match(r'^(#{1,6})\s+(.+)$', line)

            if heading_match and current_section:
                # End current section
                section_text = '\n'.join(current_section)
                if section_text.strip():
                    sections.append({
                        'text': section_text,
                        'title': current_title,
                        'level': current_level,
                        'start': section_start,
                        'end': line_start - 1
                    })

                # Start new section
                current_section = [line]
                current_title = heading_match.group(2)
                current_level = len(heading_match.group(1))
                section_start = line_start
            else:
                current_section.append(line)
                if not current_title and current_section == [line]:
                    section_start = line_start

        # Add final section
        if current_section:
            section_text = '\n'.join(current_section)
            if section_text.strip():
                sections.append({
                    'text': section_text,
                    'title': current_title,
                    'level': current_level,
                    'start': section_start,
                    'end': char_pos - 1
                })

        return sections

    def _chunk_large_section(self, section: Dict[str, Any], metadata: Optional[Dict[str, Any]]) -> List[TextChunk]:
        """Chunk a large section that exceeds chunk size."""
        # Use standard chunking for the section content
        section_chunks = self._chunk_sliding_window(section['text'], metadata)

        # Add section metadata to each chunk
        for chunk in section_chunks:
            chunk.metadata.update({
                'section_level': section.get('level', 0),
                'section_title': section.get('title', ''),
                'chunk_type': 'markdown',
                'is_large_section': True
            })
            # Adjust positions relative to full document
            chunk.start_char += section['start']
            chunk.end_char += section['start']

        return section_chunks