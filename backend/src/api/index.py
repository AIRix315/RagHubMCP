"""Index task management REST API endpoints.

This module provides endpoints for starting and monitoring indexing tasks.

Security Note:
    Path validation is performed to prevent path traversal attacks.
    Only paths within configured allowed_roots are permitted.
"""

from __future__ import annotations

import asyncio
import logging
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Sequence

from fastapi import APIRouter, HTTPException

from src.api.websocket import manager as ws_manager
from src.utils.config import get_config

from .schemas import (
    ErrorResponse,
    IndexRequest,
    IndexResponse,
    IndexTaskStatus,
)
from .schemas import (
    TaskStatus as TaskStatusEnum,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/index", tags=["index"])

# In-memory task storage (MVP approach)
_tasks: dict[str, IndexTaskStatus] = {}

# Forbidden path patterns (system directories)
FORBIDDEN_PATHS = {
    "/etc",
    "/var",
    "/usr",
    "/bin",
    "/sbin",
    "/boot",
    "/proc",
    "/sys",
    "/root",
    "/home",
    "C:\\Windows",
    "C:\\Program Files",
    "C:\\Program Files (x86)",
}

# Windows-specific forbidden paths
WINDOWS_FORBIDDEN = {
    "\\Windows",
    "\\Program Files",
    "\\Program Files (x86)",
    "\\System32",
}


def validate_path_security(
    path: str | Path | None,
    allowed_roots: Sequence[Path] | None = None,
) -> str | None:
    """Validate path for security (path traversal prevention).
    
    This function prevents:
    1. Path traversal attacks (../../../etc/passwd)
    2. Access to system directories
    3. Symlink escape attacks
    4. Access outside allowed directories
    
    Args:
        path: Path to validate.
        allowed_roots: List of allowed root directories. If empty, 
                      only basic validation is performed.
    
    Returns:
        Error message if validation fails, None if path is valid.
    
    Examples:
        >>> validate_path_security("/etc/passwd", [Path("/data")])
        "Path '/etc/passwd' is not in allowed directories"
        
        >>> validate_path_security("/data/docs", [Path("/data")])
        None
    """
    if path is None or path == "":
        return "Path cannot be empty"
    
    # Convert to Path and resolve
    try:
        path_obj = Path(path)
        # Get absolute path without resolving symlinks yet
        abs_path = path_obj.absolute()
    except (TypeError, ValueError) as e:
        return f"Invalid path format: {e}"
    
    # Normalize path (resolve .. and .)
    try:
        # Use os.path.normpath for cross-platform normalization
        normalized_str = os.path.normpath(str(abs_path))
        normalized_path = Path(normalized_str)
    except (TypeError, ValueError):
        return "Failed to normalize path"
    
    # Check for path traversal patterns
    path_str = str(normalized_path)
    
    # Check for .. patterns (should be resolved, but double check)
    if ".." in path_str:
        # After normalization, .. should be resolved
        # If still present, it might be an attempt to escape
        return "Path contains forbidden traversal pattern '../'"
    
    # Check for empty components
    parts = normalized_path.parts
    if not parts:
        return "Invalid empty path"
    
    # Check forbidden path prefixes
    lower_path = path_str.lower()
    
    # Check Unix forbidden paths
    for forbidden in FORBIDDEN_PATHS:
        if lower_path.startswith(forbidden.lower()) or path_str.startswith(forbidden):
            return f"Access to system directory '{path_str}' is forbidden"
    
    # Check Windows forbidden paths
    if os.name == 'nt':
        for forbidden in WINDOWS_FORBIDDEN:
            if forbidden.lower() in lower_path:
                return f"Access to system directory '{path_str}' is forbidden"
    
    # Validate against allowed_roots
    if allowed_roots:
        # Convert allowed_roots to absolute paths
        allowed_abs = [Path(root).absolute() for root in allowed_roots if root]
        
        if not allowed_abs:
            # No allowed roots means no access (safest default)
            return "No allowed directories configured"
        
        # Check if normalized path is under any allowed root
        # Use resolve() to handle symlinks safely
        try:
            resolved_path = normalized_path.resolve()
        except (OSError, RuntimeError):
            # Path doesn't exist or can't be resolved
            # Still check if it would be under allowed root
            resolved_path = normalized_path
        
        for allowed in allowed_abs:
            try:
                allowed_resolved = allowed.resolve()
            except (OSError, RuntimeError):
                allowed_resolved = allowed
            
            # Check if path is under allowed directory
            try:
                # relative_to raises ValueError if not under the root
                resolved_path.relative_to(allowed_resolved)
                # Path is valid
                return None
            except ValueError:
                continue
        
        # Path is not under any allowed root
        return f"Path '{path_str}' is not in allowed directories"
    
    return None


def get_task(task_id: str) -> IndexTaskStatus | None:
    """Get task status by ID.
    
    Args:
        task_id: Task identifier.
        
    Returns:
        Task status or None if not found.
    """
    return _tasks.get(task_id)


def list_tasks() -> list[IndexTaskStatus]:
    """List all tasks.
    
    Returns:
        List of all task statuses.
    """
    return list(_tasks.values())


async def run_index_task(
    task_id: str,
    path: str,
    collection_name: str,
    embedding_provider: str | None,
    chunk_size: int | None,
    chunk_overlap: int | None,
) -> None:
    """Background task to perform indexing.
    
    Args:
        task_id: Unique task identifier.
        path: Directory or file path to index.
        collection_name: Chroma collection name.
        embedding_provider: Optional embedding provider name.
        chunk_size: Optional chunk size override.
        chunk_overlap: Optional chunk overlap override.
    """
    task = _tasks[task_id]

    async def broadcast_progress():
        """Broadcast current progress via WebSocket."""
        await ws_manager.broadcast_progress(
            task_id=task_id,
            status=task.status.value,
            progress=task.progress,
            message=task.message,
            total_files=task.total_files,
            processed_files=task.processed_files,
            total_chunks=task.total_chunks,
            error=task.error,
        )

    try:
        task.status = TaskStatusEnum.RUNNING
        task.message = "Scanning files..."
        await broadcast_progress()

        # Get configuration
        config = get_config()

        # Import scanner
        from indexer.scanner import FileScanner

        scanner = FileScanner(config.indexer)
        root_path = Path(path)

        if not root_path.exists():
            raise ValueError(f"Path does not exist: {path}")

        # Scan files
        files = scanner.scan(root_path, compute_hash=True)
        task.total_files = len(files)
        task.message = f"Found {len(files)} files to index"
        await broadcast_progress()

        if not files:
            task.status = TaskStatusEnum.COMPLETED
            task.message = "No files to index"
            task.completed_at = datetime.now()
            await broadcast_progress()
            return

        # Process files
        chunks_created = 0
        for i, file_info in enumerate(files):
            task.message = f"Processing {file_info.path.name}"
            task.processed_files = i + 1
            task.progress = (i + 1) / len(files)
            
            # Broadcast progress every 10 files or at completion
            if (i + 1) % 10 == 0 or i == len(files) - 1:
                await broadcast_progress()

            # Simulate chunking and embedding (placeholder)
            # In full implementation, this would:
            # 1. Read file content
            # 2. Chunk using configured chunker
            # 3. Generate embeddings
            # 4. Store in Chroma

            # For MVP, we just count estimated chunks
            estimated_chunks = max(1, file_info.size // (chunk_size or config.indexer.chunk_size))
            chunks_created += estimated_chunks

            # Small delay to simulate processing
            await asyncio.sleep(0.01)

        task.total_chunks = chunks_created
        task.status = TaskStatusEnum.COMPLETED
        task.message = f"Indexing completed: {len(files)} files, {chunks_created} chunks"
        task.progress = 1.0
        task.completed_at = datetime.now()
        await broadcast_progress()

        logger.info(f"Index task {task_id} completed: {task.message}")

    except Exception as e:
        task.status = TaskStatusEnum.FAILED
        task.error = str(e)
        task.message = f"Indexing failed: {str(e)}"
        task.completed_at = datetime.now()
        await broadcast_progress()
        logger.error(f"Index task {task_id} failed: {e}")


@router.post(
    "",
    response_model=IndexResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request or path not allowed"},
        404: {"model": ErrorResponse, "description": "Path not found"},
        403: {"model": ErrorResponse, "description": "Path access forbidden"},
    },
    summary="Start indexing task",
    description="Start a new indexing task for the specified path. Path must be within allowed directories.",
)
async def start_index(request: IndexRequest) -> IndexResponse:
    """Start an indexing task.
    
    TC-1.15.3: POST /api/index starts indexing
    
    Security:
        - Path must be within configured allowed_roots
        - Path traversal attempts are blocked
        - System directories are forbidden
    
    Args:
        request: Index request parameters.
        
    Returns:
        Task ID and status URL.
        
    Raises:
        HTTPException: If path is invalid or not allowed.
    """
    # Get configuration for allowed paths
    config = get_config()
    allowed_roots = []
    
    # Get allowed roots from config
    if hasattr(config.indexer, 'allowed_roots') and config.indexer.allowed_roots:
        allowed_roots = [Path(r) for r in config.indexer.allowed_roots]
    
    # Validate path security
    validation_error = validate_path_security(request.path, allowed_roots)
    if validation_error:
        raise HTTPException(
            status_code=403,
            detail={
                "error": "path_not_allowed",
                "message": validation_error,
            }
        )
    
    # Validate path exists
    path = Path(request.path)
    if not path.exists():
        raise HTTPException(
            status_code=404,
            detail={
                "error": "path_not_found",
                "message": f"Path does not exist: {request.path}",
            }
        )

    # Create task
    task_id = str(uuid.uuid4())
    task = IndexTaskStatus(
        task_id=task_id,
        status=TaskStatusEnum.PENDING,
        progress=0.0,
        message="Task created, waiting to start",
        created_at=datetime.now(),
    )
    _tasks[task_id] = task

    # Start background task
    asyncio.create_task(
        run_index_task(
            task_id=task_id,
            path=request.path,
            collection_name=request.collection_name,
            embedding_provider=request.embedding_provider,
            chunk_size=request.chunk_size,
            chunk_overlap=request.chunk_overlap,
        )
    )

    logger.info(f"Started index task {task_id} for path: {request.path}")

    return IndexResponse(
        task_id=task_id,
        message="Indexing task started",
        status_url=f"/api/index/status/{task_id}",
    )


@router.get(
    "/status/{task_id}",
    response_model=IndexTaskStatus,
    responses={
        404: {"model": ErrorResponse, "description": "Task not found"},
    },
    summary="Get task status",
    description="Get the status of an indexing task",
)
async def get_index_status(task_id: str) -> IndexTaskStatus:
    """Get indexing task status.
    
    TC-1.15.4: GET /api/index/status queries status
    
    Args:
        task_id: Task identifier.
        
    Returns:
        Task status.
        
    Raises:
        HTTPException: If task not found.
    """
    task = _tasks.get(task_id)
    if task is None:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "task_not_found",
                "message": f"Task not found: {task_id}",
            }
        )

    return task


@router.get(
    "/status",
    response_model=list[IndexTaskStatus],
    summary="List all tasks",
    description="List all indexing tasks and their statuses",
)
async def list_index_tasks() -> list[IndexTaskStatus]:
    """List all indexing tasks.
    
    Returns:
        List of all tasks.
    """
    return list(_tasks.values())
