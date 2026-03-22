"""Rerank providers module.

Provides base class for reranking providers and result dataclass.
"""

from .base import BaseRerankProvider, RerankResult

__all__ = ["BaseRerankProvider", "RerankResult"]
