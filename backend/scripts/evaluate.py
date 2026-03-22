"""RAG Pipeline Evaluation Script.

This script runs evaluation tests against the RAG pipeline using
test questions and measures quality metrics.

Reference:
- Docs/12-V2-Blueprint.md (Section 3: 验证体系)
- TODO-V2.md (Phase 5.7: 实现 evaluate.py 评估脚本)
- RULE.md (Section 7: 测试验收标准)

Usage:
    # Run evaluation with default profile
    python -m backend.scripts.evaluate

    # Run with specific profile
    python -m backend.scripts.evaluate --profile accurate

    # Compare multiple profiles
    python -m backend.scripts.evaluate --compare fast,balanced,accurate

    # Output to file
    python -m backend.scripts.evaluate --output results.json

    # Markdown format
    python -m backend.scripts.evaluate --format markdown --output results.md
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

# Imports - use src/scripts/tests paths relative to backend directory
from src.config.profiles import get_profile
from src.pipeline import Document, RAGResult, get_pipeline
from tests.test_evaluation.metrics import (
    calculate_noise_ratio,
    calculate_relevance_score,
)
from tests.test_evaluation.test_questions import get_test_questions


@dataclass
class EvaluationResult:
    """Result of evaluating a single query.

    Attributes:
        query_id: Query identifier.
        query: Query text.
        profile: Profile used for evaluation.
        documents: Retrieved documents.
        execution_time_ms: Execution time in milliseconds.
        metrics: Calculated metrics for this query.
    """

    query_id: int
    query: str
    profile: str
    documents: list[Document]
    execution_time_ms: float
    metrics: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "query_id": self.query_id,
            "query": self.query,
            "profile": self.profile,
            "documents": [
                {"id": doc.id, "text": doc.text, "score": doc.score, "metadata": doc.metadata}
                for doc in self.documents
            ],
            "execution_time_ms": self.execution_time_ms,
            "metrics": self.metrics,
        }


class EvaluationRunner:
    """Runner for RAG pipeline evaluation.

    This class handles running evaluation queries against the pipeline
    and calculating quality metrics.

    Example:
        >>> runner = EvaluationRunner(profile="balanced")
        >>> result = await runner.run_evaluation()
        >>> print(result["hit_rate"])
    """

    VALID_PROFILES = ("fast", "balanced", "accurate")

    def __init__(self, profile: str = "balanced", top_k: int = 10):
        """Initialize evaluation runner.

        Args:
            profile: Profile name to use for evaluation.
            top_k: Number of results to retrieve.

        Raises:
            ValueError: If profile is invalid.
        """
        if profile not in self.VALID_PROFILES:
            raise ValueError(
                f"Invalid profile '{profile}'. Must be one of: {self.VALID_PROFILES}"
            )
        self.profile = profile
        self.top_k = top_k
        self._pipeline = None

    async def _get_pipeline(self):
        """Get or create pipeline instance."""
        if self._pipeline is None:
            self._pipeline = await get_pipeline()
        return self._pipeline

    async def run_single_query(self, question: str) -> RAGResult:
        """Run a single query through the pipeline.

        Args:
            question: Question text to query.

        Returns:
            RAGResult from the pipeline.
        """
        pipeline = await self._get_pipeline()

        result = await pipeline.run(
            query=question,
            options={
                "topK": self.top_k,
                "rerank": True,
                "profile": self.profile,
            },
        )

        return result

    async def run_evaluation(
        self,
        queries: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Run evaluation on test questions.

        Args:
            queries: Optional list of test questions. If None, uses default test set.

        Returns:
            Dictionary with evaluation results.
        """
        if queries is None:
            queries = get_test_questions()

        results: list[EvaluationResult] = []

        for query_data in queries:
            query_id = query_data.get("id")
            question = query_data.get("question", "")
            keywords = query_data.get("keywords", [])

            # Run query
            rag_result = await self.run_single_query(question)

            # Calculate metrics
            relevance = calculate_relevance_score(
                [{"text": d.text} for d in rag_result.documents],
                keywords,
            )
            noise = calculate_noise_ratio(
                [{"text": d.text} for d in rag_result.documents],
                keywords,
            )

            # Create result
            eval_result = EvaluationResult(
                query_id=query_id,
                query=question,
                profile=self.profile,
                documents=rag_result.documents,
                execution_time_ms=rag_result.execution_time_ms,
                metrics={
                    "relevance_score": relevance,
                    "noise_ratio": noise,
                    "document_count": len(rag_result.documents),
                },
            )
            results.append(eval_result)

        # Calculate aggregate metrics
        aggregate = self.calculate_aggregate_metrics(results, queries)

        return {
            "profile": self.profile,
            "top_k": self.top_k,
            "total_queries": len(queries),
            "timestamp": datetime.now().isoformat(),
            "aggregate_metrics": aggregate,
            "query_results": [r.to_dict() for r in results],
        }

    def calculate_aggregate_metrics(
        self,
        results: list[EvaluationResult],
        queries: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Calculate aggregate metrics across all results.

        Args:
            results: List of evaluation results.
            queries: Original test questions.

        Returns:
            Dictionary with aggregate metrics.
        """
        if not results:
            return {
                "avg_relevance_score": 0.0,
                "avg_noise_ratio": 0.0,
                "avg_execution_time_ms": 0.0,
            }

        total_relevance = sum(r.metrics.get("relevance_score", 0) for r in results)
        total_noise = sum(r.metrics.get("noise_ratio", 0) for r in results)
        total_time = sum(r.execution_time_ms for r in results)

        return {
            "avg_relevance_score": round(total_relevance / len(results), 4),
            "avg_noise_ratio": round(total_noise / len(results), 4),
            "avg_execution_time_ms": round(total_time / len(results), 2),
        }

    def calculate_metrics(
        self,
        queries: list[dict[str, Any]],
        results: dict[int, list[Document]],
    ) -> dict[str, Any]:
        """Calculate metrics for given results.

        Args:
            queries: List of test questions with keywords.
            results: Dictionary mapping query ID to retrieved documents.

        Returns:
            Dictionary with calculated metrics.
        """
        total_queries = len(queries)

        if total_queries == 0:
            return {
                "total_queries": 0,
                "hit_rate": 0.0,
                "avg_relevance_score": 0.0,
                "noise_ratio": 0.0,
            }

        total_relevance = 0.0
        total_noise = 0.0

        for query in queries:
            qid = query.get("id")
            keywords = query.get("keywords", [])
            retrieved = results.get(qid, [])

            # Calculate relevance and noise
            relevance = calculate_relevance_score(
                [{"text": d.text} for d in retrieved],
                keywords,
            )
            noise = calculate_noise_ratio(
                [{"text": d.text} for d in retrieved],
                keywords,
            )

            total_relevance += relevance
            total_noise += noise

        return {
            "total_queries": total_queries,
            "hit_rate": 0.0,  # Would need ground truth for actual hit rate
            "avg_relevance_score": round(total_relevance / total_queries, 4),
            "noise_ratio": round(total_noise / total_queries, 4),
        }

    def format_output(
        self,
        results: dict[str, Any],
        format: str = "json",
    ) -> str:
        """Format evaluation results for output.

        Args:
            results: Evaluation results dictionary.
            format: Output format (json or markdown).

        Returns:
            Formatted string.
        """
        if format == "json":
            return json.dumps(results, indent=2, ensure_ascii=False)

        elif format == "markdown":
            return self._format_markdown(results)

        else:
            return json.dumps(results, indent=2)

    def _format_markdown(self, results: dict[str, Any]) -> str:
        """Format results as Markdown.

        Args:
            results: Evaluation results dictionary.

        Returns:
            Markdown formatted string.
        """
        md = ["# Evaluation Results\n"]
        md.append(f"**Profile**: {results.get('profile', 'N/A')}")
        md.append(f"**Top K**: {results.get('top_k', 'N/A')}")
        md.append(f"**Total Queries**: {results.get('total_queries', 0)}")
        md.append(f"**Timestamp**: {results.get('timestamp', 'N/A')}\n")

        # Aggregate metrics
        agg = results.get("aggregate_metrics", {})
        md.append("## Aggregate Metrics\n")
        md.append("| Metric | Value |")
        md.append("|--------|-------|")
        md.append(f"| Average Relevance Score | {agg.get('avg_relevance_score', 0):.4f} |")
        md.append(f"| Average Noise Ratio | {agg.get('avg_noise_ratio', 0):.4f} |")
        md.append(f"| Average Execution Time | {agg.get('avg_execution_time_ms', 0):.2f} ms |\n")

        # Query results
        query_results = results.get("query_results", [])
        if query_results:
            md.append("## Query Results\n")
            md.append("| ID | Query | Docs | Relevance | Noise | Time (ms) |")
            md.append("|----|-------|------|-----------|-------|-----------|")

            for qr in query_results:
                md.append(
                    f"| {qr['query_id']} | "
                    f"{qr['query'][:40]}... | "
                    f"{qr['metrics']['document_count']} | "
                    f"{qr['metrics']['relevance_score']:.4f} | "
                    f"{qr['metrics']['noise_ratio']:.4f} | "
                    f"{qr['execution_time_ms']:.2f} |"
                )

        return "\n".join(md)

    def write_output(
        self,
        results: dict[str, Any],
        output_path: Path,
        format: str = "json",
    ) -> None:
        """Write results to file.

        Args:
            results: Evaluation results dictionary.
            output_path: Path to output file.
            format: Output format.
        """
        content = self.format_output(results, format)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(content, encoding="utf-8")


async def compare_profiles(
    profiles: list[str] = None,
    top_k: int = 10,
    output_file: Path | None = None,
    format: str = "json",
) -> dict[str, Any]:
    """Compare evaluation results across multiple profiles.

    Args:
        profiles: List of profile names to compare.
        top_k: Number of results to retrieve.
        output_file: Optional output file path.
        format: Output format.

    Returns:
        Dictionary with comparison results.
    """
    if profiles is None:
        profiles = ["fast", "balanced", "accurate"]

    results = {}

    for profile in profiles:
        runner = EvaluationRunner(profile=profile, top_k=top_k)
        result = await runner.run_evaluation()
        results[profile] = result

    # Format comparison output
    comparison = {
        "timestamp": datetime.now().isoformat(),
        "profiles_compared": profiles,
        "results": results,
    }

    if output_file:
        runner = EvaluationRunner(profile=profiles[0])
        runner.write_output(comparison, output_file, format)

    return comparison


def parse_args():
    """Parse command line arguments.

    Returns:
        Parsed arguments namespace.
    """
    parser = argparse.ArgumentParser(
        description="Run RAG pipeline evaluation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Run evaluation with default settings
    python -m backend.scripts.evaluate

    # Use specific profile
    python -m backend.scripts.evaluate --profile accurate

    # Compare all profiles
    python -m backend.scripts.evaluate --compare fast,balanced,accurate

    # Save results to file
    python -m backend.scripts.evaluate --output results.json

    # Markdown format
    python -m backend.scripts.evaluate --format markdown --output results.md
        """,
    )

    parser.add_argument(
        "--profile",
        type=str,
        default="balanced",
        choices=["fast", "balanced", "accurate"],
        help="Profile to use for evaluation (default: balanced)",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=10,
        help="Number of results to retrieve (default: 10)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output file path (default: stdout)",
    )
    parser.add_argument(
        "--format",
        type=str,
        default="json",
        choices=["json", "markdown"],
        help="Output format (default: json)",
    )
    parser.add_argument(
        "--compare",
        type=str,
        default=None,
        help="Comma-separated list of profiles to compare (e.g., fast,balanced,accurate)",
    )

    return parser.parse_args()


async def main():
    """Main entry point for evaluation script."""
    args = parse_args()

    # Handle comparison mode
    if args.compare:
        profiles = [p.strip() for p in args.compare.split(",")]
        print(f"Comparing profiles: {profiles}")

        results = await compare_profiles(
            profiles=profiles,
            top_k=args.top_k,
            output_file=Path(args.output) if args.output else None,
            format=args.format,
        )
    else:
        # Single profile evaluation
        print(f"Running evaluation with profile: {args.profile}")
        print(f"Top K: {args.top_k}")

        runner = EvaluationRunner(profile=args.profile, top_k=args.top_k)
        results = await runner.run_evaluation()

    # Output results
    output_content = runner.format_output(results, args.format) if args.compare else \
        EvaluationRunner(profile=args.profile).format_output(results, args.format)

    if args.output:
        output_path = Path(args.output)
        (runner if not args.compare else EvaluationRunner(args.profile)).write_output(
            results, output_path, args.format
        )
        print(f"Results written to: {output_path}")
    else:
        print(output_content)

    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))