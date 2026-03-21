"""Configuration management for RagHubMCP.

This module provides unified configuration using Pydantic models,
YAML loading, and dependency injection support.

Design:
- Single source of truth for config models (Pydantic)
- YAML-based configuration file
- Dependency injection for testability
- Validation for security and correctness
"""

from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path
from typing import Any, Optional

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


# =============================================================================
# Configuration Models (Pydantic - Single Source of Truth)
# =============================================================================


class ServerConfig(BaseModel):
    """Server configuration."""

    host: str = Field(default="0.0.0.0", description="Server host address")
    port: int = Field(default=8818, ge=1, le=65535, description="Server port (1-65535)")
    debug: bool = Field(default=True, description="Enable debug mode")

    @field_validator('port')
    @classmethod
    def validate_port(cls, v: int) -> int:
        """Validate port is in valid range."""
        if v < 1 or v > 65535:
            raise ValueError(f"Port must be between 1 and 65535, got {v}")
        return v


class ChromaConfig(BaseModel):
    """Chroma vector database configuration."""

    persist_dir: Optional[str] = Field(default="./data/chroma", description="Persistence directory")
    host: Optional[str] = Field(default=None, description="Remote host (None for local)")
    port: Optional[int] = Field(default=None, description="Remote port (None for local)")

    @model_validator(mode='after')
    def validate_mode(self) -> 'ChromaConfig':
        """Validate that either persist_dir or host/port is set, not both."""
        if self.host is not None and self.persist_dir not in (None, "./data/chroma"):
            # Both host and persist_dir set - prefer remote mode
            # Clear persist_dir to avoid confusion
            self.persist_dir = None
        return self

    @field_validator('port')
    @classmethod
    def validate_remote_port(cls, v: Optional[int]) -> Optional[int]:
        """Validate remote port if set."""
        if v is not None and (v < 1 or v > 65535):
            raise ValueError(f"Remote port must be between 1 and 65535, got {v}")
        return v


class ProviderInstance(BaseModel):
    """Provider instance configuration."""

    name: str = Field(..., description="Unique identifier")
    type: str = Field(..., description="Provider type (e.g., ollama, openai)")
    model: str = Field(..., description="Model name")
    base_url: Optional[str] = Field(default=None, description="API base URL")
    dimension: Optional[int] = Field(default=None, ge=1, description="Embedding dimension")


class ProviderCategory(BaseModel):
    """Configuration for a category of providers."""

    default: str = Field(default="", description="Default provider name")
    instances: list[dict[str, Any]] = Field(default_factory=list, description="Provider instances")

    @model_validator(mode='after')
    def validate_default_exists(self) -> 'ProviderCategory':
        """Validate that default provider exists in instances if specified."""
        if self.default and self.instances:
            instance_names = [inst.get("name") for inst in self.instances if isinstance(inst, dict)]
            if self.default not in instance_names:
                raise ValueError(f"Default provider '{self.default}' not found in instances: {instance_names}")
        return self


class ProvidersConfig(BaseModel):
    """All provider configurations."""

    embedding: ProviderCategory = Field(default_factory=ProviderCategory)
    rerank: ProviderCategory = Field(default_factory=ProviderCategory)
    llm: ProviderCategory = Field(default_factory=ProviderCategory)
    vectorstore: ProviderCategory = Field(default_factory=ProviderCategory)


class IndexerConfig(BaseModel):
    """File indexer configuration."""

    chunk_size: int = Field(default=500, ge=50, le=10000, description="Max characters per chunk (50-10000)")
    chunk_overlap: int = Field(default=50, ge=0, le=5000, description="Overlap between chunks (0-5000)")
    max_file_size: int = Field(default=1048576, ge=1, le=104857600, description="Max file size in bytes (1-100MB)")
    file_types: list[str] = Field(
        default_factory=lambda: [".py", ".ts", ".js", ".md", ".vue"],
        description="File extensions to index"
    )
    exclude_dirs: list[str] = Field(
        default_factory=lambda: ["node_modules", ".git", "__pycache__", "venv", ".venv", "dist", "build"],
        description="Directories to exclude"
    )
    allowed_roots: list[str] = Field(
        default_factory=list,
        description="Allowed root directories for indexing. Empty list allows all paths (not recommended for production)."
    )

    @field_validator('file_types')
    @classmethod
    def validate_file_types(cls, v: list[str]) -> list[str]:
        """Validate file type extensions."""
        for ext in v:
            if not ext.startswith('.'):
                raise ValueError(f"File type '{ext}' must start with '.'")
        return v

    @model_validator(mode='after')
    def validate_overlap(self) -> 'IndexerConfig':
        """Validate that overlap is less than chunk_size."""
        if self.chunk_overlap >= self.chunk_size:
            raise ValueError(f"chunk_overlap ({self.chunk_overlap}) must be less than chunk_size ({self.chunk_size})")
        return self


class WatcherConfig(BaseModel):
    """File watcher configuration."""

    enabled: bool = Field(default=True, description="Enable file watcher")
    debounce_seconds: float = Field(default=1.0, description="Debounce delay")


class HybridConfig(BaseModel):
    """Hybrid search configuration."""

    alpha: float = Field(default=0.5, ge=0.0, le=1.0, description="Vector search weight (0.0-1.0)")
    beta: float = Field(default=0.5, ge=0.0, le=1.0, description="BM25 search weight (0.0-1.0)")
    rrf_k: int = Field(default=60, ge=1, le=1000, description="RRF constant (1-1000)")
    bm25_persist_dir: str = Field(default="./data/bm25", description="BM25 index directory")

    @model_validator(mode='after')
    def validate_weights(self) -> 'HybridConfig':
        """Validate that alpha + beta roughly sum to 1.0 for expected behavior."""
        # Allow some flexibility, but warn if weights are unusual
        total = self.alpha + self.beta
        if total < 0.1 or total > 1.9:
            raise ValueError(f"alpha + beta should roughly sum to 1.0, got {total}")
        return self


class LoggingConfig(BaseModel):
    """Logging configuration."""

    level: str = Field(default="INFO", description="Log level")
    format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Log format string"
    )
    file: Optional[str] = Field(default=None, description="Log file path")


class CORSConfig(BaseModel):
    """CORS configuration for security.
    
    In production, restrict allowed origins to specific domains.
    """

    origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:3315", "http://127.0.0.1:3315"],
        description="Allowed CORS origins"
    )
    allow_credentials: bool = Field(default=True, description="Allow credentials")
    allow_methods: list[str] = Field(
        default_factory=lambda: ["*"],
        description="Allowed HTTP methods"
    )
    allow_headers: list[str] = Field(
        default_factory=lambda: ["*"],
        description="Allowed HTTP headers"
    )


class AppConfig(BaseModel):
    """Root configuration object.

    This is the single source of truth for all configuration.
    Used by both API and internal services.
    """

    model_config = ConfigDict(extra="ignore")  # Allow extra fields for forward compatibility

    server: ServerConfig = Field(default_factory=ServerConfig)
    chroma: ChromaConfig = Field(default_factory=ChromaConfig)
    providers: ProvidersConfig = Field(default_factory=ProvidersConfig)
    indexer: IndexerConfig = Field(default_factory=IndexerConfig)
    watcher: WatcherConfig = Field(default_factory=WatcherConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    hybrid: HybridConfig = Field(default_factory=HybridConfig)
    cors: CORSConfig = Field(default_factory=CORSConfig)


# =============================================================================
# MCP Tool Validation Constants
# =============================================================================

class MCPValidationConfig:
    """Validation constants for MCP tools.
    
    These constants define limits and constraints for MCP tool inputs,
    and can be overridden via configuration if needed.
    """
    
    # Collection name validation
    COLLECTION_NAME_PATTERN = re.compile(r'^[a-zA-Z0-9_-]+$')
    
    # Document limits
    MAX_DOCUMENTS = 1000  # Maximum documents per ingestion
    MAX_TEXT_LENGTH = 1000000  # 1MB max text per document
    MAX_METADATA_DEPTH = 3  # Maximum nesting depth for metadata
    
    # Chunk size limits
    MIN_CHUNK_SIZE = 50
    MAX_CHUNK_SIZE = 10000
    
    # Query limits
    DEFAULT_TOP_K = 5
    MAX_TOP_K = 100
    MIN_TOP_K = 1
    
    # Valid strategies
    VALID_STRATEGIES = frozenset(["fast", "balanced", "accurate"])
    DEFAULT_STRATEGY = "balanced"
    
    @classmethod
    def validate_collection_name(cls, name: str) -> bool:
        """Validate collection name format.
        
        Args:
            name: Collection name to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not name or not isinstance(name, str):
            return False
        return bool(cls.COLLECTION_NAME_PATTERN.match(name))
    
    @classmethod
    def validate_chunk_size(cls, size: int) -> bool:
        """Validate chunk size.
        
        Args:
            size: Chunk size to validate
            
        Returns:
            True if valid, False otherwise
        """
        return cls.MIN_CHUNK_SIZE <= size <= cls.MAX_CHUNK_SIZE
    
    @classmethod
    def validate_top_k(cls, top_k: int) -> bool:
        """Validate top_k value.
        
        Args:
            top_k: Top K value to validate
            
        Returns:
            True if valid, False otherwise
        """
        return cls.MIN_TOP_K <= top_k <= cls.MAX_TOP_K
    
    @classmethod
    def validate_non_empty_string(cls, value: Any, field_name: str) -> str | None:
        """Validate non-empty string.
        
        Args:
            value: Value to validate.
            field_name: Field name for error message.
            
        Returns:
            Error message if invalid, None if valid.
        
        Example:
            >>> validate_non_empty_string("", "query")
            'query must be a non-empty string'
            >>> validate_non_empty_string("valid", "query")
            None
        """
        if not value or not isinstance(value, str):
            return f"{field_name} must be a non-empty string"
        return None
    
    @classmethod
    def validate_query_string(cls, query: Any) -> str | None:
        """Validate query string.
        
        Args:
            query: Query string to validate.
            
        Returns:
            Error message if invalid, None if valid.
        """
        if not query or not isinstance(query, str):
            return "query must be a non-empty string"
        return None
    
    @classmethod
    def validate_text_field(cls, text: Any, field_name: str) -> str | None:
        """Validate text field.
        
        Args:
            text: Text value to validate.
            field_name: Field name for error message.
            
        Returns:
            Error message if invalid, None if valid.
        """
        if text is None or not isinstance(text, str):
            return f"{field_name} must be a string"
        if not text.strip():
            return f"{field_name} must not be empty"
        if len(text) > cls.MAX_TEXT_LENGTH:
            return f"{field_name} exceeds maximum length of {cls.MAX_TEXT_LENGTH} characters"
        return None
    
    @classmethod
    def validate_collection_name_strict(cls, name: Any) -> str | None:
        """Validate collection name strictly.
        
        Args:
            name: Collection name to validate.
            
        Returns:
            Error message if invalid, None if valid.
        """
        if not name or not isinstance(name, str):
            return "collection_name must be a non-empty string"
        
        name = name.strip()
        if not name:
            return "collection_name must not be empty or whitespace"
        
        if not cls.COLLECTION_NAME_PATTERN.match(name):
            return f"Invalid collection name '{name}'. Must contain only alphanumeric characters, underscores, or hyphens."
        
        if len(name) > 128:
            return f"Collection name too long. Maximum 128 characters, got {len(name)}."
        
        return None
    
    @classmethod
    def validate_documents_list(cls, documents: Any) -> str | None:
        """Validate documents list.
        
        Args:
            documents: Documents list to validate.
            
        Returns:
            Error message if invalid, None if valid.
        """
        if not documents or not isinstance(documents, list):
            return "documents must be a non-empty list"
        
        if len(documents) > cls.MAX_DOCUMENTS:
            return f"Too many documents. Maximum is {cls.MAX_DOCUMENTS}, got {len(documents)}"
        
        return None
    
    @classmethod
    def validate_int_range(cls, value: Any, field_name: str, min_val: int, max_val: int) -> str | None:
        """Validate integer is within range.
        
        Args:
            value: Value to validate.
            field_name: Field name for error message.
            min_val: Minimum allowed value.
            max_val: Maximum allowed value.
            
        Returns:
            Error message if invalid, None if valid.
        """
        if value is None:
            return f"{field_name} is required"
        
        if not isinstance(value, int) or isinstance(value, bool):
            return f"{field_name} must be an integer"
        
        if value < min_val or value > max_val:
            return f"{field_name} must be between {min_val} and {max_val}, got {value}"
        
        return None
    
    @classmethod
    def validate_metadata(cls, metadata: Any, max_depth: int | None = None) -> tuple[bool, str]:
        """Validate metadata structure recursively.
        
        Args:
            metadata: Metadata object to validate.
            max_depth: Maximum allowed nesting depth (uses class default if None).
            
        Returns:
            Tuple of (is_valid, error_message).
        """
        if max_depth is None:
            max_depth = cls.MAX_METADATA_DEPTH
        
        def _validate(obj: Any, depth: int = 0) -> tuple[bool, str]:
            """Internal recursive validation."""
            if depth > max_depth:
                return False, f"Metadata depth exceeds {max_depth}"
            
            if obj is None:
                return True, ""
            
            if isinstance(obj, (str, int, float, bool)):
                return True, ""
            
            if isinstance(obj, list):
                for i, item in enumerate(obj):
                    valid, msg = _validate(item, depth + 1)
                    if not valid:
                        return False, f"list[{i}]: {msg}"
                return True, ""
            
            if isinstance(obj, dict):
                for key, value in obj.items():
                    if not isinstance(key, str):
                        return False, f"Dict key must be string, got {type(key).__name__}"
                    valid, msg = _validate(value, depth + 1)
                    if not valid:
                        return False, f"{key}: {msg}"
                return True, ""
            
            return False, f"Unsupported type: {type(obj).__name__}"
        
        return _validate(metadata, 0)


# =============================================================================
# Pipeline Profile Configuration
# =============================================================================


class PipelineProfileConfig(BaseModel):
    """Pipeline profile configuration for retrieval and reranking.
    
    Defines parameters for different pipeline profiles (fast/balanced/accurate).
    """
    
    top_k: int = Field(default=5, ge=1, le=100, description="Number of final results to return")
    retrieval_multiplier: float = Field(default=2.0, ge=1.0, le=5.0, description="Multiplier for initial retrieval")
    alpha: float = Field(default=0.5, ge=0.0, le=1.0, description="Vector search weight in hybrid retrieval")
    beta: float = Field(default=0.5, ge=0.0, le=1.0, description="BM25 search weight in hybrid retrieval")
    rrf_k: int = Field(default=60, ge=1, le=1000, description="RRF constant for reciprocal rank fusion")
    rerank: bool = Field(default=True, description="Whether to enable reranking")


# =============================================================================
# Provider Defaults Configuration
# =============================================================================


class ProviderDefaultsConfig(BaseModel):
    """Default configuration values for providers.
    
    Centralized defaults for provider-specific settings.
    """
    
    embedding_timeout: float = Field(default=60.0, ge=1.0, description="Timeout for embedding API calls in seconds")
    llm_max_tokens: int = Field(default=1024, ge=1, description="Maximum tokens for LLM responses")
    rerank_max_length: int = Field(default=512, ge=128, description="Maximum token length for reranking")
    default_embedding_dimension: int = Field(default=768, ge=1, description="Default embedding dimension")


# =============================================================================
# Path Configuration
# =============================================================================


class PathConfig(BaseModel):
    """Path configuration for data directories.
    
    Centralized configuration for all file system paths.
    """
    
    chroma_persist_dir: str = Field(default="./data/chroma", description="Chroma database persistence directory")
    qdrant_path: str = Field(default="./data/qdrant", description="Qdrant database path")
    rerank_cache_dir: str = Field(default="./data/flashrank_cache", description="Rerank model cache directory")
    bm25_persist_dir: str = Field(default="./data/bm25", description="BM25 index persistence directory")


# =============================================================================
# Configuration Loading
# =============================================================================


def _find_config_file(config_path: str = "config.yaml") -> Path:
    """Find configuration file, checking multiple locations.

    Args:
        config_path: Path to config file (relative or absolute)

    Returns:
        Resolved Path object

    Raises:
        FileNotFoundError: If config file not found
    """
    path = Path(config_path)

    if path.is_absolute() and path.exists():
        return path

    # Try current working directory
    if path.exists():
        return path

    # Try relative to backend directory
    backend_path = Path(__file__).parent.parent / config_path
    if backend_path.exists():
        return backend_path

    raise FileNotFoundError(f"Configuration file not found: {config_path}")


def _parse_provider_category(data: dict[str, Any]) -> ProviderCategory:
    """Parse a provider category from raw dict data."""
    return ProviderCategory(
        default=data.get("default", ""),
        instances=data.get("instances", [])
    )


def load_config_from_yaml(config_path: str = "config.yaml") -> AppConfig:
    """Load configuration from YAML file.

    Args:
        config_path: Path to YAML configuration file

    Returns:
        Loaded AppConfig object

    Raises:
        FileNotFoundError: If configuration file not found
        yaml.YAMLError: If YAML is malformed
        ValidationError: If configuration is invalid
    """
    path = _find_config_file(config_path)

    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    # Parse nested configuration
    server_data = data.get("server", {})
    chroma_data = data.get("chroma", {})
    providers_data = data.get("providers", {})
    indexer_data = data.get("indexer", {})
    watcher_data = data.get("watcher", {})
    logging_data = data.get("logging", {})
    hybrid_data = data.get("hybrid", {})
    cors_data = data.get("cors", {})

    return AppConfig(
        server=ServerConfig(
            host=server_data.get("host", "0.0.0.0"),
            port=server_data.get("port", 8818),
            debug=server_data.get("debug", True),
        ),
        chroma=ChromaConfig(
            persist_dir=chroma_data.get("persist_dir", "./data/chroma"),
            host=chroma_data.get("host"),
            port=chroma_data.get("port"),
        ),
        providers=ProvidersConfig(
            embedding=_parse_provider_category(providers_data.get("embedding", {})),
            rerank=_parse_provider_category(providers_data.get("rerank", {})),
            llm=_parse_provider_category(providers_data.get("llm", {})),
            vectorstore=_parse_provider_category(providers_data.get("vectorstore", {})),
        ),
        indexer=IndexerConfig(
            chunk_size=indexer_data.get("chunk_size", 500),
            chunk_overlap=indexer_data.get("chunk_overlap", 50),
            max_file_size=indexer_data.get("max_file_size", 1048576),
            file_types=indexer_data.get("file_types", [".py", ".ts", ".js", ".md", ".vue"]),
            exclude_dirs=indexer_data.get("exclude_dirs", ["node_modules", ".git", "__pycache__", "venv", ".venv", "dist", "build"]),
        ),
        watcher=WatcherConfig(
            enabled=watcher_data.get("enabled", True),
            debounce_seconds=watcher_data.get("debounce_seconds", 1.0),
        ),
        logging=LoggingConfig(
            level=logging_data.get("level", "INFO"),
            format=logging_data.get("format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"),
            file=logging_data.get("file"),
        ),
        hybrid=HybridConfig(
            alpha=hybrid_data.get("alpha", 0.5),
            beta=hybrid_data.get("beta", 0.5),
            rrf_k=hybrid_data.get("rrf_k", 60),
            bm25_persist_dir=hybrid_data.get("bm25_persist_dir", "./data/bm25"),
        ),
        cors=CORSConfig(
            origins=cors_data.get("origins", ["http://localhost:3315", "http://127.0.0.1:3315"]),
            allow_credentials=cors_data.get("allow_credentials", True),
            allow_methods=cors_data.get("allow_methods", ["*"]),
            allow_headers=cors_data.get("allow_headers", ["*"]),
        ),
    )


# =============================================================================
# Dependency Injection
# =============================================================================

# Module-level config instance (for non-FastAPI contexts)
_config_instance: Optional[AppConfig] = None


def get_config() -> AppConfig:
    """Get configuration instance.

    This function provides a global configuration access point.
    For FastAPI endpoints, prefer using config_dependency instead.

    Returns:
        Current AppConfig instance

    Raises:
        RuntimeError: If configuration not loaded
    """
    global _config_instance

    if _config_instance is None:
        try:
            _config_instance = load_config_from_yaml()
        except FileNotFoundError as e:
            raise RuntimeError(
                "No configuration loaded. Call load_config() first or ensure config.yaml exists."
            ) from e

    return _config_instance


def load_config(config_path: str = "config.yaml") -> AppConfig:
    """Load configuration and set as global instance.

    Args:
        config_path: Path to configuration file

    Returns:
        Loaded AppConfig instance
    """
    global _config_instance
    _config_instance = load_config_from_yaml(config_path)
    return _config_instance


def reload_config(config_path: str = "config.yaml") -> AppConfig:
    """Reload configuration from file.

    Args:
        config_path: Path to configuration file

    Returns:
        Newly loaded AppConfig instance
    """
    return load_config(config_path)


def set_config(config: AppConfig) -> None:
    """Set configuration instance (useful for testing).

    Args:
        config: AppConfig instance to set as global
    """
    global _config_instance
    _config_instance = config


def clear_config() -> None:
    """Clear configuration instance (useful for testing)."""
    global _config_instance
    _config_instance = None


# FastAPI dependency function
def get_config_dependency() -> AppConfig:
    """FastAPI dependency for configuration.

    Usage:
        @router.get("/")
        async def endpoint(config: AppConfig = Depends(get_config_dependency)):
            ...

    Returns:
        Current AppConfig instance
    """
    return get_config()


# =============================================================================
# Backward Compatibility
# =============================================================================

# Alias for backward compatibility with old dataclass-based Config
Config = AppConfig