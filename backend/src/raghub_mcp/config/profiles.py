"""Profile configuration system for RAG Pipeline.

This module defines pipeline profiles (fast, balanced, accurate) that
provide pre-configured settings for different use cases.

Reference: Docs/22-Config-API-Design.md Section 2.3.2
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class RetrievalProfileConfig(BaseModel):
    """Retrieval stage profile configuration."""

    top_k: int = Field(default=100, description="Initial retrieval count")
    hybrid_enabled: bool = Field(default=True, description="Enable hybrid search")
    vector_weight: float = Field(default=0.7, ge=0.0, le=1.0, description="Vector weight")


class RerankProfileConfig(BaseModel):
    """Rerank stage profile configuration."""

    enabled: bool = Field(default=True, description="Enable rerank")
    provider: str = Field(default="onnx-minilm", description="Rerank provider")
    top_k: int = Field(default=10, description="Rerank result count")
    score_threshold: float = Field(default=0.3, ge=0.0, le=1.0, description="Score threshold")
    strategy: str = Field(default="standard", description="Rank strategy")


class ContextProfileConfig(BaseModel):
    """Context builder profile configuration."""

    enabled: bool = Field(default=True, description="Enable context builder")
    max_tokens: int = Field(default=4000, description="Maximum tokens")
    deduplicate: bool = Field(default=True, description="Enable deduplication")
    deduplication_threshold: float = Field(default=0.9, ge=0.5, le=1.0, description="Dedup threshold")
    merge_continuous: bool = Field(default=True, description="Merge continuous chunks")


class PipelineProfileConfig(BaseModel):
    """Complete pipeline profile configuration."""

    retrieval: RetrievalProfileConfig = Field(default_factory=RetrievalProfileConfig)
    rerank: RerankProfileConfig = Field(default_factory=RerankProfileConfig)
    context: ContextProfileConfig = Field(default_factory=ContextProfileConfig)


class ProfileMetadata(BaseModel):
    """Profile metadata and description."""

    name: str = Field(..., description="Profile name")
    description: str = Field(..., description="Profile description")
    icon: str = Field(default="⚡", description="Profile icon")
    use_cases: list[str] = Field(default_factory=list, description="Recommended use cases")
    expected_latency: str = Field(default="<150ms", description="Expected latency")
    expected_quality: str = Field(default="85%", description="Expected quality")


class Profile(BaseModel):
    """Complete profile with metadata and configuration."""

    metadata: ProfileMetadata
    config: PipelineProfileConfig
    is_default: bool = Field(default=False, description="Whether this is the default profile")


# =============================================================================
# Pre-defined Profiles
# =============================================================================

PROFILES: dict[str, Profile] = {
    "fast": Profile(
        metadata=ProfileMetadata(
            name="fast",
            description="快速响应，适合实时场景",
            icon="⚡",
            use_cases=["开发调试", "快速验证", "资源受限设备"],
            expected_latency="<50ms",
            expected_quality="70%",
        ),
        config=PipelineProfileConfig(
            retrieval=RetrievalProfileConfig(
                top_k=50,
                hybrid_enabled=False,  # Skip BM25 for speed
                vector_weight=1.0,
            ),
            rerank=RerankProfileConfig(
                enabled=True,
                provider="onnx-tiny",  # Smallest model
                top_k=5,
                score_threshold=0.2,  # Lenient
                strategy="standard",
            ),
            context=ContextProfileConfig(
                enabled=True,
                max_tokens=2000,
                deduplicate=False,  # Skip dedup for speed
                merge_continuous=True,
            ),
        ),
        is_default=False,
    ),
    "balanced": Profile(
        metadata=ProfileMetadata(
            name="balanced",
            description="速度与质量的最佳平衡",
            icon="⚖️",
            use_cases=["日常使用", "团队协作", "大多数场景"],
            expected_latency="<150ms",
            expected_quality="85%",
        ),
        config=PipelineProfileConfig(
            retrieval=RetrievalProfileConfig(
                top_k=100,
                hybrid_enabled=True,
                vector_weight=0.7,
            ),
            rerank=RerankProfileConfig(
                enabled=True,
                provider="onnx-minilm",
                top_k=10,
                score_threshold=0.3,
                strategy="standard",
            ),
            context=ContextProfileConfig(
                enabled=True,
                max_tokens=4000,
                deduplicate=True,
                deduplication_threshold=0.9,
                merge_continuous=True,
            ),
        ),
        is_default=True,  # Default profile
    ),
    "accurate": Profile(
        metadata=ProfileMetadata(
            name="accurate",
            description="追求最高质量，适合复杂查询",
            icon="🎯",
            use_cases=["生产环境", "关键业务", "复杂查询"],
            expected_latency="<500ms",
            expected_quality="92%",
        ),
        config=PipelineProfileConfig(
            retrieval=RetrievalProfileConfig(
                top_k=200,
                hybrid_enabled=True,
                vector_weight=0.8,  # More semantic
            ),
            rerank=RerankProfileConfig(
                enabled=True,
                provider="onnx-minilm",
                top_k=5,  # Stricter selection
                score_threshold=0.5,  # Higher threshold
                strategy="position_aware",  # Advanced strategy
            ),
            context=ContextProfileConfig(
                enabled=True,
                max_tokens=6000,
                deduplicate=True,
                deduplication_threshold=0.95,  # Stricter dedup
                merge_continuous=True,
            ),
        ),
        is_default=False,
    ),
}


def get_profile(name: str) -> Profile | None:
    """Get a profile by name.

    Args:
        name: Profile name (fast, balanced, accurate)

    Returns:
        Profile if found, None otherwise
    """
    return PROFILES.get(name)


def get_all_profiles() -> list[Profile]:
    """Get all available profiles.

    Returns:
        List of all profiles
    """
    return list(PROFILES.values())


def get_default_profile() -> Profile:
    """Get the default profile.

    Returns:
        Default profile (balanced)
    """
    for profile in PROFILES.values():
        if profile.is_default:
            return profile
    return PROFILES["balanced"]  # Fallback