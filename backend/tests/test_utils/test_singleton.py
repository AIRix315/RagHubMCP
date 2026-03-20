"""Tests for singleton decorator."""

import pytest
from src.utils.singleton import singleton, reset_singleton


@singleton
class SampleService:
    """Sample service using singleton decorator."""
    
    def __init__(self, value: str = "default") -> None:
        self.value = value
        self.initialized = True


class TestSingletonDecorator:
    """Test cases for @singleton decorator."""
    
    def test_singleton_returns_same_instance(self) -> None:
        """Test that get_instance returns the same instance."""
        # Reset first
        SampleService.reset()
        
        instance1 = SampleService.get_instance()
        instance2 = SampleService.get_instance()
        
        assert instance1 is instance2
    
    def test_singleton_preserves_init_args(self) -> None:
        """Test that init arguments are preserved."""
        # Reset first
        SampleService.reset()
        
        instance = SampleService.get_instance("test_value")
        
        assert instance.value == "test_value"
        assert instance.initialized is True
    
    def test_singleton_default_args(self) -> None:
        """Test singleton with default arguments."""
        # Reset first
        SampleService.reset()
        
        instance = SampleService.get_instance()
        
        assert instance.value == "default"
    
    def test_reset_clears_instance(self) -> None:
        """Test that reset clears the singleton instance."""
        # Reset first
        SampleService.reset()
        
        instance1 = SampleService.get_instance("value1")
        assert instance1.value == "value1"
        
        # Reset
        SampleService.reset()
        
        # New instance should be created
        instance2 = SampleService.get_instance("value2")
        assert instance2.value == "value2"
        
        # They should be different instances
        assert instance1 is not instance2
    
    def test_reset_singleton_function(self) -> None:
        """Test reset_singleton function."""
        # Reset first
        SampleService.reset()
        
        instance1 = SampleService.get_instance()
        
        reset_singleton(SampleService)
        
        instance2 = SampleService.get_instance()
        
        assert instance1 is not instance2


# Non-decorated class for comparison
class NonSingletonService:
    """Service without singleton decorator."""
    
    def __init__(self, value: str = "default") -> None:
        self.value = value


class TestNonSingletonComparison:
    """Verify non-singleton behavior for comparison."""
    
    def test_non_singleton_creates_new_instances(self) -> None:
        """Test that non-decorated class creates new instances each time."""
        instance1 = NonSingletonService("value1")
        instance2 = NonSingletonService("value2")
        
        assert instance1 is not instance2
        assert instance1.value == "value1"
        assert instance2.value == "value2"
        
        # They should be different instances
        assert instance1 is not instance2
    
    def test_reset_singleton_function(self) -> None:
        """Test reset_singleton function."""
        # Reset first
        TestService.reset()
        
        instance1 = TestService.get_instance()
        
        reset_singleton(TestService)
        
        instance2 = TestService.get_instance()
        
        assert instance1 is not instance2


# Non-decorated class for comparison
class NonSingletonService:
    """Service without singleton decorator."""
    
    def __init__(self, value: str = "default") -> None:
        self.value = value


class TestNonSingletonComparison:
    """Verify non-singleton behavior for comparison."""
    
    def test_non_singleton_creates_new_instances(self) -> None:
        """Test that non-decorated class creates new instances each time."""
        instance1 = NonSingletonService("value1")
        instance2 = NonSingletonService("value2")
        
        assert instance1 is not instance2
        assert instance1.value == "value1"
        assert instance2.value == "value2"
