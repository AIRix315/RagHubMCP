"""Tests for storage module."""

from __future__ import annotations

import pytest

# Storage module is currently empty, just verify it imports
from raghub_mcp.storage import __all__


class TestStorageModule:
    """Tests for storage module."""

    def test_module_imports(self):
        """Test that storage module can be imported."""
        # Storage module is currently minimal
        assert __all__ == [] or __all__ is None
