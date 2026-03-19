"""WebSocket manager for real-time progress updates.

This module provides WebSocket connection management and progress broadcasting.
"""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime
from enum import Enum
from typing import Any

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class MessageType(str, Enum):
    """WebSocket message types."""

    PROGRESS = "progress"
    HEARTBEAT = "heartbeat"
    ERROR = "error"
    CONNECTED = "connected"


class ProgressMessage:
    """Progress message structure."""

    def __init__(
        self,
        type: MessageType,
        task_id: str | None = None,
        data: dict[str, Any] | None = None,
        message: str | None = None,
    ):
        self.type = type
        self.task_id = task_id
        self.data = data or {}
        self.message = message
        self.timestamp = datetime.now().isoformat()

    def to_dict(self) -> dict[str, Any]:
        """Convert message to dictionary."""
        result = {
            "type": self.type.value,
            "timestamp": self.timestamp,
        }
        if self.task_id:
            result["task_id"] = self.task_id
        if self.data:
            result["data"] = self.data
        if self.message:
            result["message"] = self.message
        return result

    def to_json(self) -> str:
        """Convert message to JSON string."""
        return json.dumps(self.to_dict())


class ConnectionManager:
    """Manages WebSocket connections for progress updates.

    Each connection subscribes to specific task_id updates.
    """

    def __init__(self):
        # Map of task_id -> list of WebSocket connections
        self._connections: dict[str, list[WebSocket]] = {}
        # Map of WebSocket -> set of subscribed task_ids
        self._subscriptions: dict[WebSocket, set[str]] = {}
        # Lock for thread-safe operations
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, task_id: str) -> None:
        """Accept a new WebSocket connection for a specific task.

        Args:
            websocket: WebSocket connection.
            task_id: Task ID to subscribe to.
        """
        await websocket.accept()

        async with self._lock:
            # Add to connections map
            if task_id not in self._connections:
                self._connections[task_id] = []
            self._connections[task_id].append(websocket)

            # Add to subscriptions map
            if websocket not in self._subscriptions:
                self._subscriptions[websocket] = set()
            self._subscriptions[websocket].add(task_id)

        logger.info(f"WebSocket connected for task: {task_id}")

        # Send connected confirmation
        await self._send_to_websocket(
            websocket,
            ProgressMessage(
                type=MessageType.CONNECTED,
                task_id=task_id,
                message=f"Connected to task {task_id}",
            ),
        )

    async def disconnect(self, websocket: WebSocket) -> None:
        """Remove a WebSocket connection.

        Args:
            websocket: WebSocket connection to remove.
        """
        async with self._lock:
            # Get subscribed task_ids for this connection
            task_ids = self._subscriptions.pop(websocket, set())

            # Remove from connections map
            for task_id in task_ids:
                if task_id in self._connections:
                    try:
                        self._connections[task_id].remove(websocket)
                        # Clean up empty lists
                        if not self._connections[task_id]:
                            del self._connections[task_id]
                    except ValueError:
                        pass

        logger.info(f"WebSocket disconnected")

    async def broadcast_progress(
        self,
        task_id: str,
        status: str,
        progress: float,
        message: str,
        total_files: int = 0,
        processed_files: int = 0,
        total_chunks: int = 0,
        error: str | None = None,
    ) -> None:
        """Broadcast progress update to all connections subscribed to a task.

        Args:
            task_id: Task identifier.
            status: Task status (pending, running, completed, failed).
            progress: Progress value (0.0 - 1.0).
            message: Status message.
            total_files: Total files to process.
            processed_files: Files processed so far.
            total_chunks: Total chunks created.
            error: Error message if failed.
        """
        progress_msg = ProgressMessage(
            type=MessageType.PROGRESS,
            task_id=task_id,
            data={
                "status": status,
                "progress": progress,
                "message": message,
                "total_files": total_files,
                "processed_files": processed_files,
                "total_chunks": total_chunks,
                "error": error,
            },
        )

        await self._broadcast_to_task(task_id, progress_msg)

    async def broadcast_error(self, task_id: str, error_message: str) -> None:
        """Broadcast error message to task subscribers.

        Args:
            task_id: Task identifier.
            error_message: Error message.
        """
        error_msg = ProgressMessage(
            type=MessageType.ERROR,
            task_id=task_id,
            message=error_message,
        )

        await self._broadcast_to_task(task_id, error_msg)

    async def _broadcast_to_task(self, task_id: str, message: ProgressMessage) -> None:
        """Broadcast message to all connections for a task.

        Args:
            task_id: Task identifier.
            message: Message to broadcast.
        """
        async with self._lock:
            connections = self._connections.get(task_id, []).copy()

        if not connections:
            return

        # Send to all connections (don't fail if one is broken)
        for websocket in connections:
            await self._send_to_websocket(websocket, message)

    async def _send_to_websocket(
        self, websocket: WebSocket, message: ProgressMessage
    ) -> bool:
        """Send message to a WebSocket connection.

        Args:
            websocket: WebSocket connection.
            message: Message to send.

        Returns:
            True if sent successfully, False otherwise.
        """
        try:
            await websocket.send_text(message.to_json())
            return True
        except Exception as e:
            logger.warning(f"Failed to send WebSocket message: {e}")
            return False

    async def send_heartbeat(self, websocket: WebSocket) -> None:
        """Send heartbeat message to keep connection alive.

        Args:
            websocket: WebSocket connection.
        """
        heartbeat = ProgressMessage(type=MessageType.HEARTBEAT, message="ping")
        await self._send_to_websocket(websocket, heartbeat)

    def get_connection_count(self, task_id: str | None = None) -> int:
        """Get number of active connections.

        Args:
            task_id: Optional task ID to filter by.

        Returns:
            Number of active connections.
        """
        if task_id:
            return len(self._connections.get(task_id, []))
        return len(self._subscriptions)


# Global connection manager instance
manager = ConnectionManager()