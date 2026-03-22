"""Generic registry module with singleton pattern.

This module provides a reusable Registry base class for registry pattern
implementations across the codebase.
"""

from __future__ import annotations

from typing import Any, Generic, TypeVar

T = TypeVar("T")  # Base class type
K = TypeVar("K")  # Key type


class Registry(Generic[T, K]):
    """Generic registry base class with singleton pattern per subclass.

    Provides a central registration point for classes with singleton management.
    Subclasses define their own registration and lookup APIs.

    Type Parameters:
        T: The base class type that registered items must inherit from
        K: The key type used for grouping registered items

    Each subclass gets its own singleton instance.
    """

    # Per-subclass singleton storage
    _instances: dict[type, Registry[Any, Any]] = {}

    def __new__(cls) -> Registry[Any, Any]:
        """Ensure singleton pattern per subclass."""
        if cls not in cls._instances:
            instance = super().__new__(cls)
            instance._items = {}
            cls._instances[cls] = instance
        return cls._instances[cls]

    def __init__(self) -> None:
        """Initialize registry. Subclasses should call super().__init__()."""
        pass

    def _get_items(self) -> dict[K, dict[str, type[T]]]:
        """Get the internal items dictionary."""
        return self._items  # type: ignore

    def _clear_items(self) -> None:
        """Clear all items from the registry."""
        self._items.clear()
