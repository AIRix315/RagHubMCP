"""Singleton decorator for RagHubMCP.

This module provides thread-safe singleton implementations:
- @singleton: Basic singleton decorator (not thread-safe)
- @threadsafe_singleton: Thread-safe singleton decorator
- SingletonMeta: Metaclass for thread-safe singletons

Reference:
- RULE.md (RULE-2: 所有模块必须接口化)
"""

from __future__ import annotations

import threading
from functools import wraps
from typing import TypeVar

T = TypeVar('T')


# =============================================================================
# Basic Singleton (Not Thread-Safe)
# =============================================================================

def singleton(cls: type[T]) -> type[T]:
    """Decorator that ensures only one instance of a class exists.
    
    NOTE: This decorator is NOT thread-safe. Use @threadsafe_singleton
    for classes that may be accessed from multiple threads.
    
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
    - get_instance(): Static method to get the singleton instance
    - reset(): Static method to reset the singleton (for testing)
    
    Args:
        cls: The class to decorate.
        
    Returns:
        The decorated class with singleton behavior.
        
    Example:
        @singleton
        class CacheService:
            def __init__(self, cache_dir: str) -> None:
                self.cache_dir = cache_dir
        
        # Get the singleton instance
        cache1 = CacheService.get_instance("./cache")
        cache2 = CacheService.get_instance("./cache")
        assert cache1 is cache2  # Same instance
        
        # Reset for testing
        CacheService.reset()
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


# =============================================================================
# Thread-Safe Singleton
# =============================================================================

class SingletonMeta(type):
    """Thread-safe singleton metaclass.
    
    This metaclass ensures that only one instance of a class exists,
    with thread-safe initialization using a lock.
    
    Example:
        class MyService(metaclass=SingletonMeta):
            def __init__(self, config: str) -> None:
                self.config = config
        
        # Thread-safe: only one instance is created even with concurrent calls
        service1 = MyService.get_instance("config1")
        service2 = MyService.get_instance("config1")
        assert service1 is service2
    """
    
    _instances: dict[type, object] = {}
    _lock: threading.Lock = threading.Lock()
    
    def __call__(cls, *args: any, **kwargs: any) -> object:
        """Create or return the singleton instance (thread-safe)."""
        if cls not in cls._instances:
            with cls._lock:
                # Double-check locking pattern
                if cls not in cls._instances:
                    instance = super().__call__(*args, **kwargs)
                    cls._instances[cls] = instance
        return cls._instances[cls]
    
    def get_instance(cls, *args: any, **kwargs: any) -> object:
        """Get the singleton instance (thread-safe).
        
        Args:
            *args: Constructor arguments (used only on first call)
            **kwargs: Constructor keyword arguments (used only on first call)
            
        Returns:
            The singleton instance.
        """
        return cls(*args, **kwargs)
    
    def reset(cls) -> None:
        """Reset the singleton instance (for testing)."""
        with cls._lock:
            if cls in cls._instances:
                del cls._instances[cls]


def threadsafe_singleton(cls: type[T]) -> type[T]:
    """Thread-safe singleton decorator.
    
    This decorator ensures thread-safe singleton initialization
    using a lock and double-check pattern.
    
    Args:
        cls: The class to decorate.
        
    Returns:
        The decorated class with thread-safe singleton behavior.
        
    Example:
        @threadsafe_singleton
        class ProviderFactory:
            _lock = threading.Lock()
            _cache: dict[str, object] = {}
            
            def __init__(self) -> None:
                pass
        
        # Thread-safe access
        factory1 = ProviderFactory.get_instance()
        factory2 = ProviderFactory.get_instance()
        assert factory1 is factory2
    """
    _instance: T | None = None
    _lock = threading.Lock()
    
    @wraps(cls)
    def get_instance(*args: any, **kwargs: any) -> T:  # type: ignore
        nonlocal _instance
        if _instance is None:
            with _lock:
                # Double-check pattern
                if _instance is None:
                    _instance = cls(*args, **kwargs)  # type: ignore
        return _instance
    
    def reset() -> None:
        """Reset the singleton instance (for testing)."""
        nonlocal _instance
        with _lock:
            _instance = None
    
    # Attach methods to the class
    cls.get_instance = staticmethod(get_instance)  # type: ignore
    cls.reset = staticmethod(reset)  # type: ignore
    cls._singleton_instance = None  # type: ignore
    cls._singleton_lock = _lock  # type: ignore
    
    return cls


# =============================================================================
# Helper Functions
# =============================================================================

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
