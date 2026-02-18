"""
Memory System for Leader-Toolbox

A comprehensive memory system that provides persistent storage, semantic search,
and multi-provider embedding support while integrating with the existing
FastAPI architecture.
"""

from .manager import MemoryManager
from .config import MemoryConfig, load_memory_config
from .models import (
    SearchResult,
    MemorySearchRequest,
    MemorySearchResponse,
    FileIngestRequest,
    TextIngestRequest,
    IngestResponse,
    MemoryStatus,
    SyncStats
)

__version__ = "0.1.0"

__all__ = [
    "MemoryManager",
    "MemoryConfig",
    "load_memory_config",
    "SearchResult",
    "MemorySearchRequest",
    "MemorySearchResponse",
    "FileIngestRequest",
    "TextIngestRequest",
    "IngestResponse",
    "MemoryStatus",
    "SyncStats"
]