"""CLI module for RagHubMCP."""

from .main import cli, main
from .migrate import main as migrate_main

__all__ = ["cli", "main", "migrate_main"]
