"""Profile Management API endpoints.

This module provides API endpoints for managing and applying
pipeline profiles.

Reference: Docs/22-Config-API-Design.md Section 3.2.5
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from src.config.profiles import (
    Profile,
    ProfileMetadata,
    get_all_profiles,
    get_default_profile,
    get_profile,
)

router = APIRouter(prefix="/profiles", tags=["profiles"])


# =============================================================================
# Current active profile (in-memory for demo)
# =============================================================================

_active_profile: str = "balanced"


# =============================================================================
# Pydantic Models
# =============================================================================


class ProfileSummary(BaseModel):
    """Profile summary for listing."""

    name: str = Field(..., description="Profile name")
    description: str = Field(..., description="Profile description")
    icon: str = Field(..., description="Profile icon")
    is_default: bool = Field(default=False, description="Whether this is the default")
    is_active: bool = Field(default=False, description="Whether this is currently active")


class ProfileDetail(BaseModel):
    """Detailed profile information."""

    name: str
    description: str
    icon: str
    use_cases: list[str]
    expected_latency: str
    expected_quality: str
    is_default: bool
    is_active: bool
    config: dict[str, Any]


class ApplyProfileResponse(BaseModel):
    """Response after applying a profile."""

    name: str = Field(..., description="Applied profile name")
    message: str = Field(..., description="Success message")
    previous_profile: str = Field(..., description="Previously active profile")


# =============================================================================
# API Endpoints
# =============================================================================


@router.get("", response_model=list[ProfileSummary])
async def list_profiles() -> list[ProfileSummary]:
    """List all available profiles.

    Returns:
        List of profile summaries.
    """
    profiles = get_all_profiles()
    return [
        ProfileSummary(
            name=p.metadata.name,
            description=p.metadata.description,
            icon=p.metadata.icon,
            is_default=p.is_default,
            is_active=(p.metadata.name == _active_profile),
        )
        for p in profiles
    ]


@router.get("/{name}", response_model=ProfileDetail)
async def get_profile_detail(name: str) -> ProfileDetail:
    """Get detailed profile information.

    Args:
        name: Profile name (fast, balanced, accurate)

    Returns:
        Detailed profile information.

    Raises:
        HTTPException: 404 if profile not found
    """
    profile = get_profile(name)
    if not profile:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "profile_not_found",
                "message": f"Profile '{name}' not found. Available: fast, balanced, accurate",
            },
        )

    return ProfileDetail(
        name=profile.metadata.name,
        description=profile.metadata.description,
        icon=profile.metadata.icon,
        use_cases=profile.metadata.use_cases,
        expected_latency=profile.metadata.expected_latency,
        expected_quality=profile.metadata.expected_quality,
        is_default=profile.is_default,
        is_active=(profile.metadata.name == _active_profile),
        config=profile.config.model_dump(),
    )


@router.post("/{name}/apply", response_model=ApplyProfileResponse)
async def apply_profile(name: str) -> ApplyProfileResponse:
    """Apply a profile as the active configuration.

    This immediately updates the pipeline configuration to use
    the specified profile's settings.

    Args:
        name: Profile name to apply

    Returns:
        ApplyProfileResponse with the result.

    Raises:
        HTTPException: 404 if profile not found
    """
    global _active_profile

    profile = get_profile(name)
    if not profile:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "profile_not_found",
                "message": f"Profile '{name}' not found. Available: fast, balanced, accurate",
            },
        )

    previous = _active_profile
    _active_profile = name

    return ApplyProfileResponse(
        name=name,
        message=f"已应用 {profile.metadata.description} 配置",
        previous_profile=previous,
    )


@router.get("/active", response_model=ProfileDetail)
async def get_active_profile() -> ProfileDetail:
    """Get the currently active profile.

    Returns:
        Active profile details.
    """
    profile = get_profile(_active_profile) or get_default_profile()
    return ProfileDetail(
        name=profile.metadata.name,
        description=profile.metadata.description,
        icon=profile.metadata.icon,
        use_cases=profile.metadata.use_cases,
        expected_latency=profile.metadata.expected_latency,
        expected_quality=profile.metadata.expected_quality,
        is_default=profile.is_default,
        is_active=True,
        config=profile.config.model_dump(),
    )