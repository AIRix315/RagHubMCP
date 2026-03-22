"""WebSocket debug endpoint for real-time Pipeline monitoring.

This module provides WebSocket endpoints for debugging pipeline execution
with real-time progress updates.

Reference: Docs/22-Config-API-Design.md Section 3.2.6
"""

from __future__ import annotations

import asyncio
import json
import logging
import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)

router = APIRouter(tags=["debug"])


class DebugWebSocketHandler:
    """Handles WebSocket connections for pipeline debugging.

    Supports:
    - Subscribe to query updates
    - Execute pipeline with real-time stage progress
    - Push stage completion events
    """

    def __init__(self):
        # Map of query_id -> list of WebSocket connections
        self._subscribers: dict[str, list[WebSocket]] = []
        # Map of WebSocket -> set of subscribed query_ids
        self._subscriptions: dict[WebSocket, set[str]] = {}

    async def connect(self, websocket: WebSocket) -> None:
        """Accept a WebSocket connection.

        Args:
            websocket: WebSocket connection.
        """
        await websocket.accept()
        self._subscriptions[websocket] = set()
        logger.info("WebSocket debug connection established")

    async def disconnect(self, websocket: WebSocket) -> None:
        """Handle WebSocket disconnect.

        Args:
            websocket: WebSocket connection.
        """
        # Remove from all subscriptions
        if websocket in self._subscriptions:
            for query_id in self._subscriptions[websocket]:
                if query_id in self._subscribers:
                    try:
                        self._subscribers[query_id].remove(websocket)
                    except ValueError:
                        pass
            del self._subscriptions[websocket]
        logger.info("WebSocket debug connection closed")

    async def subscribe(self, websocket: WebSocket, query_id: str) -> None:
        """Subscribe a connection to query updates.

        Args:
            websocket: WebSocket connection.
            query_id: Query ID to subscribe to.
        """
        if query_id not in self._subscribers:
            self._subscribers[query_id] = []
        self._subscribers[query_id].append(websocket)
        self._subscriptions[websocket].add(query_id)
        
        await self._send_message(websocket, {
            "event": "subscribed",
            "query_id": query_id,
            "timestamp": datetime.now().isoformat(),
        })

    async def _send_message(self, websocket: WebSocket, data: dict[str, Any]) -> None:
        """Send JSON message to WebSocket.

        Args:
            websocket: WebSocket connection.
            data: Message data.
        """
        try:
            await websocket.send_json(data)
        except Exception as e:
            logger.warning(f"Failed to send WebSocket message: {e}")

    async def broadcast_stage_event(
        self,
        query_id: str,
        stage: str,
        event: str,
        data: dict[str, Any],
    ) -> None:
        """Broadcast stage event to all subscribers.

        Args:
            query_id: Query ID.
            stage: Stage name (retrieval, rerank, context).
            event: Event type (started, progress, completed, error).
            data: Event data.
        """
        message = {
            "query_id": query_id,
            "stage": stage,
            "event": event,
            "data": data,
            "timestamp": datetime.now().isoformat(),
        }

        if query_id in self._subscribers:
            for websocket in self._subscribers[query_id]:
                await self._send_message(websocket, message)

    async def execute_with_streaming(
        self,
        websocket: WebSocket,
        query: str,
        documents: list[str],
        config: dict[str, Any] | None = None,
    ) -> None:
        """Execute pipeline and stream progress updates.

        This simulates a pipeline execution with realistic stage progress.
        In production, this would call the actual RAGPipeline.

        Args:
            websocket: WebSocket connection.
            query: Query string.
            documents: Document list.
            config: Pipeline configuration override.
        """
        query_id = str(uuid.uuid4())[:8]
        config = config or {}
        
        try:
            # Notify start
            await self._send_message(websocket, {
                "event": "started",
                "query_id": query_id,
                "query": query,
                "timestamp": datetime.now().isoformat(),
            })

            # Stage 1: Retrieval
            await self._stream_stage(websocket, query_id, "retrieval", {
                "query": query,
                "top_k": config.get("top_k", 100),
            })

            # Stage 2: Rerank
            await self._stream_stage(websocket, query_id, "rerank", {
                "input_count": len(documents),
            })

            # Stage 3: Context Builder
            await self._stream_stage(websocket, query_id, "context", {
                "input_count": min(len(documents), 10),
            })

            # Notify completion
            await self._send_message(websocket, {
                "event": "completed",
                "query_id": query_id,
                "timestamp": datetime.now().isoformat(),
            })

        except Exception as e:
            logger.error(f"Pipeline execution failed: {e}")
            await self._send_message(websocket, {
                "event": "error",
                "query_id": query_id,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            })

    async def _stream_stage(
        self,
        websocket: WebSocket,
        query_id: str,
        stage_name: str,
        input_data: dict[str, Any],
    ) -> None:
        """Stream stage execution progress.

        Args:
            websocket: WebSocket connection.
            query_id: Query ID.
            stage_name: Stage name.
            input_data: Stage input data.
        """
        import random

        # Stage started
        await self._send_message(websocket, {
            "event": "stage_started",
            "query_id": query_id,
            "stage": stage_name,
            "input": input_data,
            "timestamp": datetime.now().isoformat(),
        })

        # Simulate processing
        await asyncio.sleep(0.1)

        # Stage progress (for rerank, show individual scores)
        if stage_name == "rerank":
            await self._send_message(websocket, {
                "event": "stage_progress",
                "query_id": query_id,
                "stage": stage_name,
                "data": {
                    "message": "Scoring documents...",
                    "processed": 0,
                    "total": input_data.get("input_count", 10),
                },
                "timestamp": datetime.now().isoformat(),
            })

        # Simulate latency
        latency = random.uniform(0.03, 0.08)
        await asyncio.sleep(latency)

        # Stage completed
        output_data = self._get_stage_output(stage_name, input_data)
        await self._send_message(websocket, {
            "event": "stage_completed",
            "query_id": query_id,
            "stage": stage_name,
            "output": output_data,
            "latency_ms": round(latency * 1000, 2),
            "timestamp": datetime.now().isoformat(),
        })

    def _get_stage_output(
        self,
        stage_name: str,
        input_data: dict[str, Any],
    ) -> dict[str, Any]:
        """Get simulated stage output.

        Args:
            stage_name: Stage name.
            input_data: Stage input data.

        Returns:
            Simulated output data.
        """
        import random

        if stage_name == "retrieval":
            return {
                "candidates_count": random.randint(80, 120),
                "vector_candidates": random.randint(50, 80),
                "bm25_candidates": random.randint(30, 50),
            }
        elif stage_name == "rerank":
            input_count = input_data.get("input_count", 10)
            return {
                "ranked_count": min(input_count, 10),
                "top_scores": [round(random.uniform(0.8, 0.98), 4) for _ in range(5)],
                "strategy": "position_aware",
            }
        elif stage_name == "context":
            return {
                "final_count": random.randint(6, 10),
                "dedup_removed": random.randint(1, 3),
                "final_tokens": random.randint(2500, 4000),
            }
        return {}


# Global handler instance
debug_handler = DebugWebSocketHandler()


@router.websocket("/api/debug/ws")
async def websocket_debug_endpoint(websocket: WebSocket) -> None:
    """WebSocket endpoint for real-time pipeline debugging.

    Supports:
    - Subscribe to query updates: {"action": "subscribe", "query_id": "uuid"}
    - Execute pipeline: {"action": "execute", "query": "...", "documents": [...], "config": {...}}

    Server pushes:
    - {"event": "started", "query_id": "...", ...}
    - {"event": "stage_started", "stage": "retrieval", ...}
    - {"event": "stage_progress", "stage": "rerank", "data": {...}}
    - {"event": "stage_completed", "stage": "...", "output": {...}}
    - {"event": "completed", ...}
    """
    await debug_handler.connect(websocket)

    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                action = message.get("action")

                if action == "subscribe":
                    # Subscribe to query updates
                    query_id = message.get("query_id")
                    if query_id:
                        await debug_handler.subscribe(websocket, query_id)
                    else:
                        await websocket.send_json({
                            "event": "error",
                            "message": "Missing query_id for subscribe action",
                        })

                elif action == "execute":
                    # Execute pipeline with streaming
                    query = message.get("query", "")
                    documents = message.get("documents", [])
                    config = message.get("config")

                    if not query:
                        await websocket.send_json({
                            "event": "error",
                            "message": "Missing query for execute action",
                        })
                        continue

                    if not documents:
                        await websocket.send_json({
                            "event": "error",
                            "message": "Missing documents for execute action",
                        })
                        continue

                    await debug_handler.execute_with_streaming(
                        websocket, query, documents, config
                    )

                else:
                    await websocket.send_json({
                        "event": "error",
                        "message": f"Unknown action: {action}",
                    })

            except json.JSONDecodeError:
                await websocket.send_json({
                    "event": "error",
                    "message": "Invalid JSON message",
                })

    except WebSocketDisconnect:
        await debug_handler.disconnect(websocket)