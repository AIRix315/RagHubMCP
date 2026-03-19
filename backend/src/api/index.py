"""Index task management REST API endpoints.

This module provides endpoints for starting and monitoring indexing tasks.
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import datetime
from pathlib import Path

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
        400: {"model": ErrorResponse, "description": "Invalid request"},
        404: {"model": ErrorResponse, "description": "Path not found"},
    },
    summary="Start indexing task",
    description="Start a new indexing task for the specified path",
)
async def start_index(request: IndexRequest) -> IndexResponse:
    """Start an indexing task.
    
    TC-1.15.3: POST /api/index starts indexing
    
    Args:
        request: Index request parameters.
        
    Returns:
        Task ID and status URL.
        
    Raises:
        HTTPException: If path is invalid.
    """
    # Validate path
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
