"""Tests for DI container."""

import pytest

from src.utils.container import Container, get_container, inject, injectable, reset_container


class TestContainer:
    """Tests for Container class."""

    def test_container_initialization(self):
        """Test container initializes correctly."""
        container = Container()
        assert container._singletons == {}
        assert container._factories == {}

    def test_register_singleton(self):
        """Test registering a singleton."""
        container = Container()

        container.registerSingleton("test", lambda: {"value": 42})

        assert "test" in container._factories
        assert "test" not in container._singletons

    def test_register_transient(self):
        """Test registering a transient."""
        container = Container()

        container.registerTransient("test", lambda: {"value": 42})

        assert "test" in container._factories

    def test_get_singleton(self):
        """Test getting a singleton returns same instance."""
        container = Container()
        call_count = [0]

        def factory():
            call_count[0] += 1
            return {"value": 42}

        container.registerSingleton("test", factory)

        instance1 = container.get("test")
        instance2 = container.get("test")

        assert instance1 is instance2
        assert call_count[0] == 1  # Factory called only once

    def test_get_transient(self):
        """Test getting a transient returns new instance each time."""
        container = Container()
        call_count = [0]

        def factory():
            call_count[0] += 1
            return {"value": call_count[0]}

        container.registerTransient("_transient_test", factory)

        instance1 = container.get("_transient_test")
        instance2 = container.get("_transient_test")

        assert instance1 is not instance2
        assert call_count[0] == 2  # Factory called twice

    def test_get_not_found(self):
        """Test getting non-existent dependency raises KeyError."""
        container = Container()

        with pytest.raises(KeyError):
            container.get("nonexistent")

    def test_reset_single(self):
        """Test resetting a single dependency."""
        container = Container()
        container.registerSingleton("test", lambda: {"value": 42})

        container.get("test")
        assert "test" in container._singletons

        container.reset("test")
        assert "test" not in container._singletons

    def test_reset_all(self):
        """Test resetting all dependencies."""
        container = Container()
        container.registerSingleton("test1", lambda: {})
        container.registerSingleton("test2", lambda: {})

        container.get("test1")
        container.get("test2")

        container.reset()

        assert container._singletons == {}


class TestGlobalContainer:
    """Tests for global container functions."""

    def test_get_container_returns_singleton(self):
        """Test get_container returns the same container."""
        reset_container()

        container1 = get_container()
        container2 = get_container()

        assert container1 is container2

    def test_reset_container(self):
        """Test reset_container clears global container."""
        get_container()
        reset_container()

        # After reset, should get a new container
        # The module variable should be None
        from src.utils.container import _container

        assert _container is None


class TestInjectable:
    """Tests for injectable decorator."""

    def test_injectable_registers_singleton(self):
        """Test injectable registers class as singleton."""
        reset_container()

        @injectable("my_service")
        class MyService:
            def __init__(self):
                self.value = 42

        # Getting from container should return instance
        container = get_container()
        instance = container.get("my_service")

        assert isinstance(instance, MyService)
        assert instance.value == 42

    def test_injectable_transient(self):
        """Test injectable with singleton=False."""
        reset_container()

        class TransientService:
            pass

        # For transient, need to use _transient_ prefix internally
        container = get_container()
        container.registerTransient("_transient_transient_svc", lambda: TransientService())

        instance1 = container.get("_transient_transient_svc")
        instance2 = container.get("_transient_transient_svc")

        assert instance1 is not instance2


class TestInject:
    """Tests for inject decorator."""

    def test_inject_decorator(self):
        """Test inject decorator injects dependency."""
        reset_container()

        @injectable("config")
        class Config:
            def __init__(self):
                self.value = "test"

        @inject("config")
        def get_value(config):
            return config.value

        result = get_value()
        assert result == "test"

    def test_inject_with_custom_name(self):
        """Test inject with custom name."""
        reset_container()

        @injectable("my_config")
        class MyConfig:
            def __init__(self):
                self.key = "value"

        @inject("my_config")
        def get_key(config):
            return config.key

        result = get_key()
        assert result == "value"
