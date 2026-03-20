"""Pipeline module for RagHubMCP V2.

This module provides the unified RAG Pipeline architecture:
- RAGPipeline: Abstract base class for all pipelines
- DefaultRAGPipeline: Default implementation with HybridSearch + Rerank
- PipelineFactory: Configuration-driven pipeline creation
- Retriever: Interface for document retrieval
- Reranker: Interface for document reranking
- ContextBuilder: Interface for context construction

Reference:
- Docs/11-V2-Desing.md
- Docs/12-V2-Blueprint.md
- RULE.md
"""

from .base import RAGPipeline
from .result import RAGResult, Document
from .default import DefaultRAGPipeline
from .factory import PipelineFactory
from .retriever import Retriever, HybridRetriever
from .reranker import PipelineReranker
from .context_builder import ContextBuilder, DefaultContextBuilder

__all__ = [
    "RAGPipeline",
    "RAGResult",
    "Document",
    "DefaultRAGPipeline",
    "PipelineFactory",
    "Retriever",
    "HybridRetriever",
    "PipelineReranker",
    "ContextBuilder",
    "DefaultContextBuilder",
]