"""Configuration management for RagHubMCP.

This module provides unified configuration using Pydantic models,
YAML loading, and dependency injection support.

Design:
- Single source of truth for config models (Pydantic)
- YAML-based configuration file
- Dependency injection for testability
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any, Optional

import yaml
from pydantic import BaseModel, ConfigDict, Field


# =============================================================================
# Configuration Models (Pydantic - Single Source of Truth)
# =============================================================================


class ServerConfig(BaseModel):
    """Server configuration."""

    host: str = Field(default="0.0.0.0", description="Server host address")
    port: int = Field(default=8818, description="Server port")
    debug: bool = Field(default=True, description="Enable debug mode")


class ChromaConfig(BaseModel):
    """Chroma vector database configuration."""

    persist_dir: str = Field(default="./data/chroma", description="Persistence directory")
    host: Optional[str] = Field(default=None, description="Remote host (None for local)")
    port: Optional[int] = Field(default=None, description="Remote port (None for local)")


class ProviderInstance(BaseModel):
    """Provider instance configuration."""

    name: str = Field(..., description="Unique identifier")
    type: str = Field(..., description="Provider type (e.g., ollama, openai)")
    model: str = Field(..., description="Model name")
    base_url: Optional[str] = Field(default=None, description="API base URL")
    dimension: Optional[int] = Field(default=None, description="Embedding dimension")


class ProviderCategory(BaseModel):
    """Configuration for a category of providers."""

    default: str = Field(default="", description="Default provider name")
    instances: list[dict[str, Any]] = Field(default_factory=list, description="Provider instances")


class ProvidersConfig(BaseModel):
    """All provider configurations."""

    embedding: ProviderCategory = Field(default_factory=ProviderCategory)
    rerank: ProviderCategory = Field(default_factory=ProviderCategory)
    llm: ProviderCategory = Field(default_factory=ProviderCategory)
    vectorstore: ProviderCategory = Field(default_factory=ProviderCategory)


class IndexerConfig(BaseModel):
    """File indexer configuration."""

    chunk_size: int = Field(default=500, description="Max characters per chunk")
    chunk_overlap: int = Field(default=50, description="Overlap between chunks")
    max_file_size: int = Field(default=1048576, description="Max file size in bytes")
    file_types: list[str] = Field(
        default_factory=lambda: [".py", ".ts", ".js", ".md", ".vue"],
        description="File extensions to index"
    )
    exclude_dirs: list[str] = Field(
        default_factory=lambda: ["node_modules", ".git", "__pycache__", "venv", ".venv", "dist", "build"],
        description="Directories to exclude"
    )


class WatcherConfig(BaseModel):
    """File watcher configuration."""

    enabled: bool = Field(default=True, description="Enable file watcher")
    debounce_seconds: float = Field(default=1.0, description="Debounce delay")


class HybridConfig(BaseModel):
    """Hybrid search configuration."""

    alpha: float = Field(default=0.5, ge=0.0, le=1.0, description="Vector search weight")
    beta: float = Field(default=0.5, ge=0.0, le=1.0, description="BM25 search weight")
    rrf_k: int = Field(default=60, ge=1, description="RRF constant")
    bm25_persist_dir: str = Field(default="./data/bm25", description="BM25 index directory")


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