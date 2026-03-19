"""CLI module for RagHubMCP."""

from .migrate import main as migrate_main

__all__ = ["migrate_main"]