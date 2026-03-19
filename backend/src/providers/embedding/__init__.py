"""Embedding providers module.

Provides base class for embedding providers and exports common types.
"""

from .base import BaseEmbeddingProvider
from .ollama import OllamaEmbeddingProvider

__all__ = ["BaseEmbeddingProvider", "OllamaEmbeddingProvider"]