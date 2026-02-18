"""
Pydantic models for the Memory system API.

Follows the existing FastAPI patterns in the leader-toolbox.
"""

from typing import Dict, List, Literal, Optional, Any, Union
from pydantic import BaseModel, Field, validator
from datetime import datetime
import uuid

class SearchOptions(BaseModel):
    """Search options for memory queries."""
    mode: Literal["vector", "keyword", "hybrid"] = "hybrid"
    max_results: int = Field(default=10, ge=1, le=100)
    min_score: float = Field(default=0.3, ge=0.0, le=1.0)
    sources: Optional[List[str]] = None
    vector_weight: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    keyword_weight: Optional[float] = Field(default=None, ge=0.0, le=1.0)

    @validator('keyword_weight')
    def validate_weights_sum(cls, v, values):
        if v is not None and 'vector_weight' in values and values['vector_weight'] is not None:
            if abs((v + values['vector_weight']) - 1.0) > 0.001:
                raise ValueError('Vector weight and keyword weight must sum to 1.0')
        return v

class SearchResult(BaseModel):
    """Individual search result."""
    file_id: str
    file_path: str
    text: str
    score: float = Field(ge=0.0, le=1.0)
    start_char: int = Field(ge=0)
    end_char: int = Field(ge=0)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    excerpt: Optional[str] = None  # Short preview text

    @validator('end_char')
    def validate_char_range(cls, v, values):
        start_char = values.get('start_char', 0)
        if v < start_char:
            raise ValueError('end_char must be >= start_char')
        return v

    def __post_init__(self):
        # Generate excerpt if not provided
        if self.excerpt is None:
            self.excerpt = self.text[:200] + "..." if len(self.text) > 200 else self.text

class Range(BaseModel):
    """Character or line range specification."""
    start: int = Field(ge=0)
    end: Optional[int] = Field(default=None, ge=0)

    @validator('end')
    def validate_range(cls, v, values):
        if v is not None and values.get('start', 0) > v:
            raise ValueError('End must be >= start')
        return v

# Request Models

class MemorySearchRequest(BaseModel):
    """Request for memory search operation."""
    query: str = Field(..., min_length=1, max_length=1000)
    options: Optional[SearchOptions] = None
    session_id: Optional[str] = None
    user_id: Optional[str] = None

class TextIngestRequest(BaseModel):
    """Request for text ingestion."""
    text: str = Field(..., min_length=1)
    metadata: Optional[Dict[str, Any]] = None
    source_id: Optional[str] = None
    title: Optional[str] = None

    @validator('source_id', pre=True, always=True)
    def generate_source_id(cls, v):
        return v or str(uuid.uuid4())

class FileIngestRequest(BaseModel):
    """Request for file ingestion."""
    file_path: str = Field(..., min_length=1)
    metadata: Optional[Dict[str, Any]] = None
    force_refresh: bool = False

class FileContentRequest(BaseModel):
    """Request for file content retrieval."""
    file_id: str
    lines: Optional[Range] = None
    include_metadata: bool = False

class SyncRequest(BaseModel):
    """Request for file synchronization."""
    paths: Optional[List[str]] = None
    force: bool = False
    include_stats: bool = True

# Response Models

class MemorySearchResponse(BaseModel):
    """Response from memory search operation."""
    results: List[SearchResult]
    query: str
    total_results: int = Field(ge=0)
    search_time_ms: float = Field(ge=0.0)
    mode_used: str
    has_more: bool = False

class IngestResponse(BaseModel):
    """Response from ingestion operations."""
    file_id: str
    chunks_created: int = Field(ge=0)
    embeddings_generated: int = Field(ge=0)
    processing_time_ms: float = Field(ge=0.0)
    success: bool = True
    message: Optional[str] = None

class FileContentResponse(BaseModel):
    """Response for file content retrieval."""
    file_id: str
    file_path: str
    content: str
    metadata: Optional[Dict[str, Any]] = None
    char_range: Range
    total_chars: int = Field(ge=0)

class SyncStats(BaseModel):
    """Statistics from synchronization operation."""
    files_processed: int = Field(default=0, ge=0)
    files_added: int = Field(default=0, ge=0)
    files_updated: int = Field(default=0, ge=0)
    files_deleted: int = Field(default=0, ge=0)
    chunks_created: int = Field(default=0, ge=0)
    embeddings_generated: int = Field(default=0, ge=0)
    processing_time_ms: float = Field(default=0.0, ge=0.0)
    errors: List[str] = Field(default_factory=list)

class ProviderStatus(BaseModel):
    """Status of an embedding provider."""
    name: str
    model: str
    available: bool
    dimensions: Optional[int] = None
    error: Optional[str] = None

class MemoryStatus(BaseModel):
    """Overall memory system status."""
    backend: str
    storage_path: Optional[str] = None
    total_files: int = Field(ge=0)
    total_chunks: int = Field(ge=0)
    total_embeddings: int = Field(ge=0)
    storage_size_mb: float = Field(ge=0.0)
    embedding_providers: List[ProviderStatus]
    cache_size: int = Field(ge=0)
    last_sync: Optional[datetime] = None
    is_healthy: bool = True

class SyncResponse(BaseModel):
    """Response from synchronization operation."""
    stats: SyncStats
    success: bool
    message: Optional[str] = None

# Legacy compatibility models (extend existing)

class ChatRequest(BaseModel):
    """Extended version of existing ChatRequest with memory support."""
    session_id: str
    user_id: str
    message: str
    use_memory: bool = True
    memory_options: Optional[SearchOptions] = None

class ChatResponse(BaseModel):
    """Extended version of existing ChatResponse with memory citations."""
    text: str
    citations: List[str] = Field(default_factory=list)
    used_kb_ids: List[str] = Field(default_factory=list)
    kb_version: str = "1.0"

    # New memory fields
    memory_results: List[SearchResult] = Field(default_factory=list)
    memory_query: Optional[str] = None
    search_time_ms: Optional[float] = None

# Internal models

class FileInfo(BaseModel):
    """Internal file information model."""
    id: str
    path: str
    hash: str
    size: int
    mtime: float
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime

class ChunkInfo(BaseModel):
    """Internal chunk information model."""
    id: str
    file_id: str
    text: str
    start_char: int
    end_char: int
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime

class EmbeddingCacheEntry(BaseModel):
    """Embedding cache entry model."""
    hash: str
    provider: str
    model: str
    embedding: List[float]
    created_at: datetime