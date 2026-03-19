"""Configuration management module for RagHubMCP.

This module provides configuration loading, validation, and hot-reload functionality.
Uses YAML for configuration files and dataclasses for type-safe config structures.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any

import yaml


@dataclass
class ServerConfig:
    """Server configuration settings.
    
    Attributes:
        host: Server host address.
        port: Server port number.
        debug: Enable debug mode.
    """
    host: str = "0.0.0.0"
    port: int = 8818
    debug: bool = True


@dataclass
class ChromaConfig:
    """Chroma vector database configuration.
    
    Attributes:
        persist_dir: Directory for persistent storage.
        host: Remote Chroma server host (None for local).
        port: Remote Chroma server port (None for local).
    """
    persist_dir: str = "./data/chroma"
    host: str | None = None
    port: int | None = None


@dataclass
class ProviderInstance:
    """Provider instance configuration.
    
    Attributes:
        name: Unique identifier for this provider instance.
        type: Provider type (e.g., 'ollama', 'openai', 'flashrank').
        model: Model name or identifier.
        base_url: Base URL for API calls (optional).
        dimension: Embedding dimension (optional, for embedding providers).
    """
    name: str
    type: str
    model: str
    base_url: str | None = None
    dimension: int | None = None


@dataclass
class ProviderCategoryConfig:
    """Configuration for a category of providers (embedding, rerank, llm).
    
    Attributes:
        default: Name of the default provider instance.
        instances: List of available provider instances.
    """
    default: str
    instances: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class ProvidersConfig:
    """All provider configurations.
    
    Attributes:
        embedding: Embedding provider configurations.
        rerank: Rerank provider configurations.
        llm: LLM provider configurations.
        vectorstore: Vector store provider configurations.
    """
    embedding: ProviderCategoryConfig = field(default_factory=lambda: ProviderCategoryConfig(default=""))
    rerank: ProviderCategoryConfig = field(default_factory=lambda: ProviderCategoryConfig(default=""))
    llm: ProviderCategoryConfig = field(default_factory=lambda: ProviderCategoryConfig(default=""))
    vectorstore: ProviderCategoryConfig = field(default_factory=lambda: ProviderCategoryConfig(default=""))


@dataclass
class IndexerConfig:
    """File indexer configuration.
    
    Attributes:
        chunk_size: Maximum characters per chunk.
        chunk_overlap: Overlap characters between chunks.
        max_file_size: Maximum file size in bytes.
        file_types: List of file extensions to index.
        exclude_dirs: List of directory names to exclude.
    """
    chunk_size: int = 500
    chunk_overlap: int = 50
    max_file_size: int = 1048576  # 1MB
    file_types: list[str] = field(default_factory=lambda: [".py", ".ts", ".js", ".md", ".vue"])
    exclude_dirs: list[str] = field(default_factory=lambda: ["node_modules", ".git", "__pycache__", "venv", ".venv", "dist", "build"])


@dataclass
class WatcherConfig:
    """File watcher configuration.
    
    Attributes:
        enabled: Whether the watcher is enabled.
        debounce_seconds: Seconds to wait before processing batched events.
    """
    enabled: bool = True
    debounce_seconds: float = 1.0


@dataclass
class HybridConfig:
    """Hybrid search configuration.
    
    Attributes:
        alpha: Weight for vector search results (default: 0.5).
        beta: Weight for BM25 search results (default: 0.5).
        rrf_k: RRF constant for reciprocal rank fusion (default: 60).
        bm25_persist_dir: Directory for BM25 index storage.
    """
    alpha: float = 0.5
    beta: float = 0.5
    rrf_k: int = 60
    bm25_persist_dir: str = "./data/bm25"


@dataclass
class LoggingConfig:
    """Logging configuration.
    
    Attributes:
        level: Log level (DEBUG, INFO, WARNING, ERROR).
        format: Log message format string.
        file: Log file path (optional).
    """
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file: str | None = None


@dataclass
class Config:
    """Root configuration object.
    
    Attributes:
        server: Server configuration.
        chroma: Chroma database configuration.
        providers: Provider configurations.
        indexer: Indexer configuration.
        watcher: File watcher configuration.
        logging: Logging configuration.
        hybrid: Hybrid search configuration.
    """
    server: ServerConfig = field(default_factory=ServerConfig)
    chroma: ChromaConfig = field(default_factory=ChromaConfig)
    providers: ProvidersConfig = field(default_factory=ProvidersConfig)
    indexer: IndexerConfig = field(default_factory=IndexerConfig)
    watcher: WatcherConfig = field(default_factory=WatcherConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    hybrid: HybridConfig = field(default_factory=HybridConfig)


# Global configuration instance
_config: Config | None = None


def _parse_provider_category(data: dict[str, Any]) -> ProviderCategoryConfig:
    """Parse a provider category from raw dict data.
    
    Args:
        data: Raw dictionary data from YAML.
        
    Returns:
        Parsed ProviderCategoryConfig object.
    """
    return ProviderCategoryConfig(
        default=data.get("default", ""),
        instances=data.get("instances", [])
    )


def _parse_config(data: dict[str, Any]) -> Config:
    """Parse configuration from raw YAML data.
    
    Args:
        data: Raw dictionary data from YAML file.
        
    Returns:
        Parsed Config object.
    """
    server_data = data.get("server", {})
    server_config = ServerConfig(
        host=server_data.get("host", "0.0.0.0"),
        port=server_data.get("port", 8818),
        debug=server_data.get("debug", True)
    )
    
    chroma_data = data.get("chroma", {})
    chroma_config = ChromaConfig(
        persist_dir=chroma_data.get("persist_dir", "./data/chroma"),
        host=chroma_data.get("host"),
        port=chroma_data.get("port")
    )
    
    providers_data = data.get("providers", {})
    providers_config = ProvidersConfig(
        embedding=_parse_provider_category(providers_data.get("embedding", {})),
        rerank=_parse_provider_category(providers_data.get("rerank", {})),
        llm=_parse_provider_category(providers_data.get("llm", {})),
        vectorstore=_parse_provider_category(providers_data.get("vectorstore", {}))
    )
    
    indexer_data = data.get("indexer", {})
    indexer_config = IndexerConfig(
        chunk_size=indexer_data.get("chunk_size", 500),
        chunk_overlap=indexer_data.get("chunk_overlap", 50),
        max_file_size=indexer_data.get("max_file_size", 1048576),
        file_types=indexer_data.get("file_types", [".py", ".ts", ".js", ".md", ".vue"]),
        exclude_dirs=indexer_data.get("exclude_dirs", ["node_modules", ".git", "__pycache__", "venv", ".venv", "dist", "build"])
    )
    
    logging_data = data.get("logging", {})
    logging_config = LoggingConfig(
        level=logging_data.get("level", "INFO"),
        format=logging_data.get("format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"),
        file=logging_data.get("file")
    )
    
    hybrid_data = data.get("hybrid", {})
    hybrid_config = HybridConfig(
        alpha=hybrid_data.get("alpha", 0.5),
        beta=hybrid_data.get("beta", 0.5),
        rrf_k=hybrid_data.get("rrf_k", 60),
        bm25_persist_dir=hybrid_data.get("bm25_persist_dir", "./data/bm25")
    )
    
    watcher_data = data.get("watcher", {})
    watcher_config = WatcherConfig(
        enabled=watcher_data.get("enabled", True),
        debounce_seconds=watcher_data.get("debounce_seconds", 1.0)
    )
    
    return Config(
        server=server_config,
        chroma=chroma_config,
        providers=providers_config,
        indexer=indexer_config,
        watcher=watcher_config,
        logging=logging_config,
        hybrid=hybrid_config
    )


def load_config(config_path: str = "config.yaml") -> Config:
    """Load configuration from a YAML file.
    
    This function loads configuration from the specified YAML file and
    stores it as the global configuration instance.
    
    Args:
        config_path: Path to the configuration file. Can be relative or absolute.
        
    Returns:
        The loaded Config object.
        
    Raises:
        FileNotFoundError: If the configuration file does not exist.
        yaml.YAMLError: If the YAML file is malformed.
    """
    global _config
    
    path = Path(config_path)
    if not path.is_absolute():
        # Try relative to current working directory first
        if not path.exists():
            # Try relative to backend directory
            backend_path = Path(__file__).parent.parent.parent / config_path
            if backend_path.exists():
                path = backend_path
    
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    
    _config = _parse_config(data)
    return _config


def reload_config(config_path: str = "config.yaml") -> Config:
    """Reload configuration from the YAML file.
    
    This is used for hot-reloading configuration without restarting the server.
    It re-reads the configuration file and updates the global instance.
    
    Args:
        config_path: Path to the configuration file.
        
    Returns:
        The newly loaded Config object.
    """
    return load_config(config_path)


def get_config() -> Config:
    """Get the current global configuration instance.
    
    If no configuration has been loaded yet, this will attempt to load
    the default configuration file (config.yaml).
    
    Returns:
        The current Config object.
        
    Raises:
        RuntimeError: If no configuration is loaded and default config.yaml is not found.
    """
    global _config
    if _config is None:
        try:
            return load_config()
        except FileNotFoundError as e:
            raise RuntimeError(
                "No configuration loaded. Call load_config() first or ensure config.yaml exists."
            ) from e
    return _config


def config_to_dict(config: Config) -> dict[str, Any]:
    """Convert a Config object to a dictionary.
    
    Useful for serializing configuration to JSON or YAML.
    
    Args:
        config: The Config object to convert.
        
    Returns:
        Dictionary representation of the configuration.
    """
    return asdict(config)