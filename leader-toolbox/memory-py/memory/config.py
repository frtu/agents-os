"""
Configuration system for the Memory module.

Extends the existing constitution-driven configuration approach.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Literal, Optional, Any
from pydantic import BaseModel, Field, validator
import logging

logger = logging.getLogger(__name__)

class EmbeddingConfig(BaseModel):
    """Embedding provider configuration."""
    provider: Literal["sentence_transformers", "openai", "gemini", "voyage", "auto"] = "sentence_transformers"
    model: str = "all-MiniLM-L6-v2"
    fallback_provider: str = "sentence_transformers"
    cache_embeddings: bool = True
    batch_size: int = 32

    # Provider-specific configs
    openai: Dict[str, Any] = Field(default_factory=lambda: {
        "model": "text-embedding-3-small",
        "api_key": None,
        "base_url": None
    })
    gemini: Dict[str, Any] = Field(default_factory=lambda: {
        "model": "gemini-embedding-001",
        "api_key": None
    })
    voyage: Dict[str, Any] = Field(default_factory=lambda: {
        "model": "voyage-4-large",
        "api_key": None
    })

class SearchConfig(BaseModel):
    """Search configuration."""
    max_results: int = 10
    min_score: float = 0.3
    hybrid_enabled: bool = True
    vector_weight: float = 0.7
    keyword_weight: float = 0.3

    @validator('vector_weight', 'keyword_weight')
    def validate_weights(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError('Weights must be between 0.0 and 1.0')
        return v

class ChunkingConfig(BaseModel):
    """Text chunking configuration."""
    chunk_size_chars: int = 1000
    chunk_overlap_chars: int = 200
    preserve_structure: bool = True

    @validator('chunk_overlap_chars')
    def validate_overlap(cls, v, values):
        chunk_size = values.get('chunk_size_chars', 1000)
        if v >= chunk_size:
            raise ValueError('Overlap must be less than chunk size')
        return v

class FileConfig(BaseModel):
    """File processing configuration."""
    watch_directories: List[str] = Field(default_factory=lambda: ["./memory", "./docs"])
    file_patterns: List[str] = Field(default_factory=lambda: ["*.md", "*.txt", "*.py"])
    auto_sync: bool = True
    sync_interval_seconds: int = 300
    max_file_size_mb: int = 10

class MemoryConfig(BaseModel):
    """Main memory system configuration."""
    backend: Literal["memory", "sqlite"] = "sqlite"
    storage_path: str = "./data/memory.db"

    embeddings: EmbeddingConfig = Field(default_factory=EmbeddingConfig)
    search: SearchConfig = Field(default_factory=SearchConfig)
    chunking: ChunkingConfig = Field(default_factory=ChunkingConfig)
    files: FileConfig = Field(default_factory=FileConfig)

    # Legacy compatibility
    session_retention_hours: int = 24
    long_term_opt_in: bool = True

    @validator('storage_path')
    def validate_storage_path(cls, v):
        # Ensure directory exists for SQLite path
        if v and v != ":memory:":
            Path(v).parent.mkdir(parents=True, exist_ok=True)
        return v

def load_memory_config(config_path: Optional[str] = None) -> MemoryConfig:
    """
    Load memory configuration from constitution config or default.

    Args:
        config_path: Path to constitution config file. If None, uses default location.

    Returns:
        MemoryConfig instance
    """
    if config_path is None:
        # Default path following existing pattern
        config_path = ".specify/memory/constitution_config.json"

    try:
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config_data = json.load(f)

            # Extract memory config from constitution
            memory_data = config_data.get('memory', {})

            # Handle legacy embedding config format
            if 'embeddings' in config_data:
                legacy_embeddings = config_data['embeddings']
                if 'embeddings' not in memory_data:
                    memory_data['embeddings'] = {}
                memory_data['embeddings'].update(legacy_embeddings)

            # Handle legacy chunking config
            if 'chunking' in config_data:
                legacy_chunking = config_data['chunking']
                if 'chunking' not in memory_data:
                    memory_data['chunking'] = {}
                memory_data['chunking'].update(legacy_chunking)

            # Handle legacy retrieval config
            if 'retrieval' in config_data:
                legacy_retrieval = config_data['retrieval']
                if 'search' not in memory_data:
                    memory_data['search'] = {}
                memory_data['search'].update({
                    'max_results': legacy_retrieval.get('top_k', 10),
                    'min_score': legacy_retrieval.get('similarity_threshold', 0.3)
                })

            logger.info(f"Loaded memory config from {config_path}")
            return MemoryConfig(**memory_data)

    except Exception as e:
        logger.warning(f"Failed to load config from {config_path}: {e}")

    logger.info("Using default memory configuration")
    return MemoryConfig()

def resolve_env_vars(config_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Resolve environment variable references in config values.

    Args:
        config_dict: Configuration dictionary

    Returns:
        Configuration with resolved environment variables
    """
    def resolve_value(value):
        if isinstance(value, str) and value.startswith('${') and value.endswith('}'):
            env_var = value[2:-1]
            return os.getenv(env_var)
        elif isinstance(value, dict):
            return {k: resolve_value(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [resolve_value(v) for v in value]
        return value

    return {k: resolve_value(v) for k, v in config_dict.items()}

def get_api_key(provider: str, config: MemoryConfig) -> Optional[str]:
    """
    Get API key for a specific provider.

    Args:
        provider: Provider name (openai, gemini, voyage)
        config: Memory configuration

    Returns:
        API key if available
    """
    provider_config = getattr(config.embeddings, provider, {})
    if isinstance(provider_config, dict):
        api_key = provider_config.get('api_key')
    else:
        api_key = getattr(provider_config, 'api_key', None)

    if api_key:
        return api_key

    # Fallback to environment variables
    env_vars = {
        'openai': 'OPENAI_API_KEY',
        'gemini': 'GOOGLE_API_KEY',
        'voyage': 'VOYAGE_API_KEY'
    }

    env_var = env_vars.get(provider)
    if env_var:
        return os.getenv(env_var)

    return None