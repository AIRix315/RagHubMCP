"""Common error handling utilities for MCP tools.

This module provides unified error response functions to reduce
code duplication across MCP tool implementations.

Reference:
- Docs/11-V2-Desing.md (RULE-2: 所有模块必须接口化)
- Docs/12-V2-Blueprint.md (Module 5)
"""

from __future__ import annotations

import json
from typing import Any


def error_response(
    message: str,
    **kwargs: Any,
) -> str:
    """Create a standardized JSON error response.
    
    Args:
        message: Error message to include.
        **kwargs: Additional fields to include in the response.
        
    Returns:
        JSON string with error information.
    
    Example:
        >>> error_response("collection_name must be a non-empty string", results=[], count=0)
        '{"error": "collection_name must be a non-empty string", "results": [], "count": 0}'
    """
    result = {"error": message, **kwargs}
    return json.dumps(result, indent=2)


def validate_collection_name(name: Any) -> str | None:
    """Validate collection name.
    
    Args:
        name: Collection name to validate.
        
    Returns:
        Error message if invalid, None if valid.
    
    Example:
        >>> validate_collection_name("")
        'collection_name must be a non-empty string'
        >>> validate_collection_name("valid_name")
        None
    """
    if not name or not isinstance(name, str):
        return "collection_name must be a non-empty string"
    return None


def validate_query(query: Any) -> str | None:
    """Validate query string.
    
    Args:
        query: Query string to validate.
        
    Returns:
        Error message if invalid, None if valid.
    """
    if not query or not isinstance(query, str):
        return "query must be a non-empty string"
    return None


def validate_documents(documents: Any) -> str | None:
    """Validate documents list.
    
    Args:
        documents: Documents list to validate.
        
    Returns:
        Error message if invalid, None if valid.
    """
    if not documents or not isinstance(documents, list):
        return "documents must be a non-empty list"
    return None


def validate_positive_int(value: Any, field_name: str) -> str | None:
    """Validate positive integer.
    
    Args:
        value: Value to validate.
        field_name: Field name for error message.
        
    Returns:
        Error message if invalid, None if valid.
    """
    if value is not None and (not isinstance(value, int) or value <= 0):
        return f"{field_name} must be a positive integer"
    return None


def validate_range(value: Any, field_name: str, min_val: float, max_val: float) -> str | None:
    """Validate numeric value is within range.
    
    Args:
        value: Value to validate.
        field_name: Field name for error message.
        min_val: Minimum allowed value.
        max_val: Maximum allowed value.
        
    Returns:
        Error message if invalid, None if valid.
    """
    if value is not None and not (min_val <= value <= max_val):
        return f"{field_name} must be between {min_val} and {max_val}"
    return None


def success_response(
    message: str = "Operation completed successfully",
    **kwargs: Any,
) -> str:
    """Create a standardized JSON success response.
    
    Args:
        message: Success message to include.
        **kwargs: Additional fields to include in the response.
        
    Returns:
        JSON string with success information.
    """
    result = {"status": "success", "message": message, **kwargs}
    return json.dumps(result, indent=2)