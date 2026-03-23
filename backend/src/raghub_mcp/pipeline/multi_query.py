"""Multi-Query Generator interface for RAG Pipeline.

This module defines the MultiQueryGenerator abstract base class for
generating multiple query variations to improve retrieval recall.

Multi-query approach improves recall by:
1. Generating variations of the original query
2. Running parallel retrieval for each variation
3. Merging and deduplicating results
4. Returning comprehensive context

Reference:
- Docs/11-V2-Design.md (Section 5: Retrieval设计 - Multi-query)
- Docs/20-RerankEngine-Architecture.md (Quality First原则)
- TODO-V2.md (Phase 5: 8.2 Multi-query)
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any


class QueryGenerationMode(str, Enum):
    """Query generation mode for multi-query."""

    NONE = "none"  # No multi-query (single query only)
    TEMPLATE = "template"  # Template-based variation
    EXPANSION = "expansion"  # Query expansion with synonyms
    LLM = "llm"  # LLM-based generation


@dataclass
class MultiQueryResult:
    """Result of multi-query generation.

    Attributes:
        original_query: The original input query.
        queries: List of generated query variations (includes original).
        mode: The generation mode used.
        metadata: Additional metadata about the generation.
    """

    original_query: str
    queries: list[str]
    mode: QueryGenerationMode
    metadata: dict[str, Any] | None = None

    @property
    def primary_query(self) -> str:
        """Get the primary (first) query."""
        return self.queries[0] if self.queries else self.original_query

    @property
    def variations(self) -> list[str]:
        """Get variations excluding the original query."""
        if len(self.queries) <= 1:
            return []
        return self.queries[1:]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "original_query": self.original_query,
            "queries": self.queries,
            "mode": self.mode.value,
            "metadata": self.metadata,
        }


class MultiQueryGenerator(ABC):
    """Abstract base class for multi-query generators.

    All multi-query generator implementations must inherit from this class
    and implement the generate() method.

    Multi-query generation creates variations of the original query:
    - Template-based: Uses predefined query templates
    - Expansion-based: Adds synonyms/related terms
    - LLM-based: Uses language model for sophisticated variations

    Design Patterns:
    - None: Single query only (no generation)
    - Template: Predefined variations based on query type
    - Expansion: Synonym and related term expansion
    - LLM: Model-based sophisticated variations

    Example:
        >>> class MyGenerator(MultiQueryGenerator):
        ...     async def generate(self, query: str, n: int, **kwargs) -> MultiQueryResult:
        ...         variations = [f"{query} tutorial", f"{query} guide"]
        ...         return MultiQueryResult(
        ...             original_query=query,
        ...             queries=[query] + variations[:n],
        ...             mode=QueryGenerationMode.TEMPLATE
        ...         )
    """

    @abstractmethod
    async def generate(
        self,
        query: str,
        n: int = 3,
        include_original: bool = True,
        options: dict[str, Any] | None = None,
    ) -> MultiQueryResult:
        """Generate query variations.

        Args:
            query: The original search query.
            n: Maximum number of variations to generate.
            include_original: Whether to include the original query in results.
            options: Optional generation options:
                - max_variations: Override for n parameter
                - template_type: Specific template category to use
                - language: Target language for variations

        Returns:
            MultiQueryResult containing original and generated queries.
        """
        pass

    @property
    def name(self) -> str:
        """Get generator name."""
        return self.__class__.__name__

    @property
    def mode(self) -> QueryGenerationMode:
        """Get the generation mode for this generator."""
        return QueryGenerationMode.NONE


class NoOpQueryGenerator(MultiQueryGenerator):
    """No-operation generator that returns only the original query.

    This is the default when multi-query is disabled.
    Simply returns the original query with no variations.

    Example:
        >>> generator = NoOpQueryGenerator()
        >>> result = await generator.generate("machine learning")
        >>> result.queries
        ['machine learning']
    """

    @property
    def mode(self) -> QueryGenerationMode:
        return QueryGenerationMode.NONE

    async def generate(
        self,
        query: str,
        n: int = 3,
        include_original: bool = True,
        options: dict[str, Any] | None = None,
    ) -> MultiQueryResult:
        """Return only the original query.

        Args:
            query: The original search query.
            n: Ignored (no variations generated).
            include_original: Ignored (always returns original).
            options: Ignored.

        Returns:
            MultiQueryResult with only the original query.
        """
        return MultiQueryResult(
            original_query=query,
            queries=[query],
            mode=self.mode,
            metadata={"single_query": True},
        )


class TemplateQueryGenerator(MultiQueryGenerator):
    """Template-based query variation generator.

    Uses predefined templates to create query variations:
    - Clarification templates: "What is X" → ["X definition", "X explained"]
    - How-to templates: "How to X" → ["X tutorial", "X guide", "X steps"]
    - Comparison templates: "X vs Y" → ["X compared to Y", "difference"]
    - Error templates: "X error" → ["X fix", "X debug", "X troubleshooting"]

    Example:
        >>> generator = TemplateQueryGenerator()
        >>> result = await generator.generate("How to use FastAPI", n=5)
        >>> result.queries
        ['How to use FastAPI', 'FastAPI tutorial', 'FastAPI guide', ...]
    """

    # Query templates by type (similar to TemplateRewriter but generates variations)
    QUERY_TEMPLATES: dict[str, dict[str, list[str]]] = {
        "clarification": {
            # "what is X" variations
            "what is": ["{query}", "{term} definition", "{term} explained", "how does {term} work", "{term} meaning"],
            "what are": ["{query}", "{term} definition", "{term} explained", "{term} types"],
            "define": ["{query}", "{term} definition", "what is {term}", "{term} meaning"],
        },
        "howto": {
            # "how to X" variations
            "how to": ["{query}", "{term} tutorial", "{term} guide", "{term} steps", "{term} example"],
            "how do i": ["{query}", "{term} tutorial", "{term} guide", "{term} how to"],
            "how can i": ["{query}", "{term} tutorial", "{term} guide", "{term} how to"],
        },
        "comparison": {
            # "X vs Y" variations
            "vs": ["{query}", "{term1} vs {term2} comparison", "difference between {term1} and {term2}"],
            "versus": ["{query}", "{term1} vs {term2}", "{term1} compared to {term2}"],
            "difference between": ["{query}", "{term1} vs {term2}", "{term1} compared to {term2}"],
        },
        "troubleshooting": {
            # "X not working/ error" variations
            "not working": ["{query}", "{term} fix", "{term} error solution", "{term} troubleshooting", "{term} debug"],
            "error": ["{query}", "{term} error fix", "{term} debug", "{term} troubleshooting"],
            "bug": ["{query}", "{term} bug fix", "{term} issue", "{term} solution"],
        },
    }

    @property
    def mode(self) -> QueryGenerationMode:
        return QueryGenerationMode.TEMPLATE

    async def generate(
        self,
        query: str,
        n: int = 3,
        include_original: bool = True,
        options: dict[str, Any] | None = None,
    ) -> MultiQueryResult:
        """Generate query variations using templates.

        Args:
            query: The original search query.
            n: Maximum variations to generate.
            include_original: Whether to include original in results.
            options: Optional generation options.

        Returns:
            MultiQueryResult with query variations.
        """
        options = options or {}
        max_variations = options.get("max_variations", n)

        variations: list[str] = []

        # Always include original if requested
        if include_original:
            variations.append(query)

        # Find matching template category
        matched_category: str | None = None
        matched_key: str | None = None

        query_lower = query.lower()

        for category, patterns in self.QUERY_TEMPLATES.items():
            for key in patterns:
                if key in query_lower:
                    matched_category = category
                    matched_key = key
                    break
            if matched_category:
                break

        if matched_category and matched_key:
            templates = self.QUERY_TEMPLATES[matched_category][matched_key]

            # Extract the main term from the query
            term = query_lower.replace(matched_key, "").strip()

            # For comparison queries, extract both terms
            terms: tuple[str, str] | None = None
            if matched_category == "comparison":
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
                        variation = template.format(term1=terms[0], term2=terms[1], query=query)
                    elif "{term1}" in template and "{term2}" in template:
                        # Skip if comparison template but terms not extracted
                        continue
                    elif "{term}" in template:
                        variation = template.format(term=term, query=query)
                    else:
                        variation = template.format(query=query)
                except KeyError:
                    continue

                # Avoid duplicates
                if variation not in variations:
                    variations.append(variation)

        metadata = {
            "template_type": matched_category,
            "matched_key": matched_key,
            "num_generated": len(variations) - (1 if include_original else 0),
            "max_variations": max_variations,
            "include_original": include_original,
        }

        return MultiQueryResult(
            original_query=query,
            queries=variations,
            mode=self.mode,
            metadata=metadata,
        )


# Factory function to create generators
def create_multi_query_generator(
    mode: QueryGenerationMode | str = QueryGenerationMode.NONE,
    config: dict[str, Any] | None = None,
) -> MultiQueryGenerator:
    """Create a multi-query generator based on mode.

    Args:
        mode: Generation mode (none, template, expansion, llm).
        config: Optional configuration for the generator.

    Returns:
        MultiQueryGenerator instance.
    """
    config = config or {}

    # Convert string to enum if needed
    if isinstance(mode, str):
        try:
            mode = QueryGenerationMode(mode)
        except ValueError:
            # Unknown mode - default to none
            return NoOpQueryGenerator()

    if mode == QueryGenerationMode.NONE:
        return NoOpQueryGenerator()
    elif mode == QueryGenerationMode.TEMPLATE:
        return TemplateQueryGenerator()
    elif mode == QueryGenerationMode.EXPANSION:
        # TODO: Implement expansion-based generator
        # For now, fall back to template
        return TemplateQueryGenerator()
    elif mode == QueryGenerationMode.LLM:
        # TODO: Implement LLM-based generator
        # Import LLM generator lazily to avoid dependency issues
        try:
            from .llm_multi_query import LLMMultiQueryGenerator

            # mypy doesn't know about LLMMultiQueryGenerator, so we cast it
            generator: MultiQueryGenerator = LLMMultiQueryGenerator(
                provider=config.get("provider"),
                model=config.get("model"),
                max_variations=config.get("max_variations", 3),
            )
            return generator
        except ImportError:
            # Fallback to template if LLM deps not available
            return TemplateQueryGenerator()
    else:
        # Default to no-op
        return NoOpQueryGenerator()