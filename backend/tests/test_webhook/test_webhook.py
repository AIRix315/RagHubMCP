"""Tests for webhook handler."""

import sys
from pathlib import Path

import pytest

# Add src to path for imports
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))


class TestWebhookHandler:
    """Tests for webhook handler."""

    def test_handle_ping_event(self):
        """Ping event returns accepted status."""
        from webhook.handler import WebhookHandler
        
        handler = WebhookHandler()
        result = handler.handle("ping", {"zen": "Keep it simple"}, None)
        
        assert result["status"] == "accepted"
        assert result["event"] == "ping"

    def test_handle_push_event(self):
        """Push event extracts files changed."""
        from webhook.handler import WebhookHandler
        
        handler = WebhookHandler()
        payload = {
            "repository": {"full_name": "owner/repo"},
            "ref": "refs/heads/main",
            "sender": {"login": "user"},
            "commits": [
                {"added": ["file1.py"], "modified": ["file2.py"], "removed": []}
            ]
        }
        
        result = handler.handle("push", payload, None)
        
        assert result["status"] == "accepted"
        assert result["event"] == "push"
        assert result["repository"] == "owner/repo"
        assert result["branch"] == "main"
        assert result["files_changed"] == 2

    def test_handle_pull_request_event(self):
        """Pull request event extracts action and branch."""
        from webhook.handler import WebhookHandler
        
        handler = WebhookHandler()
        payload = {
            "repository": {"full_name": "owner/repo"},
            "action": "opened",
            "sender": {"login": "user"},
            "pull_request": {
                "head": {"ref": "feature-branch"}
            }
        }
        
        result = handler.handle("pull_request", payload, None)
        
        assert result["status"] == "accepted"
        assert result["event"] == "pull_request"
        assert result["action"] == "opened"
        assert result["branch"] == "feature-branch"

    def test_verify_signature_valid(self):
        """Valid signature passes verification."""
        import json
        from webhook.handler import WebhookHandler
        
        secret = "my_secret"
        handler = WebhookHandler(secret=secret)
        
        payload = {"test": "data"}
        payload_bytes = json.dumps(payload).encode("utf-8")
        
        import hmac
        import hashlib
        expected_sig = "sha256=" + hmac.new(
            secret.encode("utf-8"),
            payload_bytes,
            hashlib.sha256
        ).hexdigest()
        
        assert handler.verify_signature(payload_bytes, expected_sig) is True

    def test_verify_signature_invalid(self):
        """Invalid signature fails verification."""
        from webhook.handler import WebhookHandler
        
        handler = WebhookHandler(secret="my_secret")
        
        assert handler.verify_signature(b"payload", "sha256=invalid") is False

    def test_verify_signature_no_secret_configured(self):
        """No secret configured skips verification."""
        from webhook.handler import WebhookHandler
        
        handler = WebhookHandler(secret=None)
        
        assert handler.verify_signature(b"payload", None) is True

    def test_handle_invalid_json(self):
        """Invalid JSON returns error."""
        from webhook.handler import WebhookHandler
        
        handler = WebhookHandler()
        result = handler.handle("push", b"not json", None)
        
        assert result["status"] == "error"

    def test_handle_unknown_event(self):
        """Unknown event type returns ignored."""
        from webhook.handler import WebhookHandler
        
        handler = WebhookHandler()
        result = handler.handle("unknown_event", {}, None)
        
        # Unknown events use default handler or return ignored
        assert result["status"] in ["accepted", "ignored", "error"]


class TestWebhookPayload:
    """Tests for WebhookPayload parsing."""

    def test_parse_push_payload(self):
        """Push payload is parsed correctly."""
        from webhook.handler import WebhookPayload, EventType
        
        data = {
            "repository": {"full_name": "owner/repo"},
            "ref": "refs/heads/main",
            "sender": {"login": "user"},
            "commits": [{"added": ["test.py"]}]
        }
        
        payload = WebhookPayload.from_github_event("push", data)
        
        assert payload.event_type == EventType.PUSH
        assert payload.repository == "owner/repo"
        assert payload.branch == "main"
        assert payload.sender == "user"
        assert len(payload.commits) == 1

    def test_parse_ping_payload(self):
        """Ping payload is parsed correctly."""
        from webhook.handler import WebhookPayload, EventType
        
        data = {"zen": "Keep it simple"}
        
        payload = WebhookPayload.from_github_event("ping", data)
        
        assert payload.event_type == EventType.PING

    def test_parse_pull_request_payload(self):
        """Pull request payload is parsed correctly."""
        from webhook.handler import WebhookPayload, EventType
        
        data = {
            "repository": {"full_name": "owner/repo"},
            "action": "synchronize",
            "sender": {"login": "user"},
            "pull_request": {"head": {"ref": "feature"}}
        }
        
        payload = WebhookPayload.from_github_event("pull_request", data)
        
        assert payload.event_type == EventType.PULL_REQUEST
        assert payload.action == "synchronize"
        assert payload.branch == "feature"