"""Configuration management REST API endpoints.

This module provides endpoints for viewing and updating server configuration.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import yaml
from fastapi import APIRouter, HTTPException

from src.utils.config import (
    AppConfig,
    get_config,
    reload_config,
)

from .schemas import (
    ConfigModel,
    ConfigUpdateRequest,
    ErrorResponse,
    SuccessResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/config", tags=["config"])


def _merge_config(base: dict[str, Any], update: dict[str, Any] | None) -> dict[str, Any]:
    """Deep merge update into base dictionary.

    Args:
        base: Base dictionary.
        update: Update dictionary (can be None).

    Returns:
        Merged dictionary.
    """
    if update is None:
        return base

    result = base.copy()
    for key, value in update.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _merge_config(result[key], value)
        else:
            result[key] = value
    return result


@router.get(
    "",
    response_model=ConfigModel,
    summary="Get current configuration",
    description="Returns the current server configuration loaded from config.yaml",
)
async def get_current_config() -> AppConfig:
    """Get the current server configuration.

    TC-1.15.1: GET /api/config returns configuration

    Returns:
        Current configuration as AppConfig (ConfigModel alias).
    """
    return get_config()


@router.put(
    "",
    response_model=SuccessResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid configuration"},
        500: {"model": ErrorResponse, "description": "Failed to save configuration"},
    },
    summary="Update configuration",
    description="Updates the server configuration and writes it back to config.yaml",
)
async def update_config(request: ConfigUpdateRequest) -> SuccessResponse:
    """Update server configuration.

    TC-1.15.2: PUT /api/config updates configuration

    Args:
        request: Configuration update request.

    Returns:
        Success response.

    Raises:
        HTTPException: If configuration update fails.
    """
    try:
        # Get current config as dict
        config = get_config()
        current_dict = config.model_dump()

        # Merge updates
        update_data = request.model_dump(exclude_none=True)
        updated_dict = _merge_config(current_dict, update_data)

        # Find config file path
        config_path = Path("config.yaml")
        if not config_path.is_absolute():
            backend_path = Path(__file__).parent.parent.parent.parent / "config.yaml"
            if backend_path.exists():
                config_path = backend_path

        # Write to YAML file
        with open(config_path, "w", encoding="utf-8") as f:
            yaml.dump(updated_dict, f, default_flow_style=False, allow_unicode=True)

        # Reload configuration
        reload_config(str(config_path))

        logger.info(f"Configuration updated and saved to {config_path}")

        return SuccessResponse(
            status="success",
            message="Configuration updated successfully",
        )

    except Exception as e:
        logger.error(f"Failed to update configuration: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "config_update_failed",
                "message": f"Failed to update configuration: {str(e)}",
            },
        )
