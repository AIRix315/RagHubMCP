# RagHubMCP 修复计划

**版本**: v1.0  
**创建日期**: 2026-03-22  
**目标**: 系统性修复项目问题，不制造新问题，不扩散问题

---

## 修复原则

1. **渐进式重构**: 每步可验证，不破坏现有功能
2. **向后兼容**: 保留旧接口，添加 deprecation 警告
3. **测试优先**: 每个修复前编写测试，修复后验证
4. **单一职责**: 每个 PR 只解决一个问题
5. **不扩散**: 修复范围控制在最小必要改动

---

## Phase 1: 架构基础修复 (高优先级)

### 1.1 创建 IndexPipeline (修复 RULE-1)

**目标**: 将 ingest/index 操作统一到 Pipeline 架构

**文件清单**:
- 新增: `backend/src/pipeline/index_pipeline.py`
- 修改: `backend/src/pipeline/__init__.py`
- 修改: `backend/src/pipeline/factory.py`
- 修改: `backend/src/mcp_server/tools/v2/__init__.py`
- 修改: `backend/src/api/index.py`

**变更详情**:

```python
# backend/src/pipeline/index_pipeline.py (新增)
"""Index Pipeline for unified indexing operations.

This module provides IndexPipeline that encapsulates:
- File scanning
- Chunking
- Embedding generation
- Vector store insertion
- BM25 index update

Reference: RULE-1 - Pipeline is the only execution entry.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.chunkers import ChunkerRegistry
from src.indexer.scanner import FileScanner
from src.providers import factory


@dataclass
class IndexOptions:
    """Options for indexing operation."""
    collection_name: str = "default"
    chunk_size: int = 500
    chunk_overlap: int = 50
    recursive: bool = True
    embedding_provider: str | None = None


@dataclass
class IndexResult:
    """Result of indexing operation."""
    task_id: str
    total_files: int
    processed_files: int
    total_chunks: int
    status: str  # "pending", "running", "completed", "failed"
    message: str | None = None


class IndexPipeline(ABC):
    """Abstract base class for indexing pipelines."""

    @abstractmethod
    async def index(
        self,
        path: str | Path,
        options: IndexOptions | None = None
    ) -> IndexResult:
        """Execute indexing operation.

        Args:
            path: Directory or file path to index
            options: Indexing options

        Returns:
            IndexResult with task status and statistics
        """
        ...


class DefaultIndexPipeline(IndexPipeline):
    """Default implementation of IndexPipeline."""

    def __init__(self) -> None:
        self._scanner = FileScanner()
        self._chunker_registry = ChunkerRegistry()

    async def index(
        self,
        path: str | Path,
        options: IndexOptions | None = None
    ) -> IndexResult:
        options = options or IndexOptions()
        # Implementation...
        pass


# Singleton instance
_index_pipeline: IndexPipeline | None = None


def get_index_pipeline() -> IndexPipeline:
    """Get singleton IndexPipeline instance."""
    global _index_pipeline
    if _index_pipeline is None:
        _index_pipeline = DefaultIndexPipeline()
    return _index_pipeline


def execute_index(
    path: str | Path,
    options: IndexOptions | None = None
) -> IndexResult:
    """Convenience function to execute indexing."""
    pipeline = get_index_pipeline()
    return await pipeline.index(path, options)
```

```python
# backend/src/pipeline/__init__.py (修改)
# 添加导出
from .index_pipeline import (
    DefaultIndexPipeline,
    IndexOptions,
    IndexPipeline,
    IndexResult,
    execute_index,
    get_index_pipeline,
)

__all__ = [
    # ... existing exports ...
    # Index Pipeline
    "IndexPipeline",
    "DefaultIndexPipeline",
    "IndexOptions",
    "IndexResult",
    "get_index_pipeline",
    "execute_index",
]
```

```python
# backend/src/mcp_server/tools/v2/__init__.py (修改)
# 修改 ingest 函数

# 旧代码 (违反 RULE-1):
# from chunkers import SimpleChunker
# from providers.factory import factory
# chunker = SimpleChunker()
# vectorstore = factory.get_vectorstore_provider()

# 新代码 (遵守 RULE-1):
from src.pipeline import execute_index, IndexOptions

@mcp.tool()
async def ingest(path: str, collection_name: str = "default") -> dict:
    """Index a directory or file."""
    result = await execute_index(
        path,
        IndexOptions(collection_name=collection_name)
    )
    return {
        "task_id": result.task_id,
        "status": result.status,
        "total_files": result.total_files,
    }
```

**测试要求**:
- 新增: `backend/tests/test_pipeline/test_index_pipeline.py`
- 验证: IndexPipeline 能正确调用 FileScanner 和 Chunker
- 验证: MCP ingest 工具通过 IndexPipeline 执行

---

### 1.2 创建 ChunkerFactory (修复 RULE-3)

**目标**: 为 Chunkers 添加类似 Providers 的工厂模式

**文件清单**:
- 修改: `backend/src/chunkers/registry.py`
- 新增: `backend/src/chunkers/factory.py`
- 修改: `backend/src/chunkers/__init__.py`
- 修改: `backend/src/mcp_server/tools/v2/__init__.py`

**变更详情**:

```python
# backend/src/chunkers/factory.py (新增)
"""Chunker Factory for configuration-driven instantiation.

Reference: RULE-3 - No direct dependency on concrete implementations.
"""

from typing import Any

from .base import ChunkerPlugin
from .registry import ChunkerRegistry, registry


class ChunkerFactory:
    """Factory for creating chunker instances.

    Similar to ProviderFactory, this factory creates chunker instances
    based on configuration, supporting hot reloading.
    """

    def __init__(self) -> None:
        self._registry = registry
        self._cache: dict[str, ChunkerPlugin] = {}

    def get_chunker(
        self,
        name: str | None = None,
        file_type: str | None = None,
        **config: Any
    ) -> ChunkerPlugin:
        """Get a chunker instance.

        Args:
            name: Chunker name (e.g., "simple", "markdown")
            file_type: File extension to determine chunker
            **config: Chunker configuration

        Returns:
            Configured ChunkerPlugin instance
        """
        if name:
            return self._get_by_name(name, **config)
        elif file_type:
            return self._get_by_file_type(file_type, **config)
        else:
            # Default chunker
            return self._get_by_name("simple", **config)

    def _get_by_name(self, name: str, **config: Any) -> ChunkerPlugin:
        """Get chunker by name."""
        if name not in self._cache:
            chunker_class = self._registry.get(name)
            self._cache[name] = chunker_class(**config)
        return self._cache[name]

    def _get_by_file_type(self, file_type: str, **config: Any) -> ChunkerPlugin:
        """Get chunker by file type."""
        # Map file types to chunkers
        type_map = {
            ".md": "markdown",
            ".py": "python_ast",
            ".ts": "typescript_ast",
            ".go": "go_ast",
        }
        name = type_map.get(file_type, "simple")
        return self._get_by_name(name, **config)

    def clear_cache(self) -> None:
        """Clear cached chunker instances."""
        self._cache.clear()


# Singleton instance
factory = ChunkerFactory()
```

```python
# backend/src/chunkers/__init__.py (修改)
# 添加导出
from .factory import ChunkerFactory, factory

__all__ = [
    # ... existing exports ...
    "ChunkerFactory",
    "factory",
]
```

**测试要求**:
- 新增: `backend/tests/test_chunkers/test_factory.py`
- 验证: 通过 factory 获取 chunker
- 验证: 缓存机制工作正常

---

## Phase 2: 安全与配置 (高优先级)

### 2.1 修复 CORS 配置

**目标**: 显式列出允许的 HTTP 方法，减少安全风险

**文件清单**:
- 修改: `backend/config.yaml`
- 修改: `backend/src/utils/config.py` (Pydantic 模型)

**变更详情**:

```yaml
# backend/config.yaml (修改)
cors:
  allow_credentials: true
  # 修改前: allow_methods: ["*"]
  # 修改后: 显式列出允许的方法
  allow_methods:
    - GET
    - POST
    - PUT
    - DELETE
    - OPTIONS
  # 修改前: allow_headers: ["*"]
  # 修改后: 显式列出允许的头部
  allow_headers:
    - Content-Type
    - Authorization
    - X-Requested-With
  origins:
    - http://localhost:3315
    - http://127.0.0.1:3315
```

**向后兼容**: 配置变更不影响 API，仅增强安全性

---

### 2.2 生成 Python Lock 文件

**目标**: 锁定依赖版本，支持漏洞扫描

**文件清单**:
- 新增: `backend/requirements-lock.txt`
- 修改: `.github/workflows/ci.yml` (添加安全检查)

**变更详情**:

```bash
# 生成 lock 文件
cd backend
pip freeze > requirements-lock.txt

# 或使用 pip-tools (推荐)
pip install pip-tools
pip-compile pyproject.toml -o requirements.txt
```

```yaml
# .github/workflows/ci.yml (添加)
- name: Security Audit
  run: |
    pip install safety
    safety check -r backend/requirements-lock.txt
```

**测试要求**:
- 验证 CI 能通过 safety 检查
- 验证 lock 文件与 pyproject.toml 一致

---

## Phase 3: 代码质量 (中优先级)

### 3.1 提取 normalize_scores (DRY)

**目标**: 消除 3 处重复代码

**文件清单**:
- 新增: `backend/src/utils/scoring.py`
- 修改: `backend/src/pipeline/retriever.py`
- 修改: `backend/src/rerank_engine/scorers/hybrid_scorer.py`
- 修改: `backend/src/rerank_engine/scorers/bm25_scorer.py`

**变更详情**:

```python
# backend/src/utils/scoring.py (新增)
"""Scoring utilities for normalization and aggregation."""

import numpy as np
from typing import Sequence


def normalize_scores(
    scores: Sequence[float],
    method: str = "minmax"
) -> list[float]:
    """Normalize scores to [0, 1] range.

    Args:
        scores: Raw scores to normalize
        method: Normalization method ("minmax" or "zscore")

    Returns:
        Normalized scores

    Example:
        >>> normalize_scores([1.0, 2.0, 3.0])
        [0.0, 0.5, 1.0]
    """
    if not scores:
        return []

    if method == "minmax":
        min_score = min(scores)
        max_score = max(scores)
        if max_score == min_score:
            return [0.5] * len(scores)
        return [(s - min_score) / (max_score - min_score) for s in scores]

    elif method == "zscore":
        mean = np.mean(scores)
        std = np.std(scores)
        if std == 0:
            return [0.0] * len(scores)
        return [(s - mean) / std for s in scores]

    else:
        raise ValueError(f"Unknown normalization method: {method}")
```

```python
# backend/src/pipeline/retriever.py (修改)
# 替换原有实现
from src.utils.scoring import normalize_scores

# 删除旧的 normalize_scores 函数
# 使用新的统一实现
```

**向后兼容**: 函数签名保持一致，直接替换

---

### 3.2 修复空 Catch 块

**目标**: 至少记录日志，不静默忽略错误

**文件清单**:
- 修改: `backend/src/cli/main.py`
- 修改: `backend/src/api/websocket_debug.py`

**变更详情**:

```python
# backend/src/cli/main.py (修改)
# 旧代码:
# except Exception:
#     pass

# 新代码:
except Exception as e:
    logger.warning(f"Failed to get active profile: {e}")
    # 可选: 显示友好的错误信息给用户
    console.print("[yellow]Warning: Could not retrieve active profile[/]")
```

```python
# backend/src/api/websocket_debug.py (修改)
# 旧代码:
# except ValueError:
#     pass

# 新代码:
except ValueError:
    logger.debug(f"WebSocket {websocket.client} not in subscribers list")
    # 这是正常情况，不需要报错，但应该记录
```

---

### 3.3 修复 ONNX 资源泄露

**目标**: 添加资源清理机制

**文件清单**:
- 修改: `backend/src/rerank_engine/scorers/onnx_scorer.py`

**变更详情**:

```python
# backend/src/rerank_engine/scorers/onnx_scorer.py (修改)

class ONNXScorer(BaseScorer):
    """ONNX-based scorer with proper resource management."""

    def __init__(self, config: dict[str, Any]) -> None:
        # ... existing code ...
        self._session: ort.InferenceSession | None = None

    def __del__(self):
        """Cleanup ONNX session on garbage collection."""
        self.close()

    def close(self) -> None:
        """Explicitly close ONNX session and release resources."""
        if self._session is not None:
            # ONNX Runtime doesn't have explicit close, but we can
            # set to None to allow GC
            self._session = None
            logger.debug("ONNX session closed")

    # 添加上下文管理器支持
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
```

---

## Phase 4: 测试改进 (中优先级)

### 4.1 减少 Mock 使用

**目标**: 为核心流程添加真实集成测试

**文件清单**:
- 新增: `backend/tests/test_integration/test_index_pipeline.py`
- 新增: `backend/tests/test_integration/test_search_pipeline.py`
- 修改: `backend/tests/test_graph/test_graph.py` (减少 mock)

**策略**:
1. 使用 Testcontainers 启动 ChromaDB/Qdrant
2. 使用真实 Provider 实例 (Ollama mock 或 HTTP mock)
3. 测试完整流程: index → search → rerank

```python
# backend/tests/test_integration/test_index_pipeline.py (新增)
import pytest
from testcontainers.core.container import DockerContainer

@pytest.fixture(scope="module")
def chroma_container():
    """Start ChromaDB container for integration tests."""
    container = DockerContainer("chromadb/chroma:latest")
    container.with_exposed_port(8000)
    container.start()
    yield container
    container.stop()

@pytest.mark.integration
def test_index_and_search_flow(chroma_container):
    """Test complete index → search flow with real dependencies."""
    # 使用真实 ChromaDB 实例
    # 使用 mock HTTP server for Ollama
    # 验证完整流程
    pass
```

---

### 4.2 测试模块化收敛（关键）

**背景**: 
- MVP 早期采用"一个文件一个测试"模式（80个测试文件 vs 117个源文件，几乎 1:1）
- 经历2次重构后，版本已稳定，许多测试可以按模块合并
- 细粒度测试导致：Mock 过多、维护成本高、覆盖范围受限

**目标**: 
- 按功能模块重新组织测试，减少测试文件数量
- 降低 Mock 使用，扩大测试范围
- 提升测试可维护性和实际意义

**当前问题示例**:
```
test_pipeline/
├── test_pipeline.py              # 基础测试
├── test_pipeline_context_builder.py   # 可合并到 test_pipeline
├── test_pipeline_manager.py      # 可合并到 test_pipeline
├── test_pipeline_options.py      # 可合并到 test_pipeline
├── test_hybrid_retriever.py      # 独立，但可扩展
├── test_vector_retriever.py      # 可合并到 test_retriever.py
├── test_reranker.py              # 独立
├── test_query_rewrite.py         # 可合并到 test_query_processing.py
└── test_multi_query.py           # 可合并到 test_query_processing.py

# 应收敛为:
test_pipeline/
├── test_pipeline_core.py         # pipeline/manager/options 合并
├── test_retrieval.py             # hybrid + vector 合并
├── test_reranker.py              # 保留（核心组件）
└── test_query_processing.py      # query_rewrite + multi_query 合并
```

**合并策略**:

| 当前分散文件 | 合并目标 | 预期效果 |
|-------------|---------|---------|
| `test_pipeline*.py` (5个文件) | `test_pipeline_core.py` | 统一 Pipeline 测试入口，减少重复 fixtures |
| `test_vector_retriever.py` + `test_hybrid_retriever.py` | `test_retrieval.py` | 测试 Hybrid 和 Vector 的协作，而非隔离 |
| `test_query_rewrite.py` + `test_multi_query.py` | `test_query_processing.py` | 测试完整查询处理流程 |
| `test_context_builder_merge.py` + `test_pipeline_context_builder.py` | 合并到 `test_pipeline_core.py` | ContextBuilder 作为 Pipeline 一部分测试 |
| `test_onnx_scorer.py` + `test_vector_scorer.py` + `test_hybrid_scorer.py` | `test_scorers.py` | 统一 Scorer 接口测试 |
| `test_strategies.py` + `test_processors.py` | `test_rerank_components.py` | Rerank 流程整体测试 |

**实施步骤**:

1. **保持现有测试通过** - 先不删除旧文件，创建新合并文件
2. **迁移并扩展测试** - 合并时移除 Mock，使用真实组件
3. **验证覆盖范围** - 确保合并后覆盖率不下降
4. **删除旧文件** - 验证稳定后删除分散的测试文件

**预期收益**:
- 测试文件从 80 个 → 约 40 个（减少 50%）
- Mock 使用减少 60%+（因为测试范围扩大，真实组件协作）
- 维护成本降低（ fixtures 共享，setup/teardown 统一）
- 测试速度提升（减少重复初始化）

---

### 4.3 添加前端组件测试

**目标**: 为关键组件添加单元测试

**文件清单**:
- 新增: `frontend/src/components/common/__tests__/ThemeSwitcher.test.ts`
- 新增: `frontend/src/components/charts/__tests__/LatencyChart.test.ts`
- 修改: `frontend/vitest.config.ts` (添加组件测试配置)

```typescript
// frontend/src/components/common/__tests__/ThemeSwitcher.test.ts (新增)
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import ThemeSwitcher from '../ThemeSwitcher.vue'

describe('ThemeSwitcher', () => {
  it('should toggle theme on click', async () => {
    const wrapper = mount(ThemeSwitcher)
    await wrapper.find('button').trigger('click')
    expect(wrapper.emitted()).toHaveProperty('toggle')
  })
})
```

---

## Phase 5: 完善与清理 (低优先级)

### 5.1 增强路径遍历防护

**目标**: 验证最终路径仍在 root 内

**文件清单**:
- 修改: `backend/src/indexer/scanner.py`

**变更详情**:

```python
# backend/src/indexer/scanner.py (修改)
def _validate_path(self, path: Path, root: Path) -> bool:
    """Validate that resolved path is within root directory."""
    try:
        resolved = path.resolve()
        root_resolved = root.resolve()
        # 确保解析后的路径以 root 开头
        return str(resolved).startswith(str(root_resolved))
    except (OSError, ValueError):
        return False

# 在 scan 方法中使用
for file_path in root.rglob("*"):
    if not self._validate_path(file_path, root):
        logger.warning(f"Skipping path outside root: {file_path}")
        continue
```

---

### 5.2 废弃 services 模块

**目标**: 清理 deprecated 代码

**文件清单**:
- 修改: `backend/src/services/__init__.py`
- 新增: `backend/src/services/DEPRECATED.md`

**变更详情**:

```python
# backend/src/services/__init__.py (修改)
import warnings

warnings.warn(
    "services module is deprecated and will be removed in v3.0. "
    "Use pipeline module instead.",
    DeprecationWarning,
    stacklevel=2
)
```

---

## 关于性能监控的补充说明

**背景**: 
- Docs/20-RerankEngine-Architecture.md Section 8.2 提到性能目标（P99 < 500ms, 内存 < 200MB）
- 但性能基线**不在本次修复计划范围内**

**原因**:
1. **硬件差异大**: 当前标准（如 500ms）在客户机器上难以统一衡量
2. **缺乏数据**: 需要普遍调查数据后才能建立合理基线
3. **先修复架构**: 架构合规性是前置条件，性能优化后置

**建议**:
- 修复计划完成后，通过实际使用收集性能数据
- 当有足够样本后，再建立基于百分位的性能基线
- 届时作为独立 Phase 添加到 roadmap

---

## 验证清单

每个 Phase 完成后验证:

- [ ] 所有测试通过
- [ ] 新增测试覆盖率 > 80%
- [ ] 无新的 LSP 错误
- [ ] 向后兼容 (旧接口仍可用)
- [ ] 文档已更新
- [ ] CHANGELOG.md 已更新

---

## 风险缓解

| 风险 | 缓解措施 |
|------|---------|
| 重构破坏现有功能 | 每个 Phase 前编写完整测试套件 |
| 性能回归 | 添加基准测试，对比修复前后性能 |
| 合并冲突 | 小步快跑，频繁 rebase |
| 测试不稳定 | 使用 Testcontainers 替代外部依赖 |

---

*最后更新: 2026-03-22*