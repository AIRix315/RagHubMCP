# Deprecated Module Notice

**Status**: DEPRECATED  
**Deprecated Since**: v2.1  
**Removal Target**: v3.0  
**Last Updated**: 2026-03-22

---

## Overview

The `src/services` module is deprecated and will be removed in v3.0.

This module previously provided service layer abstractions for search operations.
All functionality has been migrated to the Pipeline architecture.

---

## Migration Guide

### Before (Deprecated)

```python
from src.services import HybridSearchService, get_hybrid_search_service
from src.services import BM25Service, get_bm25_service

# Direct service usage (DEPRECATED)
hybrid_service = get_hybrid_search_service()
results = await hybrid_service.search(query, options)

bm25_service = get_bm25_service()
results = await bm25_service.search(query)
```

### After (Current)

```python
from src.pipeline import execute_search, get_pipeline

# Use Pipeline (RULE-1 compliance)
result = await execute_search(query, options)

# Or create pipeline instance
pipeline = get_pipeline()
result = await pipeline.run(query, options)
```

---

## Component Mappings

| Old (services/) | New (pipeline/) | Notes |
|-----------------|-----------------|-------|
| `HybridSearchService` | `HybridRetriever` | Via Pipeline |
| `BM25Service` | `HybridRetriever` (BM25 component) | Integrated into Pipeline |
| `reciprocal_rank_fusion()` | Internal Pipeline method | Not exposed directly |
| `HybridSearchResult` | `RAGResult` | Pipeline result type |

---

## Why Deprecated?

1. **RULE-1 Compliance**: All RAG operations must go through Pipeline
2. **Single Responsibility**: Pipeline is the unified execution entry
3. **Better Testability**: Pipeline architecture supports dependency injection
4. **Simpler API**: Users only need to interact with Pipeline, not individual services

---

## Backward Compatibility

The module will continue to work in v2.x with deprecation warnings:

```python
import warnings
warnings.warn(
    "services module is deprecated, use pipeline module instead",
    DeprecationWarning,
    stacklevel=2
)
```

---

## Timeline

- **v2.1**: Deprecation warning added
- **v2.x**: Module works with warnings
- **v3.0**: Module will be removed

---

## Questions?

See:
- `src/pipeline/__init__.py` for new API
- `Docs/11-V2-Design.md` for architecture overview
- `RULE.md` for development guidelines
