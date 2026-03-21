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


def validate_collection_name_strict(name: Any) -> str | None:
    """Validate collection name strictly.
    
    Args:
        name: Collection name to validate.
        
    Returns:
        Error message if invalid, None if valid.
    """
    import re
    
    COLLECTION_NAME_PATTERN = re.compile(r'^[a-zA-Z0-9_-]+$')
    MAX_COLLECTION_NAME_LENGTH = 128
    
    if not name or not isinstance(name, str):
        return "collection_name must be a non-empty string"
    
    name = name.strip()
    if not name:
        return "collection_name must not be empty or whitespace"
    
    if not COLLECTION_NAME_PATTERN.match(name):
        return f"Invalid collection name '{name}'. Must contain only alphanumeric characters, underscores, or hyphens."
    
    if len(name) > MAX_COLLECTION_NAME_LENGTH:
        return f"Collection name too long. Maximum {MAX_COLLECTION_NAME_LENGTH} characters, got {len(name)}."
    
    return None


def validate_documents_list(documents: Any, max_count: int = 1000) -> str | None:
    """Validate documents list.
    
    Args:
        documents: Documents list to validate.
        max_count: Maximum number of documents allowed.
        
    Returns:
        Error message if invalid, None if valid.
    """
    if not documents or not isinstance(documents, list):
        return "documents must be a non-empty list"
    
    if len(documents) > max_count:
        return f"Too many documents. Maximum is {max_count}, got {len(documents)}"
    
    return None


def validate_int_range(value: Any, field_name: str, min_val: int, max_val: int) -> str | None:
    """Validate integer is within range.
    
    Args:
        value: Value to validate.
        field_name: Field name for error message.
        min_val: Minimum allowed value.
        max_val: Maximum allowed value.
        
    Returns:
        Error message if invalid, None if valid.
    """
    if value is None:
        return f"{field_name} is required"
    
    if not isinstance(value, int) or isinstance(value, bool):
        return f"{field_name} must be an integer"
    
    if value < min_val or value > max_val:
        return f"{field_name} must be between {min_val} and {max_val}, got {value}"
    
    return None


def validate_text_field(text: Any, field_name: str, max_length: int = 1000000) -> str | None:
    """Validate text field.
    
    Args:
        text: Text value to validate.
        field_name: Field name for error message.
        max_length: Maximum allowed text length.
        
    Returns:
        Error message if invalid, None if valid.
    """
    if text is None or not isinstance(text, str):
        return f"{field_name} must be a string"
    if not text.strip():
        return f"{field_name} must not be empty"
    if len(text) > max_length:
        return f"{field_name} exceeds maximum length of {max_length} characters"
    return None


def validate_metadata(metadata: Any, max_depth: int = 3) -> tuple[bool, str]:
    """Validate metadata structure recursively.
    
    Args:
        metadata: Metadata object to validate.
        max_depth: Maximum allowed nesting depth.
        
    Returns:
        Tuple of (is_valid, error_message).
    """
    def _validate(obj: Any, depth: int = 0) -> tuple[bool, str]:
        """Internal recursive validation."""
        if depth > max_depth:
            return False, f"Metadata depth exceeds {max_depth}"
        
        if obj is None:
            return True, ""
        
        if isinstance(obj, (str, int, float, bool)):
            return True, ""
        
        if isinstance(obj, list):
            for i, item in enumerate(obj):
                valid, msg = _validate(item, depth + 1)
                if not valid:
                    return False, f"list[{i}]: {msg}"
            return True, ""
        
        if isinstance(obj, dict):
            for key, value in obj.items():
                if not isinstance(key, str):
                    return False, f"Dict key must be string, got {type(key).__name__}"
                valid, msg = _validate(value, depth + 1)
                if not valid:
                    return False, f"{key}: {msg}"
            return True, ""
        
        return False, f"Unsupported type: {type(obj).__name__}"
    
    return _validate(metadata, 0)


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