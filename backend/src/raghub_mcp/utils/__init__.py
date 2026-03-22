"""Utils module."""

from .config import (
    AppConfig,
    ChromaConfig,
    HybridConfig,
    IndexerConfig,
    LoggingConfig,
    ProviderCategory,
    ProviderInstance,
    ProvidersConfig,
    ServerConfig,
    WatcherConfig,
    clear_config,
    get_config,
    get_config_dependency,
    load_config,
    reload_config,
    set_config,
)
from .migrate import (
    CollectionMigrationResult,
    MigrationResult,
    VectorStoreMigrator,
    migrate_chroma_to_qdrant,
)

# Backward compatibility alias
Config = AppConfig

__all__ = [
    # Config (new names)
    "AppConfig",
    "ServerConfig",
    "ChromaConfig",
    "ProvidersConfig",
    "IndexerConfig",
    "LoggingConfig",
    "HybridConfig",
    "WatcherConfig",
    "ProviderCategory",
    "ProviderInstance",
    "load_config",
    "reload_config",
    "get_config",
    "set_config",
    "clear_config",
    "get_config_dependency",
    # Backward compatibility
    "Config",
    # Migration
    "VectorStoreMigrator",
    "MigrationResult",
    "CollectionMigrationResult",
    "migrate_chroma_to_qdrant",
]
