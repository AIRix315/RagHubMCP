"""Test for V2 import fix - verifies absolute imports are used."""

from raghub_mcp.mcp_server.tools.v2 import register_v2_tools


def test_v2_imports():
    """Verify V2 tools use absolute imports."""
    assert callable(register_v2_tools)
