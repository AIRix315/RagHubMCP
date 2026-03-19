"""Watcher MCP tools for incremental indexing.

This module provides MCP tools for:
- Starting file watcher on a directory
- Stopping the file watcher
- Getting watcher status
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import TYPE_CHECKING

from src.indexer.incremental import IncrementalIndexer
from src.indexer.watcher import (
    FileEvent,
    FileWatcher,
    WatcherConfig,
    get_watcher,
    reset_watcher,
)

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

logger = logging.getLogger(__name__)

# Flag to track if tools are registered
_tools_registered = False

# Global state for incremental indexer
_incremental_indexer: IncrementalIndexer | None = None
_collection_name: str | None = None


def _get_watcher_config() -> WatcherConfig:
    """Get watcher configuration from config."""
    try:
        from utils.config import get_config
        config = get_config()
        return WatcherConfig(
            debounce_seconds=getattr(config, "watcher", None) and config.watcher.debounce_seconds or 1.0,
            exclude_dirs=config.indexer.exclude_dirs,
            file_types=config.indexer.file_types,
        )
    except Exception:
        return WatcherConfig()


def _on_file_events(events: list[FileEvent]) -> None:
    """Callback for file events from watcher.
    
    Args:
        events: List of file events to process.
    """
    global _incremental_indexer
    
    if _incremental_indexer is None:
        logger.warning("No incremental indexer configured")
        return
    
    logger.info(f"Processing {len(events)} file events")
    result = _incremental_indexer.process_events(events)
    
    logger.info(
        f"Incremental update: added={result.files_added}, "
        f"updated={result.files_updated}, deleted={result.files_deleted}"
    )


def register_watcher_tools(mcp: "FastMCP") -> None:
    """Register watcher MCP tools.
    
    Args:
        mcp: The FastMCP server instance to register tools with.
    """
    global _tools_registered
    
    # Avoid duplicate registration
    if _tools_registered:
        logger.debug("Watcher tools already registered, skipping")
        return
    
    @mcp.tool()
    def start_watcher(
        path: str,
        collection_name: str,
        recursive: bool = True,
    ) -> str:
        """Start watching a directory for file changes.
        
        When file changes are detected, the index is automatically updated:
        - New files: Added to the index
        - Modified files: Re-indexed with updated content
        - Deleted files: Removed from the index
        
        Args:
            path: Directory path to watch (must exist).
            collection_name: ChromaDB collection to update.
            recursive: Watch subdirectories (default: True).
        
        Returns:
            JSON string with status and watcher information.
        
        Example:
            >>> start_watcher("/path/to/project", "code_index")
        """
        global _incremental_indexer, _collection_name
        
        # Validate path
        watch_path = Path(path).resolve()
        if not watch_path.exists():
            return json.dumps({
                "status": "error",
                "message": f"Path does not exist: {path}",
                "watcher_running": False,
            })
        
        if not watch_path.is_dir():
            return json.dumps({
                "status": "error",
                "message": f"Path is not a directory: {path}",
                "watcher_running": False,
            })
        
        # Check if already running
        watcher = get_watcher()
        if watcher.is_running:
            return json.dumps({
                "status": "error",
                "message": f"Watcher already running on: {watcher.watch_path}",
                "watcher_running": True,
                "current_path": str(watcher.watch_path),
            })
        
        try:
            # Get services
            from services import get_chroma_service
            from providers.factory import factory
            from indexer.indexer import Indexer
            from utils.config import get_config
            
            config = get_config()
            chroma_service = get_chroma_service()
            collection = chroma_service.get_or_create_collection(collection_name)
            embedding_provider = factory.get_embedding_provider()
            
            # Create indexer and incremental indexer
            indexer = Indexer(config.indexer, embedding_provider, collection)
            _incremental_indexer = IncrementalIndexer(
                indexer=indexer,
                collection=collection,
                config=config.indexer,
            )
            _collection_name = collection_name
            
            # Create new watcher with callback
            watcher_config = _get_watcher_config()
            new_watcher = FileWatcher(watcher_config, _on_file_events)
            
            # Reset singleton and set new watcher
            reset_watcher()
            watcher = get_watcher(watcher_config, _on_file_events)
            
            # Start watching
            success = watcher.start(watch_path, recursive=recursive)
            
            if success:
                return json.dumps({
                    "status": "started",
                    "message": f"Started watching: {watch_path}",
                    "watch_path": str(watch_path),
                    "collection": collection_name,
                    "recursive": recursive,
                    "debounce_seconds": watcher_config.debounce_seconds,
                })
            else:
                return json.dumps({
                    "status": "error",
                    "message": "Failed to start watcher",
                    "watcher_running": False,
                })
                
        except Exception as e:
            logger.error(f"Error starting watcher: {e}")
            return json.dumps({
                "status": "error",
                "message": f"Failed to start watcher: {str(e)}",
                "watcher_running": False,
            })
    
    @mcp.tool()
    def stop_watcher() -> str:
        """Stop the file watcher.
        
        Stops watching for file changes. The existing indexed content
        is preserved.
        
        Returns:
            JSON string with status confirmation.
        """
        global _incremental_indexer, _collection_name
        
        try:
            watcher = get_watcher()
            
            if not watcher.is_running:
                return json.dumps({
                    "status": "not_running",
                    "message": "Watcher is not running",
                })
            
            watch_path = watcher.watch_path
            watcher.stop()
            
            # Clear state
            _incremental_indexer = None
            _collection_name = None
            
            return json.dumps({
                "status": "stopped",
                "message": f"Stopped watching: {watch_path}",
            })
            
        except Exception as e:
            logger.error(f"Error stopping watcher: {e}")
            return json.dumps({
                "status": "error",
                "message": f"Failed to stop watcher: {str(e)}",
            })
    
    @mcp.tool()
    def get_watcher_status() -> str:
        """Get the current watcher status.
        
        Returns information about whether the watcher is running,
        what directory is being watched, and which collection is
        being updated.
        
        Returns:
            JSON string with watcher status information.
        """
        try:
            watcher = get_watcher()
            
            status = {
                "is_running": watcher.is_running,
                "watch_path": str(watcher.watch_path) if watcher.watch_path else None,
                "collection": _collection_name,
            }
            
            if watcher.is_running:
                status["status"] = "running"
                status["message"] = f"Watching {watcher.watch_path}"
            else:
                status["status"] = "stopped"
                status["message"] = "Watcher is not running"
            
            return json.dumps(status, indent=2)
            
        except Exception as e:
            logger.error(f"Error getting watcher status: {e}")
            return json.dumps({
                "status": "error",
                "message": f"Failed to get status: {str(e)}",
                "is_running": False,
            })
    
    @mcp.tool()
    def sync_directory(
        path: str,
        collection_name: str,
    ) -> str:
        """Synchronize a directory with the index.
        
        Scans the directory and performs incremental updates:
        - Adds new files not in index
        - Updates files with changed content (by content hash)
        - Removes deleted files from index
        
        Use this for initial sync or periodic consistency checks.
        
        Args:
            path: Directory path to synchronize.
            collection_name: ChromaDB collection to sync with.
        
        Returns:
            JSON string with sync statistics.
        
        Example:
            >>> sync_directory("/path/to/project", "code_index")
        """
        sync_path = Path(path).resolve()
        
        if not sync_path.exists():
            return json.dumps({
                "status": "error",
                "message": f"Path does not exist: {path}",
            })
        
        if not sync_path.is_dir():
            return json.dumps({
                "status": "error",
                "message": f"Path is not a directory: {path}",
            })
        
        try:
            from services import get_chroma_service
            from providers.factory import factory
            from indexer.indexer import Indexer
            from utils.config import get_config
            
            config = get_config()
            chroma_service = get_chroma_service()
            collection = chroma_service.get_or_create_collection(collection_name)
            embedding_provider = factory.get_embedding_provider()
            
            indexer = Indexer(config.indexer, embedding_provider, collection)
            incremental = IncrementalIndexer(
                indexer=indexer,
                collection=collection,
                config=config.indexer,
            )
            
            result = incremental.sync_directory(sync_path)
            
            return json.dumps({
                "status": "completed",
                "path": str(sync_path),
                "collection": collection_name,
                "files_added": result.files_added,
                "files_updated": result.files_updated,
                "files_deleted": result.files_deleted,
                "chunks_added": result.chunks_added,
                "chunks_removed": result.chunks_removed,
                "errors": result.errors,
            }, indent=2)
            
        except Exception as e:
            logger.error(f"Error syncing directory: {e}")
            return json.dumps({
                "status": "error",
                "message": f"Failed to sync directory: {str(e)}",
            })
    
    _tools_registered = True
    logger.debug("Watcher tools registered")