"""Query Rewriter interface for RAG Pipeline.

This module defines the QueryRewriter abstract base class for
query preprocessing and rewriting.

Query rewriting improves retrieval quality by:
1. Normalizing queries (lowercase, removing noise)
2. Expanding queries with synonyms/related terms
3. Simplifying complex queries
4. Generating query variations for better recall

Reference:
- Docs/11-V2-Design.md (Section 5: Retrieval设计 - 可选增强)
- Docs/20-RerankEngine-Architecture.md (Quality First原则)
- TODO-V2.md (Phase 5: 8.1 Query Rewrite)
"""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import StrEnum
from typing import Any


class RewriteMode(StrEnum):
    """Query rewriting mode."""

    IDENTITY = "identity"  # No rewriting (passthrough)
    NORMALIZE = "normalize"  # Basic normalization
    EXPAND = "expand"  # Query expansion with synonyms
    TEMPLATE = "template"  # Template-based rewriting
    LLM = "llm"  # LLM-based rewriting (optional)


@dataclass
class RewriteResult:
    """Result of query rewriting.

    Attributes:
        original_query: The original input query.
        rewritten_queries: List of rewritten queries (main + variations).
        mode: The rewriting mode used.
        metadata: Additional metadata about the rewriting.
    """

    original_query: str
    rewritten_queries: list[str]
    mode: RewriteMode
    metadata: dict[str, Any] | None = None

    @property
    def primary_query(self) -> str:
        """Get the primary (first) rewritten query."""
        return self.rewritten_queries[0] if self.rewritten_queries else self.original_query

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "original_query": self.original_query,
            "rewritten_queries": self.rewritten_queries,
            "mode": self.mode.value,
            "metadata": self.metadata,
        }


class QueryRewriter(ABC):
    """Abstract base class for query rewriters.

    All query rewriter implementations must inherit from this class and
    implement the rewrite() method.

    Query rewriting is an optional preprocessing step in the RAG pipeline:
    - Can improve retrieval recall by generating query variations
    - Can normalize queries for more consistent retrieval
    - Can expand queries with synonyms or related terms

    Design Patterns:
    - Identity: Return original query (no rewriting)
    - Normalize: Clean and standardize query
    - Expand: Add synonyms/related terms
    - Template: Use predefined templates
    - LLM: Use language model for sophisticated rewriting

    Example:
        >>> class MyRewriter(QueryRewriter):
        ...     async def rewrite(self, query: str, options: dict) -> RewriteResult:
        ...         rewritten = query.lower().strip()
        ...         return RewriteResult(
        ...             original_query=query,
        ...             rewritten_queries=[rewritten],
        ...             mode=RewriteMode.NORMALIZE
        ...         )
    """

    @abstractmethod
    async def rewrite(
        self,
        query: str,
        options: dict[str, Any] | None = None,
    ) -> RewriteResult:
        """Rewrite a query to improve retrieval quality.

        Args:
            query: The original search query.
            options: Optional rewriting options:
                - mode: Rewrite mode override
                - max_variations: Maximum query variations to generate
                - expand_with_synonyms: Whether to expand with synonyms
                - language: Target language for rewriting

        Returns:
            RewriteResult containing original and rewritten queries.
        """
        pass

    @property
    def name(self) -> str:
        """Get rewriter name."""
        return self.__class__.__name__

    @property
    def mode(self) -> RewriteMode:
        """Get the rewriting mode for this rewriter."""
        return RewriteMode.IDENTITY


class IdentityRewriter(QueryRewriter):
    """Identity rewriter that returns the original query unchanged.

    This is the default rewriter used when query rewriting is disabled.
    It simply passes through the original query.

    Example:
        >>> rewriter = IdentityRewriter()
        >>> result = await rewriter.rewrite("Machine Learning")
        >>> result.rewritten_queries
        ['Machine Learning']
    """

    @property
    def mode(self) -> RewriteMode:
        return RewriteMode.IDENTITY

    async def rewrite(
        self,
        query: str,
        options: dict[str, Any] | None = None,
    ) -> RewriteResult:
        """Return the original query unchanged.

        Args:
            query: The original search query.
            options: Ignored (identity rewriter has no options).

        Returns:
            RewriteResult with only the original query.
        """
        return RewriteResult(
            original_query=query,
            rewritten_queries=[query],
            mode=self.mode,
            metadata={"passthrough": True},
        )


class NormalizeRewriter(QueryRewriter):
    """Query normalizer that cleans and standardizes queries.

    Performs basic text normalization:
    - Convert to lowercase
    - Remove extra whitespace
    - Remove special characters (optional)
    - Remove common stop words from start/end
    - Trim punctuation

    Example:
        >>> rewriter = NormalizeRewriter()
        >>> result = await rewriter.rewrite("  How do I use FastAPI???  ")
        >>> result.primary_query
        'how do i use fastapi'
    """

    # Common English stop words to potentially remove from start/end
    STOP_WORDS = {
        "a",
        "an",
        "the",
        "is",
        "are",
        "was",
        "were",
        "be",
        "been",
        "being",
        "have",
        "has",
        "had",
        "do",
        "does",
        "did",
        "will",
        "would",
        "could",
        "should",
        "may",
        "might",
        "must",
        "shall",
        "can",
        "need",
        "dare",
        "ought",
        "used",
        "i",
        "you",
        "he",
        "she",
        "it",
        "we",
        "they",
        "what",
        "which",
        "who",
        "whom",
        "this",
        "that",
        "these",
        "those",
        "how",
        "why",
        "where",
        "when",
    }

    @property
    def mode(self) -> RewriteMode:
        return RewriteMode.NORMALIZE

    def __init__(
        self,
        lowercase: bool = True,
        remove_stopwords: bool = False,
        remove_punctuation: bool = True,
        min_length: int = 2,
    ):
        """Initialize the normalizer.

        Args:
            lowercase: Whether to convert to lowercase.
            remove_stopwords: Whether to remove stop words from start/end.
            remove_punctuation: Whether to remove punctuation.
            min_length: Minimum query length to keep (after normalization).
        """
        self.lowercase = lowercase
        self.remove_stopwords = remove_stopwords
        self.remove_punctuation = remove_punctuation
        self.min_length = min_length

    async def rewrite(
        self,
        query: str,
        options: dict[str, Any] | None = None,
    ) -> RewriteResult:
        """Normalize the query.

        Args:
            query: The original search query.
            options: Optional normalization options.

        Returns:
            RewriteResult with normalized query.
        """
        options = options or {}

        # Override settings from options
        lowercase = options.get("lowercase", self.lowercase)
        remove_stopwords = options.get("remove_stopwords", self.remove_stopwords)
        remove_punctuation = options.get("remove_punctuation", self.remove_punctuation)

        normalized = query

        # Step 1: Lowercase
        if lowercase:
            normalized = normalized.lower()

        # Step 2: Remove punctuation
        if remove_punctuation:
            normalized = re.sub(r"[^\w\s]", " ", normalized)

        # Step 3: Normalize whitespace
        normalized = " ".join(normalized.split())

        # Step 4: Remove stop words from start/end
        if remove_stopwords:
            words = normalized.split()
            # Remove from start
            while words and words[0] in self.STOP_WORDS:
                words.pop(0)
            # Remove from end
            while words and words[-1] in self.STOP_WORDS:
                words.pop()
            normalized = " ".join(words)

        # Step 5: Check minimum length
        if len(normalized) < self.min_length:
            # Fall back to original if normalized is too short
            normalized = query.strip()

        return RewriteResult(
            original_query=query,
            rewritten_queries=[normalized],
            mode=self.mode,
            metadata={
                "original_length": len(query),
                "normalized_length": len(normalized),
                "lowercase": lowercase,
                "remove_stopwords": remove_stopwords,
                "remove_punctuation": remove_punctuation,
            },
        )


class TemplateRewriter(QueryRewriter):
    """Template-based query rewriter that generates query variations.

    Uses predefined templates to create query variations:
    - Converts questions to different forms
    - Generates topic-focused variations
    - Useful for improving recall without LLM

    Template Categories:
    - clarification: "what is X" → ["X definition", "X explained", "how does X work"]
    - howto: "how to X" → ["X tutorial", "X guide", "X steps"]
    - comparison: "X vs Y" → ["X compared to Y", "difference between X and Y"]
    - troubleshooting: "X not working" → ["X error", "X fix", "X debug"]

    Example:
        >>> rewriter = TemplateRewriter()
        >>> result = await rewriter.rewrite("how to use FastAPI")
        >>> result.rewritten_queries
        ['how to use FastAPI', 'FastAPI tutorial', 'FastAPI guide', 'FastAPI steps']
    """

    # Query templates by type
    TEMPLATES: dict[str, dict[str, list[str]]] = {
        "clarification": {
            # "what is X" template
            "what is": ["{query}", "{term} definition", "{term} explained", "how does {term} work"],
            "what are": ["{query}", "{term} definition", "{term} explained"],
            "what does": ["{query}", "{term} meaning", "what {term} does"],
            # "define X" template
            "define": ["{query}", "{term} definition", "what is {term}"],
        },
        "howto": {
            # "how to X" template
            "how to": [
                "{query}",
                "{term} tutorial",
                "{term} guide",
                "{term} steps",
                "{term} how to",
            ],
            "how do i": ["{query}", "{term} tutorial", "{term} guide"],
            "how can i": ["{query}", "{term} tutorial", "{term} guide"],
        },
        "comparison": {
            # "X vs Y" template
            "vs": [
                "{query}",
                "{term1} compared to {term2}",
                "difference between {term1} and {term2}",
            ],
            "versus": [
                "{query}",
                "{term1} compared to {term2}",
                "difference between {term1} and {term2}",
            ],
            "difference between": ["{query}", "{term1} vs {term2}", "{term1} compared to {term2}"],
        },
        "troubleshooting": {
            # "X not working" template
            "not working": [
                "{query}",
                "{term} error",
                "{term} fix",
                "{term} debug",
                "{term} troubleshooting",
            ],
            "error": ["{query}", "{term} error fix", "{term} debug"],
            "bug": ["{query}", "{term} bug fix", "{term} issue"],
        },
    }

    @property
    def mode(self) -> RewriteMode:
        return RewriteMode.TEMPLATE

    async def rewrite(
        self,
        query: str,
        options: dict[str, Any] | None = None,
    ) -> RewriteResult:
        """Generate query variations using templates.

        Args:
            query: The original search query.
            options: Optional rewrite options:
                - max_variations: Maximum variations to generate (default: 3)
                - include_original: Include original query (default: True)

        Returns:
            RewriteResult with query variations.
        """
        options = options or {}
        max_variations = options.get("max_variations", 3)
        include_original = options.get("include_original", True)

        variations: list[str] = []

        # Always include original if requested
        if include_original:
            variations.append(query)

        # Find matching template categories
        matched_category = None
        matched_key = None

        query_lower = query.lower()

        for category, patterns in self.TEMPLATES.items():
            for key in patterns:
                if key in query_lower:
                    matched_category = category
                    matched_key = key
                    break
            if matched_category:
                break

        if matched_category and matched_key:
            templates = self.TEMPLATES[matched_category][matched_key]

            # Extract the main term from the query
            # Simple extraction: remove the matched key and clean up
            term = query_lower.replace(matched_key, "").strip()

            # For comparison queries, extract both terms
            terms = None
            if matched_category == "comparison":
                # Split on "vs" or "versus" or "and"
                for sep in [" vs ", " versus ", " and "]:
                    if sep in term:
                        parts = term.split(sep)
                        if len(parts) == 2:
                            terms = (parts[0].strip(), parts[1].strip())
                        break

            # Generate variations from templates
            for template in templates:
                if len(variations) >= max_variations + (1 if include_original else 0):
                    break

                try:
                    if "{term1}" in template and "{term2}" in template and terms:
                        # Comparison template with two terms
                        variation = template.format(term1=terms[0], term2=terms[1], query=query)
                    elif "{term1}" in template and "{term2}" in template:
                        # Comparison template but terms extraction failed - skip
                        continue
                    elif "{term}" in template:
                        # Single term template
                        variation = template.format(term=term, query=query)
                    else:
                        # Direct template - needs only {query}
                        variation = template.format(query=query)
                except KeyError:
                    # Skip templates that can't be formatted
                    continue

                # Avoid duplicates
                if variation not in variations:
                    variations.append(variation)

        metadata = {
            "matched_category": matched_category,
            "matched_key": matched_key,
            "num_variations": len(variations),
            "max_variations": max_variations,
            "include_original": include_original,
        }

        return RewriteResult(
            original_query=query,
            rewritten_queries=variations,
            mode=self.mode,
            metadata=metadata,
        )


# Factory function to create rewriters
def create_query_rewriter(
    mode: RewriteMode | str = RewriteMode.IDENTITY,
    config: dict[str, Any] | None = None,
) -> QueryRewriter:
    """Create a query rewriter based on mode.

    Args:
        mode: Rewriting mode (identity, normalize, expand, template, llm).
        config: Optional configuration for the rewriter.

    Returns:
        QueryRewriter instance.
    """
    config = config or {}

    # Convert string to enum if needed
    if isinstance(mode, str):
        try:
            mode = RewriteMode(mode)
        except ValueError:
            # Unknown mode - default to identity
            return IdentityRewriter()

    if mode == RewriteMode.IDENTITY:
        return IdentityRewriter()
    elif mode == RewriteMode.NORMALIZE:
        return NormalizeRewriter(
            lowercase=config.get("lowercase", True),
            remove_stopwords=config.get("remove_stopwords", False),
            remove_punctuation=config.get("remove_punctuation", True),
        )
    elif mode == RewriteMode.TEMPLATE:
        return TemplateRewriter()
    elif mode == RewriteMode.LLM:
        # Import LLM rewriter lazily to avoid dependency issues
        try:
            from .llm_rewrite import LLMRewriter

            # mypy doesn't know about LLMRewriter, so we cast it
            rewriter: QueryRewriter = LLMRewriter(
                provider=config.get("provider"),
                model=config.get("model"),
                max_variations=config.get("max_variations", 3),
            )
            return rewriter
        except ImportError:
            # Fallback to template if LLM deps not available
            return TemplateRewriter()
    else:
        # Default to identity for unknown modes
        return IdentityRewriter()
