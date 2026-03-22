"""Webhook handler for GitHub integration.

Handles GitHub webhooks for:
- Push events: Trigger re-indexing
- Pull request events: Index changed files
- Release events: Update documentation
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class EventType(str, Enum):
    """Supported GitHub webhook event types."""

    PUSH = "push"
    PULL_REQUEST = "pull_request"
    RELEASE = "release"
    PING = "ping"


@dataclass
class WebhookPayload:
    """Parsed webhook payload data."""

    event_type: EventType
    action: str | None = None
    repository: str = ""
    branch: str = ""
    sender: str = ""
    commits: list[dict[str, Any]] = field(default_factory=list)
    raw_data: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_github_event(cls, event_type: str, data: dict[str, Any]) -> WebhookPayload:
        """Parse GitHub webhook payload.

        Args:
            event_type: X-GitHub-Event header value
            data: JSON payload

        Returns:
            Parsed WebhookPayload
        """
        try:
            event = EventType(event_type)
        except ValueError:
            event = EventType.PUSH  # Default

        if event == EventType.PING:
            return cls(event_type=event, raw_data=data)

        repo = data.get("repository", {})
        repo_name = repo.get("full_name", "")

        if event == EventType.PUSH:
            ref = data.get("ref", "")
            branch = ref.replace("refs/heads/", "") if ref else ""

            return cls(
                event_type=event,
                repository=repo_name,
                branch=branch,
                sender=data.get("sender", {}).get("login", ""),
                commits=data.get("commits", []),
                raw_data=data,
            )

        elif event == EventType.PULL_REQUEST:
            pr = data.get("pull_request", {})

            return cls(
                event_type=event,
                action=data.get("action"),
                repository=repo_name,
                branch=pr.get("head", {}).get("ref", ""),
                sender=data.get("sender", {}).get("login", ""),
                raw_data=data,
            )

        elif event == EventType.RELEASE:
            return cls(
                event_type=event,
                action=data.get("action"),
                repository=repo_name,
                sender=data.get("sender", {}).get("login", ""),
                raw_data=data,
            )

        return cls(event_type=event, raw_data=data)


class WebhookHandler:
    """Handles GitHub webhook events.

    Example:
        >>> handler = WebhookHandler(secret="my_webhook_secret")
        >>> result = handler.handle(event_type, payload_body, signature)
    """

    def __init__(self, secret: str | None = None):
        """Initialize webhook handler.

        Args:
            secret: Webhook secret for signature verification
        """
        self.secret = secret
        self._handlers: dict[EventType, callable] = {}

        # Register default handlers
        self._handlers[EventType.PUSH] = self._handle_push
        self._handlers[EventType.PULL_REQUEST] = self._handle_pull_request
        self._handlers[EventType.RELEASE] = self._handle_release
        self._handlers[EventType.PING] = self._handle_ping

    def verify_signature(self, payload_body: bytes, signature_header: str | None) -> bool:
        """Verify GitHub webhook HMAC-SHA256 signature.

        Args:
            payload_body: Raw request body bytes
            signature_header: X-Hub-Signature-256 header value

        Returns:
            True if signature is valid
        """
        if not self.secret:
            logger.warning("No webhook secret configured, skipping verification")
            return True

        if not signature_header:
            logger.warning("Missing signature header")
            return False

        expected_signature = (
            "sha256="
            + hmac.new(
                self.secret.encode("utf-8"), msg=payload_body, digestmod=hashlib.sha256
            ).hexdigest()
        )

        return hmac.compare_digest(expected_signature, signature_header)

    def handle(
        self,
        event_type: str,
        payload_body: bytes | str | dict,
        signature: str | None = None,
    ) -> dict[str, Any]:
        """Handle a webhook event.

        Args:
            event_type: X-GitHub-Event header value
            payload_body: Request body (bytes, string, or dict)
            signature: X-Hub-Signature-256 header value

        Returns:
            Response dict with status and message
        """
        # Parse payload
        if isinstance(payload_body, bytes):
            raw_body = payload_body
            try:
                data = json.loads(payload_body.decode("utf-8"))
            except json.JSONDecodeError:
                return {"status": "error", "message": "Invalid JSON payload"}
        elif isinstance(payload_body, str):
            raw_body = payload_body.encode("utf-8")
            try:
                data = json.loads(payload_body)
            except json.JSONDecodeError:
                return {"status": "error", "message": "Invalid JSON payload"}
        else:
            data = payload_body
            raw_body = json.dumps(data).encode("utf-8")

        # Verify signature
        if self.secret and not self.verify_signature(raw_body, signature):
            return {"status": "error", "message": "Invalid signature"}

        # Parse event
        try:
            payload = WebhookPayload.from_github_event(event_type, data)
        except Exception as e:
            logger.error(f"Failed to parse webhook payload: {e}")
            return {"status": "error", "message": f"Failed to parse payload: {e}"}

        # Dispatch to handler
        handler = self._handlers.get(payload.event_type)
        if handler:
            try:
                return handler(payload)
            except Exception as e:
                logger.error(f"Handler error: {e}")
                return {"status": "error", "message": f"Handler error: {e}"}

        return {"status": "ignored", "message": f"No handler for event: {event_type}"}

    def _handle_push(self, payload: WebhookPayload) -> dict[str, Any]:
        """Handle push event - trigger re-indexing."""
        commits = payload.commits
        files_changed = set()

        for commit in commits:
            files_changed.update(commit.get("added", []))
            files_changed.update(commit.get("modified", []))
            files_changed.update(commit.get("removed", []))

        logger.info(
            f"Push to {payload.repository}/{payload.branch} "
            f"by {payload.sender}: {len(files_changed)} files changed"
        )

        return {
            "status": "accepted",
            "event": "push",
            "repository": payload.repository,
            "branch": payload.branch,
            "files_changed": len(files_changed),
            "action": "index_triggered",
        }

    def _handle_pull_request(self, payload: WebhookPayload) -> dict[str, Any]:
        """Handle pull request event."""
        action = payload.action
        logger.info(
            f"Pull request {action} on {payload.repository} "
            f"branch {payload.branch} by {payload.sender}"
        )

        return {
            "status": "accepted",
            "event": "pull_request",
            "action": action,
            "repository": payload.repository,
            "branch": payload.branch,
        }

    def _handle_release(self, payload: WebhookPayload) -> dict[str, Any]:
        """Handle release event."""
        logger.info(f"Release {payload.action} on {payload.repository} by {payload.sender}")

        return {
            "status": "accepted",
            "event": "release",
            "action": payload.action,
            "repository": payload.repository,
        }

    def _handle_ping(self, payload: WebhookPayload) -> dict[str, Any]:
        """Handle ping event - just acknowledge."""
        return {
            "status": "accepted",
            "event": "ping",
            "message": "Webhook received successfully",
        }

    def register_handler(self, event_type: EventType, handler: callable) -> None:
        """Register a custom handler for an event type.

        Args:
            event_type: Event type to handle
            handler: Handler function (takes WebhookPayload, returns dict)
        """
        self._handlers[event_type] = handler


# FastAPI integration (optional)
def create_webhook_router(handler: WebhookHandler):
    """Create FastAPI router for webhook endpoint.

    Args:
        handler: WebhookHandler instance

    Returns:
        FastAPI APIRouter
    """
    try:
        from fastapi import APIRouter, BackgroundTasks, Header, HTTPException, Request
    except ImportError:
        raise ImportError("FastAPI is required for create_webhook_router")

    router = APIRouter(prefix="/webhook", tags=["webhooks"])

    @router.post("/github")
    async def github_webhook(
        request: Request,
        background_tasks: BackgroundTasks,
        x_github_event: str | None = Header(None),
        x_hub_signature_256: str | None = Header(None),
        x_github_delivery: str | None = Header(None),
    ):
        """Handle GitHub webhook.

        GitHub requires a response within 10 seconds.
        We verify signature, then process in background.
        """
        # Get raw body for signature verification
        payload_body = await request.body()

        if not x_github_event:
            raise HTTPException(status_code=400, detail="Missing X-GitHub-Event header")

        # Process webhook (can be done in background for slow operations)
        result = handler.handle(
            event_type=x_github_event,
            payload_body=payload_body,
            signature=x_hub_signature_256,
        )

        if result["status"] == "error":
            raise HTTPException(status_code=400, detail=result["message"])

        return result

    return router
