"""Migration MCP tool implementation.

This module provides the migrate_vectorstore tool for migrating data
between different vector store providers (ChromaDB to Qdrant).
"""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

logger = logging.getLogger(__name__)

# Flag to track if tools are registered
_tools_registered = False


def register_migrate_tools(mcp: "FastMCP") -> None:
    """Register migration MCP tools.
    
    Args:
        mcp: The FastMCP server instance to register tools with.
    """
    global _tools_registered
    
    # Avoid duplicate registration
    if _tools_registered:
        logger.debug("Migration tools already registered, skipping")
        return
    
    @mcp.tool()
    def migrate_vectorstore(
        source_provider: str = "chroma",
        target_provider: str = "qdrant",
        collections: list[str] | None = None,
        batch_size: int = 100,
        verify: bool = True,
        chroma_persist_dir: str = "./data/chroma",
        qdrant_mode: str = "local",
        qdrant_path: str = "./data/qdrant",
        qdrant_host: str | None = None,
        qdrant_port: int | None = None,
        qdrant_url: str | None = None,
        qdrant_api_key: str | None = None,
    ) -> str:
        """Migrate data between vector store providers.
        
        This tool transfers collections and documents from a source vector
        store to a target vector store. Currently supports ChromaDB to Qdrant
        migration with full embedding preservation.
        
        Args:
            source_provider: Source provider type ("chroma")
            target_provider: Target provider type ("qdrant")
            collections: List of collection names to migrate.
                        If None, migrates all collections.
            batch_size: Number of documents to process per batch (default: 100)
            verify: Whether to verify data integrity after migration
            chroma_persist_dir: ChromaDB persistence directory
            qdrant_mode: Qdrant mode - "memory", "local", "remote", "cloud"
            qdrant_path: Qdrant storage path (for local mode)
            qdrant_host: Qdrant server host (for remote mode)
            qdrant_port: Qdrant server port (for remote mode)
            qdrant_url: Full URL (for cloud mode)
            qdrant_api_key: API key (for cloud mode)
        
        Returns:
            JSON string containing migration results:
            {
                "success": bool,
                "collections_migrated": int,
                "documents_migrated": int,
                "collections": [...],
                "errors": [...],
                "warnings": [...],
                "duration_seconds": float
            }
        
        Example:
            >>> # Migrate all collections from ChromaDB to local Qdrant
            >>> result = migrate_vectorstore(
            ...     source_provider="chroma",
            ...     target_provider="qdrant",
            ... )
            
            >>> # Migrate specific collections to Qdrant Cloud
            >>> result = migrate_vectorstore(
            ...     collections=["docs", "code"],
            ...     qdrant_mode="cloud",
            ...     qdrant_url="https://your-cluster.cloud.qdrant.io:6333",
            ...     qdrant_api_key="your-api-key",
            ... )
        """
        # Validate provider types
        if source_provider != "chroma":
            return json.dumps({
                "success": False,
                "error": f"Unsupported source provider: {source_provider}. Only 'chroma' is supported.",
                "collections_migrated": 0,
                "documents_migrated": 0,
            }, indent=2)
        
        if target_provider != "qdrant":
            return json.dumps({
                "success": False,
                "error": f"Unsupported target provider: {target_provider}. Only 'qdrant' is supported.",
                "collections_migrated": 0,
                "documents_migrated": 0,
            }, indent=2)
        
        try:
            from providers.vectorstore import ChromaProvider, QdrantProvider
            from utils.migrate import VectorStoreMigrator
            
            # Initialize source provider
            source = ChromaProvider(persist_dir=chroma_persist_dir)
            
            # Initialize target provider
            target_kwargs = {"mode": qdrant_mode}
            if qdrant_path:
                target_kwargs["path"] = qdrant_path
            if qdrant_host:
                target_kwargs["host"] = qdrant_host
            if qdrant_port:
                target_kwargs["port"] = qdrant_port
            if qdrant_url:
                target_kwargs["url"] = qdrant_url
            if qdrant_api_key:
                target_kwargs["api_key"] = qdrant_api_key
            
            target = QdrantProvider(**target_kwargs)
            
            # Create migrator and execute
            migrator = VectorStoreMigrator(
                source=source,
                target=target,
                batch_size=batch_size,
            )
            
            logger.info(
                f"Starting migration: {source_provider} -> {target_provider}, "
                f"collections={collections or 'all'}"
            )
            
            result = migrator.migrate(
                collections=collections,
                verify=verify,
            )
            
            logger.info(
                f"Migration completed: {result.documents_migrated} documents, "
                f"{result.duration_seconds:.2f}s"
            )
            
            return json.dumps(result.to_dict(), indent=2)
            
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            return json.dumps({
                "success": False,
                "error": str(e),
                "collections_migrated": 0,
                "documents_migrated": 0,
            }, indent=2)
    
    @mcp.tool()
    def list_vectorstore_collections(
        provider: str = "chroma",
        chroma_persist_dir: str = "./data/chroma",
        qdrant_mode: str = "local",
        qdrant_path: str = "./data/qdrant",
    ) -> str:
        """List all collections in a vector store.
        
        This tool lists all collections available in the specified
        vector store provider, useful for planning migrations.
        
        Args:
            provider: Provider type ("chroma" or "qdrant")
            chroma_persist_dir: ChromaDB persistence directory
            qdrant_mode: Qdrant mode ("memory", "local", "remote", "cloud")
            qdrant_path: Qdrant storage path (for local mode)
        
        Returns:
            JSON string containing collection information:
            {
                "provider": str,
                "collections": [
                    {
                        "name": str,
                        "count": int
                    },
                    ...
                ],
                "total_collections": int,
                "total_documents": int
            }
        
        Example:
            >>> result = list_vectorstore_collections(provider="chroma")
        """
        try:
            if provider == "chroma":
                from providers.vectorstore import ChromaProvider
                vs_provider = ChromaProvider(persist_dir=chroma_persist_dir)
            elif provider == "qdrant":
                from providers.vectorstore import QdrantProvider
                vs_provider = QdrantProvider(mode=qdrant_mode, path=qdrant_path)
            else:
                return json.dumps({
                    "error": f"Unsupported provider: {provider}",
                    "collections": [],
                }, indent=2)
            
            collections = []
            total_documents = 0
            
            for name in vs_provider.list_collections():
                try:
                    count = vs_provider.count(name)
                    collections.append({"name": name, "count": count})
                    total_documents += count
                except Exception as e:
                    collections.append({"name": name, "count": 0, "error": str(e)})
            
            result = {
                "provider": provider,
                "collections": collections,
                "total_collections": len(collections),
                "total_documents": total_documents,
            }
            
            return json.dumps(result, indent=2)
            
        except Exception as e:
            logger.error(f"Failed to list collections: {e}")
            return json.dumps({
                "error": str(e),
                "collections": [],
            }, indent=2)
    
    _tools_registered = True
    logger.debug("Migration tools registered")