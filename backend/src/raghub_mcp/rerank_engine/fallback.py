"""Fallback manager for provider graceful degradation.

This module provides automatic fallback from API providers to local
ONNX models when API calls fail, ensuring continuous service availability.

Reference: Docs/20-RerankEngine-Architecture.md Section 4.4
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class ProviderStatus(Enum):
    """Provider health status."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    FAILED = "failed"


@dataclass
class ProviderHealth:
    """Provider health information."""

    name: str
    status: ProviderStatus
    last_success: float | None = None
    last_failure: float | None = None
    consecutive_failures: int = 0
    total_requests: int = 0
    total_failures: int = 0


class FallbackManager:
    """Manages provider fallback with circuit breaker pattern.

    Automatically falls back from API providers to local ONNX when
    failures are detected, with automatic recovery.

    Attributes:
        failure_threshold: Number of failures before fallback.
        recovery_timeout: Seconds before attempting recovery.
        fallback_provider: Name of fallback provider (e.g., "onnx-minilm").

    Example:
        >>> manager = FallbackManager(failure_threshold=3, recovery_timeout=60)
        >>> manager.record_success("cohere")
        >>> manager.record_failure("cohere", "API timeout")
        >>> provider = manager.get_provider("cohere")  # Returns fallback if failed
    """

    def __init__(
        self,
        failure_threshold: int = 3,
        recovery_timeout: float = 60.0,
        fallback_provider: str = "onnx-minilm",
    ) -> None:
        """Initialize fallback manager.

        Args:
            failure_threshold: Consecutive failures before fallback.
            recovery_timeout: Seconds before attempting provider recovery.
            fallback_provider: Default fallback provider name.
        """
        self._failure_threshold = failure_threshold
        self._recovery_timeout = recovery_timeout
        self._fallback_provider = fallback_provider
        self._health: dict[str, ProviderHealth] = {}
        self._lock_timeout = 0.1  # Lock acquisition timeout

    def get_provider(self, primary: str) -> str:
        """Get provider to use, with fallback support.

        Args:
            primary: Primary provider name.

        Returns:
            Provider name to use (primary if healthy, fallback if not).
        """
        health = self._health.get(primary)

        if health is None:
            # Unknown provider, use as-is
            return primary

        if health.status == ProviderStatus.HEALTHY:
            return primary

        if health.status == ProviderStatus.DEGRADED:
            # Check if recovery is possible
            if self._can_recover(health):
                logger.info(f"Provider {primary} recovering, attempting use")
                return primary

        # Use fallback
        logger.warning(
            f"Provider {primary} is {health.status.value}, using fallback {self._fallback_provider}"
        )
        return self._fallback_provider

    def record_success(self, provider: str) -> None:
        """Record successful provider call.

        Args:
            provider: Provider name.
        """
        if provider not in self._health:
            self._health[provider] = ProviderHealth(
                name=provider,
                status=ProviderStatus.HEALTHY,
            )

        health = self._health[provider]
        health.last_success = time.time()
        health.consecutive_failures = 0
        health.total_requests += 1

        # Reset to healthy if was degraded
        if health.status == ProviderStatus.DEGRADED:
            health.status = ProviderStatus.HEALTHY
            logger.info(f"Provider {provider} recovered, status: HEALTHY")

    def record_failure(self, provider: str, error: str) -> None:
        """Record failed provider call.

        Args:
            provider: Provider name.
            error: Error message.
        """
        if provider not in self._health:
            self._health[provider] = ProviderHealth(
                name=provider,
                status=ProviderStatus.HEALTHY,
            )

        health = self._health[provider]
        health.last_failure = time.time()
        health.consecutive_failures += 1
        health.total_requests += 1
        health.total_failures += 1

        # Check if should transition to failed
        if health.consecutive_failures >= self._failure_threshold:
            if health.status != ProviderStatus.FAILED:
                health.status = ProviderStatus.FAILED
                logger.warning(
                    f"Provider {provider} marked as FAILED after "
                    f"{health.consecutive_failures} consecutive failures: {error}"
                )
        elif health.consecutive_failures >= 1:
            if health.status != ProviderStatus.DEGRADED:
                health.status = ProviderStatus.DEGRADED
                logger.warning(f"Provider {provider} marked as DEGRADED: {error}")

    def _can_recover(self, health: ProviderHealth) -> bool:
        """Check if provider can attempt recovery.

        Args:
            health: Provider health record.

        Returns:
            True if enough time has passed for recovery attempt.
        """
        if health.last_failure is None:
            return True

        elapsed = time.time() - health.last_failure
        return elapsed >= self._recovery_timeout

    def get_health(self, provider: str) -> ProviderHealth | None:
        """Get provider health status.

        Args:
            provider: Provider name.

        Returns:
            Provider health or None if not tracked.
        """
        return self._health.get(provider)

    def get_all_health(self) -> dict[str, ProviderHealth]:
        """Get all provider health statuses.

        Returns:
            Dictionary of provider name to health.
        """
        return self._health.copy()

    def reset(self, provider: str | None = None) -> None:
        """Reset provider health status.

        Args:
            provider: Provider name, or None to reset all.
        """
        if provider:
            if provider in self._health:
                del self._health[provider]
                logger.info(f"Reset health tracking for {provider}")
        else:
            self._health.clear()
            logger.info("Reset all provider health tracking")

    def get_fallback_stats(self) -> dict[str, Any]:
        """Get fallback statistics.

        Returns:
            Dictionary with fallback stats.
        """
        provider_stats: dict[str, dict[str, Any]] = {}

        for name, health in self._health.items():
            failure_rate = (
                health.total_failures / health.total_requests if health.total_requests > 0 else 0.0
            )
            provider_stats[name] = {
                "status": health.status.value,
                "consecutive_failures": health.consecutive_failures,
                "total_requests": health.total_requests,
                "total_failures": health.total_failures,
                "failure_rate": failure_rate,
                "last_success": health.last_success,
                "last_failure": health.last_failure,
            }

        stats: dict[str, Any] = {
            "failure_threshold": self._failure_threshold,
            "recovery_timeout": self._fallback_provider,
            "fallback_provider": self._fallback_provider,
            "providers": provider_stats,
        }

        return stats


# Global fallback manager instance
_fallback_manager: FallbackManager | None = None


def get_fallback_manager() -> FallbackManager:
    """Get global fallback manager instance.

    Returns:
        Global FallbackManager instance.
    """
    global _fallback_manager
    if _fallback_manager is None:
        _fallback_manager = FallbackManager()
    return _fallback_manager


def reset_fallback_manager() -> None:
    """Reset global fallback manager instance."""
    global _fallback_manager
    _fallback_manager = None
