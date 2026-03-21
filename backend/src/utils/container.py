"""Dependency injection container for RagHubMCP.

This module provides a simple dependency injection container
to manage singleton instances and their lifecycle.

Reference:
- Docs/11-V2-Desing.md (RULE-3: 禁止直接依赖具体实现)
- RULE.md (所有能力必须可配置)
"""

from __future__ import annotations

import threading
from collections.abc import Callable
from typing import Any, TypeVar

T = TypeVar("T")


class Container:
    """Simple dependency injection container with singleton support.

    This container manages singleton instances and their creation,
    providing a central place for dependency management.

    Example:
        >>> container = Container()
        >>> container.registerSingleton('config', lambda: load_config())
        >>> config = container.get('config')
    """

    def __init__(self) -> None:
        """Initialize the container."""
        self._singletons: dict[str, Any] = {}
        self._factories: dict[str, Callable[[], Any]] = {}
        self._lock = threading.Lock()

    def register_singleton(self, name: str, factory: Callable[[], T]) -> None:
        """Register a singleton factory.

        Args:
            name: Unique identifier for the dependency.
            factory: Factory function that creates the instance.
        """
        with self._lock:
            self._factories[name] = factory
            # Clear any existing singleton
            if name in self._singletons:
                del self._singletons[name]

    def register_transient(self, name: str, factory: Callable[[], T]) -> None:
        """Register a transient factory (new instance each time).

        Args:
            name: Unique identifier for the dependency.
            factory: Factory function that creates the instance.
        """
        with self._lock:
            self._factories[name] = factory

    def get(self, name: str) -> Any:
        """Get a dependency.

        Args:
            name: Unique identifier for the dependency.

        Returns:
            The dependency instance.

        Raises:
            KeyError: If dependency is not registered.
        """
        with self._lock:
            # Check if it's a singleton
            if name in self._singletons:
                return self._singletons[name]

            # Check if it's a registered factory
            if name not in self._factories:
                raise KeyError(f"Dependency '{name}' is not registered")

            factory = self._factories[name]

            # Create and cache if it's a singleton (factory without 'transient' prefix)
            if not name.startswith("_transient_"):
                instance = factory()
                self._singletons[name] = instance
                return instance

            # Transient - create new instance each time
            return factory()

    def reset(self, name: str | None = None) -> None:
        """Reset singleton instances.

        Args:
            name: If provided, reset only that singleton.
                  If None, reset all singletons.
        """
        with self._lock:
            if name is None:
                self._singletons.clear()
            elif name in self._singletons:
                del self._singletons[name]


# Global container instance
_container: Container | None = None


def get_container() -> Container:
    """Get the global container instance.

    Returns:
        The global Container instance.
    """
    global _container
    if _container is None:
        _container = Container()
        _setup_defaults(_container)
    return _container


def reset_container() -> None:
    """Reset the global container (useful for testing)."""
    global _container
    _container = None


def _setup_defaults(container: Container) -> None:
    """Setup default dependencies in the container.

    Args:
        container: Container to setup.
    """
    from src.utils.config import load_config

    # Register configuration as singleton
    container.register_singleton("config", lambda: load_config())


# =============================================================================
# Dependency Injection Decorator
# =============================================================================


def injectable(name: str | None = None, singleton: bool = True):
    """Decorator to mark a class as injectable.

    Args:
        name: Optional custom name for the dependency.
        singleton: Whether to create a singleton (default: True).

    Example:
        @injectable('my_service')
        class MyService:
            def __init__(self):
                self.value = 42
    """

    def decorator(cls: type[T]) -> type[T]:
        container = get_container()
        if singleton:
            container.register_singleton(name or cls.__name__, lambda: cls())
        else:
            container.register_transient(name or cls.__name__, lambda: cls())
        return cls

    return decorator


def inject(name: str | None = None):
    """Decorator to inject a dependency into a function or class.

    Args:
        name: Optional custom name for the dependency.

    Example:
        @inject('config')
        def my_function(config):
            return config.get('server')
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        def wrapper(*args: Any, **kwargs: Any) -> T:
            container = get_container()
            dep_name = name or func.__name__
            dep = container.get(dep_name)
            return func(dep, *args, **kwargs)

        return wrapper

    return decorator
