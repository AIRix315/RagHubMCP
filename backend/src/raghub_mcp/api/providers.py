"""Provider Management API endpoints.

This module implements the Provider CRUD and testing API as defined in:
- Docs/22-Config-API-Design.md Section 3.2.2, 3.2.3
- TODO 1.10: Rerank相关API实现

Endpoints:
- GET /api/providers - List all providers
- GET /api/providers/{type} - List providers by type
- GET /api/providers/{type}/{name} - Get provider details
- POST /api/providers/{type}/{name}/test - Test provider (rerank focus)
- PUT /api/providers/{type}/{name} - Create/update provider
- DELETE /api/providers/{type}/{name} - Delete provider
- POST /api/providers/{type}/{name}/set-default - Set as default
"""

from __future__ import annotations

import time
from typing import Any

from fastapi import APIRouter, HTTPException

from raghub_mcp.providers import ProviderCategory
from raghub_mcp.providers.factory import factory
from raghub_mcp.utils.config import get_config

from .schemas import (
    EngineComparison,
    EngineMetrics,
    ErrorResponse,
    ProviderCreateRequest,
    ProviderDeleteResponse,
    ProviderInfo,
    ProvidersListResponse,
    ProviderStatus,
    ProviderUpdateResponse,
    RerankCompareRequest,
    RerankCompareResponse,
    RerankResult,
    RerankTestRequest,
    RerankTestResponse,
    SetDefaultProviderResponse,
)

router = APIRouter(prefix="/providers", tags=["providers"])


# Provider type mapping
PROVIDER_TYPES = {
    "embedding": ProviderCategory.EMBEDDING,
    "rerank": ProviderCategory.RERANK,
    "llm": ProviderCategory.LLM,
    "vectorstore": ProviderCategory.VECTORSTORE,
}


def _get_provider_status(provider_config: dict[str, Any]) -> tuple[ProviderStatus, str | None]:
    """Determine provider status based on configuration.

    Args:
        provider_config: Provider instance configuration

    Returns:
        Tuple of (status, error_message)
    """
    # Check for required fields based on type
    provider_type = provider_config.get("type", "")

    if provider_type == "api":
        # API providers need api_key
        api_key = provider_config.get("api_key")
        if not api_key:
            return ProviderStatus.ERROR, "API Key not configured"
        return ProviderStatus.ACTIVE, None

    if provider_type == "onnx":
        # ONNX providers need model_path
        model_path = provider_config.get("model_path")
        if not model_path:
            return ProviderStatus.ERROR, "Model path not configured"
        return ProviderStatus.ACTIVE, None

    if provider_type in ("ollama", "openai"):
        # These need base_url or have defaults
        return ProviderStatus.ACTIVE, None

    # Default to active for other types
    return ProviderStatus.ACTIVE, None


def _build_provider_info(
    instance: dict[str, Any],
    category: str,
    default_name: str,
) -> ProviderInfo:
    """Build ProviderInfo from instance configuration.

    Args:
        instance: Provider instance configuration
        category: Provider category name
        default_name: Name of the default provider

    Returns:
        ProviderInfo model
    """
    status, error_message = _get_provider_status(instance)
    name = instance.get("name", "unknown")

    return ProviderInfo(
        name=name,
        type=instance.get("type", "unknown"),
        status=status,
        is_default=(name == default_name),
        model=instance.get("model"),
        config=instance,
        error_message=error_message,
        capabilities={
            "supports_batch": instance.get("batch_size") is not None,
            "has_model": instance.get("model") is not None,
        },
    )


@router.get("", response_model=ProvidersListResponse)
async def list_all_providers() -> ProvidersListResponse:
    """List all providers grouped by category.

    Returns:
        ProvidersListResponse with all providers organized by category.
    """
    config = get_config()
    result = ProvidersListResponse()

    for category in ["embedding", "rerank", "llm", "vectorstore"]:
        category_config = getattr(config.providers, category, None)
        if not category_config:
            continue

        default_name = category_config.default or ""
        providers_list = []

        for instance in category_config.instances:
            info = _build_provider_info(instance, category, default_name)
            providers_list.append(info)

        setattr(result, category, providers_list)

    return result


@router.get("/rerank", response_model=list[ProviderInfo])
async def list_rerank_providers() -> list[ProviderInfo]:
    """List all rerank providers with status.

    Task 1.10.1: GET /api/providers/rerank

    Returns:
        List of ProviderInfo for rerank providers.
    """
    config = get_config()
    rerank_config = config.providers.rerank

    if not rerank_config:
        return []

    default_name = rerank_config.default or ""
    providers_list = []

    for instance in rerank_config.instances:
        info = _build_provider_info(instance, "rerank", default_name)
        providers_list.append(info)

    return providers_list


@router.get(
    "/{provider_type}/{name}",
    response_model=ProviderInfo,
    responses={404: {"model": ErrorResponse}},
)
async def get_provider(provider_type: str, name: str) -> ProviderInfo:
    """Get details of a specific provider.

    Args:
        provider_type: Provider category (embedding, rerank, llm, vectorstore)
        name: Provider instance name

    Returns:
        ProviderInfo for the requested provider.

    Raises:
        HTTPException: 404 if provider not found
    """
    if provider_type not in PROVIDER_TYPES:
        raise HTTPException(
            status_code=404,
            detail={"error": "invalid_type", "message": f"Unknown provider type: {provider_type}"},
        )

    config = get_config()
    category_config = getattr(config.providers, provider_type, None)

    if not category_config:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "category_not_found",
                "message": f"No providers configured for type: {provider_type}",
            },
        )

    for instance in category_config.instances:
        if instance.get("name") == name:
            return _build_provider_info(instance, provider_type, category_config.default or "")

    available = [i.get("name") for i in category_config.instances]
    raise HTTPException(
        status_code=404,
        detail={
            "error": "provider_not_found",
            "message": f"Provider '{name}' not found. Available: {available}",
        },
    )


@router.post(
    "/rerank/{name}/test",
    response_model=RerankTestResponse,
    responses={404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
async def test_rerank_provider(name: str, request: RerankTestRequest) -> RerankTestResponse:
    """Test a rerank provider.

    Task 1.10.2: POST /api/providers/rerank/{name}/test

    Args:
        name: Rerank provider instance name
        request: Test request with query and documents

    Returns:
        RerankTestResponse with results and latency.

    Raises:
        HTTPException: 404 if provider not found, 500 on test failure
    """
    try:
        provider = factory.get_rerank_provider(name)
    except Exception as e:
        raise HTTPException(
            status_code=404,
            detail={"error": "provider_not_found", "message": str(e)},
        )

    start_time = time.time()

    try:
        # Call the provider's async rerank method
        results = await provider.arerank(
            query=request.query,
            documents=request.documents,
            top_k=request.top_k,
        )
        latency_ms = (time.time() - start_time) * 1000

        # Build response
        rerank_results = []
        for i, result in enumerate(results[: request.top_k]):
            rerank_results.append(
                RerankResult(
                    index=result.index,
                    text=result.text or request.documents[result.index],
                    score=result.score,
                    rank=i + 1,
                )
            )

        # Get provider config for engine info
        config = get_config()
        provider_config = None
        for inst in config.providers.rerank.instances:
            if inst.get("name") == name:
                provider_config = inst
                break

        return RerankTestResponse(
            results=rerank_results,
            latency_ms=latency_ms,
            engine_info={
                "name": name,
                "type": provider_config.get("type", "unknown") if provider_config else "unknown",
                "model": provider_config.get("model", "unknown") if provider_config else "unknown",
            },
            intermediate_scores=None,  # Not supported by base provider
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error": "test_failed", "message": f"Rerank test failed: {str(e)}"},
        )


@router.post(
    "/rerank/compare",
    response_model=RerankCompareResponse,
    responses={404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
async def compare_rerank_engines(request: RerankCompareRequest) -> RerankCompareResponse:
    """Compare multiple rerank engines.

    Task 2.6.1: POST /api/providers/rerank/compare

    Args:
        request: Compare request with query, documents, and engine names

    Returns:
        RerankCompareResponse with comparison results.

    Raises:
        HTTPException: 404 if any engine not found, 500 on comparison failure
    """
    import time  # already imported at top

    start_time = time.time()
    comparisons: list[EngineComparison] = []

    for engine_name in request.engines:
        try:
            provider = factory.get_rerank_provider(engine_name)
        except Exception as e:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "provider_not_found",
                    "message": f"Engine '{engine_name}' not found: {str(e)}",
                },
            )

        engine_start = time.time()

        try:
            # Call the provider's async rerank method
            results = await provider.arerank(
                query=request.query,
                documents=request.documents,
                top_k=request.top_k,
            )
            engine_latency = (time.time() - engine_start) * 1000

            # Build result list
            rerank_results = []
            scores = []
            for i, result in enumerate(results[: request.top_k]):
                rerank_results.append(
                    RerankResult(
                        index=result.index,
                        text=result.text or request.documents[result.index],
                        score=result.score,
                        rank=i + 1,
                    )
                )
                scores.append(result.score)

            # Calculate metrics
            top1_score = scores[0] if scores else 0.0
            avg_score = sum(scores) / len(scores) if scores else 0.0

            comparisons.append(
                EngineComparison(
                    engine=engine_name,
                    metrics=EngineMetrics(
                        latency_ms=engine_latency,
                        top1_score=top1_score,
                        avg_score=avg_score,
                    ),
                    results=rerank_results,
                )
            )

        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "comparison_failed",
                    "message": f"Engine '{engine_name}' comparison failed: {str(e)}",
                },
            )

    total_latency = (time.time() - start_time) * 1000

    return RerankCompareResponse(
        query=request.query,
        comparisons=comparisons,
        total_latency_ms=total_latency,
    )


@router.put(
    "/{provider_type}/{name}",
    response_model=ProviderUpdateResponse,
    responses={400: {"model": ErrorResponse}, 422: {"model": ErrorResponse}},
)
async def create_or_update_provider(
    provider_type: str, name: str, request: ProviderCreateRequest
) -> ProviderUpdateResponse:
    """Create or update a provider configuration.

    Task 1.10.3: Provider CRUD API

    Args:
        provider_type: Provider category
        name: Provider instance name
        request: Provider configuration

    Returns:
        ProviderUpdateResponse

    Raises:
        HTTPException: 400/422 on validation failure
    """
    if provider_type not in PROVIDER_TYPES:
        raise HTTPException(
            status_code=400,
            detail={"error": "invalid_type", "message": f"Unknown provider type: {provider_type}"},
        )

    config = get_config()
    category_config = getattr(config.providers, provider_type, None)

    if not category_config:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "category_not_configured",
                "message": f"Provider category '{provider_type}' is not configured",
            },
        )

    # Check if provider exists
    is_new = True
    for i, instance in enumerate(category_config.instances):
        if instance.get("name") == name:
            # Update existing
            category_config.instances[i] = {"name": name, **request.config, "type": request.type}
            is_new = False
            break

    if is_new:
        # Add new provider
        category_config.instances.append({"name": name, **request.config, "type": request.type})

    # Set as default if requested
    if request.set_as_default:
        category_config.default = name

    # Clear factory cache to pick up new config
    factory.clear_cache()

    return ProviderUpdateResponse(
        name=name,
        message=f"Provider {'created' if is_new else 'updated'} successfully",
        is_new=is_new,
    )


@router.delete(
    "/{provider_type}/{name}",
    response_model=ProviderDeleteResponse,
    responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
)
async def delete_provider(provider_type: str, name: str) -> ProviderDeleteResponse:
    """Delete a provider configuration.

    Task 1.10.3: Provider CRUD API

    Args:
        provider_type: Provider category
        name: Provider instance name

    Returns:
        ProviderDeleteResponse

    Raises:
        HTTPException: 400 if default provider, 404 if not found
    """
    if provider_type not in PROVIDER_TYPES:
        raise HTTPException(
            status_code=404,
            detail={"error": "invalid_type", "message": f"Unknown provider type: {provider_type}"},
        )

    config = get_config()
    category_config = getattr(config.providers, provider_type, None)

    if not category_config:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "category_not_configured",
                "message": f"Provider category '{provider_type}' is not configured",
            },
        )

    # Find and remove provider
    for i, instance in enumerate(category_config.instances):
        if instance.get("name") == name:
            # Check if it's the default
            if category_config.default == name:
                raise HTTPException(
                    status_code=400,
                    detail={
                        "error": "cannot_delete_default",
                        "message": f"Cannot delete default provider '{name}'. Set another provider as default first.",
                    },
                )

            del category_config.instances[i]
            factory.clear_cache()

            return ProviderDeleteResponse(name=name, message=f"Provider '{name}' deleted")

    raise HTTPException(
        status_code=404,
        detail={"error": "provider_not_found", "message": f"Provider '{name}' not found"},
    )


@router.post(
    "/{provider_type}/{name}/set-default",
    response_model=SetDefaultProviderResponse,
    responses={404: {"model": ErrorResponse}},
)
async def set_default_provider(provider_type: str, name: str) -> SetDefaultProviderResponse:
    """Set a provider as the default for its category.

    Args:
        provider_type: Provider category
        name: Provider instance name

    Returns:
        SetDefaultProviderResponse

    Raises:
        HTTPException: 404 if provider not found
    """
    if provider_type not in PROVIDER_TYPES:
        raise HTTPException(
            status_code=404,
            detail={"error": "invalid_type", "message": f"Unknown provider type: {provider_type}"},
        )

    config = get_config()
    category_config = getattr(config.providers, provider_type, None)

    if not category_config:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "category_not_configured",
                "message": f"Provider category '{provider_type}' is not configured",
            },
        )

    # Find provider
    for instance in category_config.instances:
        if instance.get("name") == name:
            category_config.default = name
            factory.clear_cache()

            return SetDefaultProviderResponse(
                name=name,
                type=provider_type,
                message=f"'{name}' is now the default {provider_type} provider",
            )

    available = [i.get("name") for i in category_config.instances]
    raise HTTPException(
        status_code=404,
        detail={
            "error": "provider_not_found",
            "message": f"Provider '{name}' not found. Available: {available}",
        },
    )
