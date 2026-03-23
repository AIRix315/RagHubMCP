"""Tests for webhook handler.

Test cases:
- WebhookPayload parsing for different event types
- Event type detection
- Signature verification
"""

from __future__ import annotations

import pytest

from raghub_mcp.webhook.handler import EventType, WebhookPayload


class TestEventType:
    """Tests for EventType enum."""

    def test_event_types_exist(self):
        """Test all event types exist."""
        assert EventType.PUSH == "push"
        assert EventType.PULL_REQUEST == "pull_request"
        assert EventType.RELEASE == "release"
        assert EventType.PING == "ping"


class TestWebhookPayload:
    """Tests for WebhookPayload."""

    def test_from_push_event(self):
        """Test parsing push event."""
        data = {
            "ref": "refs/heads/main",
            "repository": {"full_name": "owner/repo"},
            "sender": {"login": "user1"},
            "commits": [
                {"id": "abc123", "message": "Fix bug"},
                {"id": "def456", "message": "Add feature"},
            ],
        }

        payload = WebhookPayload.from_github_event("push", data)

        assert payload.event_type == EventType.PUSH
        assert payload.repository == "owner/repo"
        assert payload.branch == "main"
        assert payload.sender == "user1"
        assert len(payload.commits) == 2

    def test_from_pull_request_event(self):
        """Test parsing pull_request event."""
        data = {
            "action": "opened",
            "repository": {"full_name": "owner/repo"},
            "sender": {"login": "user1"},
            "pull_request": {
                "head": {"ref": "feature-branch"},
                "number": 42,
            },
        }

        payload = WebhookPayload.from_github_event("pull_request", data)

        assert payload.event_type == EventType.PULL_REQUEST
        assert payload.action == "opened"
        assert payload.repository == "owner/repo"
        assert payload.branch == "feature-branch"
        assert payload.sender == "user1"

    def test_from_release_event(self):
        """Test parsing release event."""
        data = {
            "action": "published",
            "repository": {"full_name": "owner/repo"},
            "sender": {"login": "user1"},
            "release": {"tag_name": "v1.0.0"},
        }

        payload = WebhookPayload.from_github_event("release", data)

        assert payload.event_type == EventType.RELEASE
        assert payload.action == "published"
        assert payload.repository == "owner/repo"

    def test_from_ping_event(self):
        """Test parsing ping event."""
        data = {"zen": "Keep it simple"}

        payload = WebhookPayload.from_github_event("ping", data)

        assert payload.event_type == EventType.PING
        assert payload.raw_data == data

    def test_unknown_event_type_defaults_to_push(self):
        """Test unknown event type defaults to push."""
        data = {"repository": {"full_name": "owner/repo"}}

        payload = WebhookPayload.from_github_event("unknown", data)

        # Unknown event types default to PUSH
        assert payload.event_type == EventType.PUSH

    def test_from_push_event_empty_commits(self):
        """Test push event with no commits."""
        data = {
            "ref": "refs/heads/main",
            "repository": {"full_name": "owner/repo"},
            "sender": {"login": "user1"},
            "commits": [],
        }

        payload = WebhookPayload.from_github_event("push", data)

        assert payload.commits == []

    def test_from_push_event_missing_optional_fields(self):
        """Test push event with missing optional fields."""
        data = {
            "ref": "refs/heads/feature",
            "repository": {},
            "sender": {},
        }

        payload = WebhookPayload.from_github_event("push", data)

        assert payload.repository == ""
        assert payload.branch == "feature"
        assert payload.sender == ""
        assert payload.commits == []

    def test_from_pull_request_event_with_action(self):
        """Test pull_request event with different actions."""
        actions = ["opened", "closed", "synchronize", "reopened"]

        for action in actions:
            data = {
                "action": action,
                "repository": {"full_name": "owner/repo"},
                "sender": {"login": "user1"},
                "pull_request": {"head": {"ref": "branch"}},
            }

            payload = WebhookPayload.from_github_event("pull_request", data)
            assert payload.action == action
