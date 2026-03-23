"""Message configuration for RagHubMCP.

This module provides centralized message strings for internationalization.
Currently supports Chinese (zh-CN) and English (en-US).

Usage:
    from raghub_mcp.messages import get_message

    message = get_message("app_title", lang="zh")
"""

from __future__ import annotations

from typing import Literal

# Supported languages
Language = Literal["zh", "en"]

# Message key type
MessageKey = Literal[
    "app_title",
    "app_description",
    "profile_fast_description",
    "profile_fast_use_cases",
    "profile_balanced_description",
    "profile_balanced_use_cases",
    "profile_accurate_description",
    "profile_accurate_use_cases",
    "profile_applied",
    "profile_not_found",
]

# Chinese messages
MESSAGES_ZH: dict[str, str] = {
    "app_title": "通用代码 RAG 中枢",
    "app_description": "通用代码 RAG 中枢 - REST API + MCP Server",
    "profile_fast_description": "快速响应，适合实时场景",
    "profile_fast_use_cases": "开发调试, 快速验证, 资源受限设备",
    "profile_balanced_description": "速度与质量的最佳平衡",
    "profile_balanced_use_cases": "日常使用, 团队协作, 大多数场景",
    "profile_accurate_description": "追求最高质量，适合复杂查询",
    "profile_accurate_use_cases": "生产环境, 关键业务, 复杂查询",
    "profile_applied": "已应用 {description} 配置",
    "profile_not_found": "配置 {profile} 不存在",
}

# English messages
MESSAGES_EN: dict[str, str] = {
    "app_title": "Universal Code RAG Hub",
    "app_description": "Universal Code RAG Hub - REST API + MCP Server",
    "profile_fast_description": "Fast response, suitable for real-time scenarios",
    "profile_fast_use_cases": "development, quick verification, resource-constrained devices",
    "profile_balanced_description": "Best balance between speed and quality",
    "profile_balanced_use_cases": "daily use, team collaboration, most scenarios",
    "profile_accurate_description": "Highest quality, suitable for complex queries",
    "profile_accurate_use_cases": "production, critical business, complex queries",
    "profile_applied": "Applied {description} configuration",
    "profile_not_found": "Profile {profile} not found",
}


def get_message(key: MessageKey, lang: Language = "zh", **kwargs: str) -> str:
    """Get a localized message by key.

    Args:
        key: Message key.
        lang: Language code (zh or en).
        **kwargs: Format arguments for the message template.

    Returns:
        Localized message string.

    Example:
        >>> get_message("app_title")
        '通用代码 RAG 中枢'
        >>> get_message("profile_applied", description="balanced")
        '已应用 balanced 配置'
    """
    messages = MESSAGES_ZH if lang == "zh" else MESSAGES_EN
    template = messages.get(key, key)

    if kwargs:
        return template.format(**kwargs)
    return template


def get_profile_description(profile: str, lang: Language = "zh") -> str:
    """Get profile description by profile name.

    Args:
        profile: Profile name (fast, balanced, accurate).
        lang: Language code (zh or en).

    Returns:
        Profile description string.
    """
    key = f"profile_{profile}_description"
    messages = MESSAGES_ZH if lang == "zh" else MESSAGES_EN
    return messages.get(key, profile)


def get_profile_use_cases(profile: str, lang: Language = "zh") -> str:
    """Get profile use cases by profile name.

    Args:
        profile: Profile name (fast, balanced, accurate).
        lang: Language code (zh or en).

    Returns:
        Profile use cases string (comma-separated).
    """
    key = f"profile_{profile}_use_cases"
    messages = MESSAGES_ZH if lang == "zh" else MESSAGES_EN
    return messages.get(key, profile)


__all__ = [
    "get_message",
    "get_profile_description",
    "get_profile_use_cases",
    "MESSAGES_ZH",
    "MESSAGES_EN",
    "Language",
    "MessageKey",
]
