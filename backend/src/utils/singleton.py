"""Singleton decorator for RagHubMCP.

This module provides a simple @singleton decorator to ensure only one
instance of a class exists throughout the application lifecycle.

Reference:
- RULE.md (RULE-2: 所有模块必须接口化)
"""

from __future__ import annotations

from functools import wraps
from typing import TypeVar

T = TypeVar('T')


def singleton(cls: type[T]) -> type[T]:
    """Decorator that ensures only one instance of a class exists.
    
    This decorator replaces the common pattern of:
    ```python
    _instance: MyClass | None = None
    
    def get_my_class() -> MyClass:
        global _instance
        if _instance is None:
            _instance = MyClass()
        return _instance
    
    def reset_my_class() -> None:
        global _instance
        _instance = None
    ```
    
    With a simple:
    ```python
    @singleton
    class MyClass:
        pass
    ```
    
    The decorated class gains:
    - _instance: Class-level instance storage
    - get_instance(): Static method to get the singleton instance
    - reset(): Instance method to reset the singleton (for testing)
    
    Args:
        cls: The class to decorate.
        
    Returns:
        The decorated class with singleton behavior.
        
    Example:
        @singleton
        class ChromaService:
            def __init__(self, persist_dir: str) -> None:
                self.persist_dir = persist_dir
        
        # Get the singleton instance
        service1 = ChromaService.get_instance("./data")
        service2 = ChromaService.get_instance("./data")
        assert service1 is service2  # Same instance
        
        # Reset for testing
        ChromaService.reset()
    """
    _instance: T | None = None
    
    @wraps(cls)
    def get_instance(*args: any, **kwargs: any) -> T:  # type: ignore
        nonlocal _instance
        if _instance is None:
            _instance = cls(*args, **kwargs)  # type: ignore
        return _instance
    
    def reset() -> None:
        """Reset the singleton instance (for testing)."""
        nonlocal _instance
        _instance = None
    
    # Attach methods to the class
    cls.get_instance = staticmethod(get_instance)  # type: ignore
    cls.reset = staticmethod(reset)  # type: ignore
    cls._singleton_instance = None  # type: ignore
    
    return cls


def reset_singleton(cls: type[T]) -> None:
    """Reset a singleton instance.
    
    Args:
        cls: The class with singleton decorator to reset.
        
    Example:
        @singleton
        class MyService:
            pass
        
        service = MyService.get_instance()
        reset_singleton(MyService)  # _instance = None
    """
    if hasattr(cls, 'reset'):
        cls.reset()
    elif hasattr(cls, '_singleton_instance'):
        cls._singleton_instance = None  # type: ignore
