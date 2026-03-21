"""Webhook module for GitHub integration."""

from src.webhook.handler import EventType, WebhookHandler, WebhookPayload

__all__ = ["WebhookHandler", "WebhookPayload", "EventType"]
