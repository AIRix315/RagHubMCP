# RagHubMCP TODO

**项目名称**: RagHubMCP - 通用代码 RAG 中枢  
**创建日期**: 2026-03-19

---

## 项目定位

**核心价值**: 效果对比仪表盘 - 让用户测试、调配、找到最优配置

**核心洞察**: 模型在迅速发展，用户希望得到更好的结果。本项目与其他竞品的区别在于：竞品提供便捷的封装方案，本项目的便捷之上，把封装全部打开，让用户自己去调配。

**用户收益**:
- 测试自己最需要的配置
- 找到效果最好的组合
- 理解每个参数的影响

---

## 技术栈

| 层级 | 技术选型 |
|------|---------|
| 后端语言 | Python 3.11+ |
| 后端框架 | FastAPI |
| 协议层 | MCP (modelcontextprotocol/python-sdk) |
| 向量数据库 | Chroma |
| Rerank | FlashRank |
| 前端框架 | Vue 3 + TypeScript |
| UI 组件 | shadcn-vue |
| 状态管理 | Pinia |

---

## 参考资源

| 资源 | 链接 | 用途 |
|------|------|------|
| MCP 协议规范 | https://modelcontextprotocol.io/ | 协议规范 |
| FastMCP 框架 | https://github.com/modelcontextprotocol/python-sdk | 服务端开发 |
| chroma-mcp 源码 | https://github.com/chroma-core/chroma-mcp | 实现参考 |
| FlashRank 文档 | https://github.com/PrithivirajDamodaran/FlashRank | Rerank 集成 |
| Chroma 文档 | https://docs.trychroma.com/ | 向量数据库 |
| shadcn-vue | https://www.shadcn-vue.com/ | UI 组件 |

---

# RagHubMCP V2 开发计划

**项目名称**: RagHubMCP V2 - 面向 AI 工具的 RAG 执行基础设施  
**创建日期**: 2026-03-20  
**核心目标**: 让 RAG 从"拼工具"变成"稳定可用的基础能力"

---

## V2 核心定位

**从 V1 到 V2**:

| 维度 | V1 | V2 |
|------|----|----|
| 入口 | 多个 MCP 工具 | **单一 Pipeline** |
| MCP 接口 | 5+ 工具 | **2 个：query + ingest** |
| Rerank | 可选 | **必须（质量核心）** |
| 配置 | 参数多 | **Profile 系统** |
| 用户认知 | 需理解 RAG | **无需理解即可用** |

**一句话执行指令**: 
> "用 Pipeline 统一一切，用 Rerank 提升质量，用 Provider 保证未来"

---

## 实施策略

- ❌ 不推翻 V1
- ✅ 渐进式重构（Strangler Pattern）
- ✅ 每一步必须"可运行 + 可验证"

---

# Phase 1: 重构核心

**目标**: 在 V1 基础上重构为统一 Pipeline 架构

**包含模块**:
- Module 1: Pipeline Core（统一执行入口）
- Module 2: Rerank Integration（质量核心）
- Module 3: Provider 抽象（解耦）

---

## Module 1: Pipeline Core

**目标**: 统一所有 RAG 流程入口

### 1.1 定义 Pipeline 接口

**前置条件**: 无

- [ ] 创建 `backend/src/pipeline/__init__.py`
- [ ] 创建 `backend/src/pipeline/base.py` — 定义 RAGPipeline 抽象基类
  ```python
  class RAGPipeline(ABC):
      @abstractmethod
      async def run(self, query: str, options: dict) -> RAGResult:
          pass
  ```
- [ ] 创建 `backend/src/pipeline/result.py` — 定义 RAGResult 数据类
- [ ] 编写测试用例
- [ ] Git 提交

**验证**:
```
✅ 输入 query → 返回 docs
✅ 结果与 V1 search 一致（初期允许无 rerank）
```

**完成记录**: 待完成

---

### 1.2 实现 DefaultPipeline

**前置条件**: 1.1 完成

- [ ] 创建 `backend/src/pipeline/default.py` — 实现 DefaultRAGPipeline
  ```python
  class DefaultRAGPipeline(RAGPipeline):
      async def run(self, query, options):
          # 1. retrieval（调用现有 HybridSearch）
          docs = await self.retriever.retrieve(query)
          # 2. rerank（暂时可为空）
          if self.reranker:
              docs = await self.reranker.rerank(query, docs)
          # 3. context build（初版直接截断）
          docs = docs[:options.get("topK", 5)]
          return docs
  ```
- [ ] 创建 `backend/src/pipeline/retriever.py` — Retriever 接口
- [ ] 集成现有 `HybridSearchService` 作为默认 Retriever
- [ ] 编写测试用例
- [ ] Git 提交

**完成记录**: 待完成

---

### 1.3 Pipeline 工厂

**前置条件**: 1.2 完成

- [ ] 创建 `backend/src/pipeline/factory.py` — PipelineFactory
- [ ] 支持配置驱动创建 Pipeline
- [ ] 支持热重载
- [ ] 编写测试用例
- [ ] Git 提交

**完成记录**: 待完成

---

### Module 1 验收

**前置条件**: 1.1 - 1.3 完成

- [ ] 运行全部测试
- [ ] 更新 CHANGELOG.md
- [ ] Git 提交

**验收标准**:
```
✅ 输入 query → 返回 docs
✅ 结果与 V1 search 一致
```

**完成记录**: 待完成

---

## Module 2: Rerank Integration

**目标**: 引入"最终排序层"

### 2.1 定义 Reranker 接口

**前置条件**: Module 1 完成

- [ ] 创建 `backend/src/pipeline/reranker.py` — Reranker 抽象接口
  ```python
  class Reranker(ABC):
      @abstractmethod
      async def rerank(self, query: str, docs: list[Doc]) -> list[Doc]:
          pass
  ```
- [ ] 统一现有 `FlashRankRerankProvider` 接口
- [ ] 编写测试用例
- [ ] Git 提交

**完成记录**: 待完成

---

### 2.2 实现基础版本

**前置条件**: 2.1 完成

- [ ] FlashRank（本地）集成
- [ ] API rerank（Cohere/Jina）支持（可选）
- [ ] fallback 机制（rerank 失败时返回原始结果）
- [ ] 编写测试用例
- [ ] Git 提交

**完成记录**: 待完成

---

### 2.3 接入 Pipeline

**前置条件**: 2.2 完成

- [ ] 修改 `DefaultRAGPipeline.run()` 调用 reranker
- [ ] 添加 rerank 配置项
- [ ] 编写测试用例
- [ ] Git 提交

**完成记录**: 待完成

---

### Module 2 验收（必须做对比）

**前置条件**: 2.1 - 2.3 完成

- [ ] 运行全部测试
- [ ] 对比 V1（无 rerank）vs V2（+rerank）
- [ ] 记录 Top3 命中率
- [ ] 生成对比报告
- [ ] 更新 CHANGELOG.md
- [ ] Git 提交

**验证标准**:
```
✅ Top3 是否更相关
✅ 错误结果是否下降
✅ Top3 命中率提升 ≥ 20%
```

**完成记录**: 待完成

---

## Module 3: Provider 抽象

**目标**: 彻底解耦模型和数据库

### 3.1 定义接口

**前置条件**: Module 2 完成

- [ ] 审查现有 `backend/src/providers/vectorstore/base.py`
- [ ] 统一接口方法：
  ```python
  class VectorDBProvider(ABC):
      async def search(self, query_embedding, top_k) -> list[Doc]
      async def add(self, docs: list[Doc]) -> None
      async def delete(self, ids: list[str]) -> None
  ```
- [ ] 审查现有 `ChromaProvider`、`QdrantProvider` 实现
- [ ] 编写测试用例
- [ ] Git 提交

**完成记录**: 待完成

---

### 3.2 重构 Pipeline 使用 Provider

**前置条件**: 3.1 完成

- [ ] 修改 `Retriever` 使用 `VectorDBProvider` 接口
- [ ] 移除对 `ChromaService` 的直接依赖
  ```python
  # ❌ 不允许
  from chroma_service import ...
  
  # ✅ 必须
  vector_db.search(...)
  ```
- [ ] 验证 Chroma → Qdrant 切换无需改业务代码
- [ ] 编写测试用例
- [ ] Git 提交

**完成记录**: 待完成

---

### Module 3 验收

**前置条件**: 3.1 - 3.2 完成

- [ ] 运行全部测试
- [ ] 更新 CHANGELOG.md
- [ ] Git 提交

**验证标准**:
```
✅ 替换 Chroma → Qdrant 不改业务代码
✅ embedding 模型切换无影响
```

**完成记录**: 待完成

---

# Phase 2: 质量提升

**目标**: 提升 RAG 结果质量，降低用户复杂度

**包含模块**:
- Module 4: Context Builder（质量优化）
- Module 5: Profile 配置系统

---

## Module 4: Context Builder

**目标**: 构建"最优上下文"

### 4.1 定义 ContextBuilder 接口

**前置条件**: Phase 1 完成

- [ ] 创建 `backend/src/pipeline/context_builder.py`
  ```python
  class ContextBuilder(ABC):
      def build(self, docs: list[Doc], limit: int) -> list[Context]:
          pass
  ```
- [ ] 编写测试用例
- [ ] Git 提交

**完成记录**: 待完成

---

### 4.2 实现 DefaultContextBuilder

**前置条件**: 4.1 完成

- [ ] 创建 `backend/src/pipeline/builders/default_builder.py`
- [ ] 实现功能：
  - [ ] 去重（简单 hash）
  - [ ] 排序（按 score）
  - [ ] 截断（topK）
  - [ ] 合并（连续内容，可选）
- [ ] 接入 Pipeline
- [ ] 编写测试用例
- [ ] Git 提交

**完成记录**: 待完成

---

### Module 4 验收

**前置条件**: 4.1 - 4.2 完成

- [ ] 运行全部测试
- [ ] 更新 CHANGELOG.md
- [ ] Git 提交

**验证标准**:
```
✅ 上下文无重复
✅ 相关性更集中
✅ 长文不过长
```

**完成记录**: 待完成

---

## Module 5: Profile 配置系统

**目标**: 降低用户复杂度

### 5.1 定义 Profile

**前置条件**: Module 4 完成

- [ ] 创建 `backend/src/pipeline/profiles.py`
- [ ] 定义三种 profile：
  ```python
  PROFILES = {
      "fast": {"rerank": False, "topK": 3},
      "balanced": {"rerank": True, "topK": 5},
      "accurate": {"rerank": True, "topK": 10, "multi_query": True}
  }
  ```
- [ ] 编写测试用例
- [ ] Git 提交

**完成记录**: 待完成

---

### 5.2 接入 Pipeline

**前置条件**: 5.1 完成

- [ ] 修改 `Pipeline.run()` 支持 profile 参数
- [ ] 更新配置系统支持 profile 选择
- [ ] 编写测试用例
- [ ] Git 提交

**完成记录**: 待完成

---

### Module 5 验收

**前置条件**: 5.1 - 5.2 完成

- [ ] 运行全部测试
- [ ] 更新 CHANGELOG.md
- [ ] Git 提交

**验证标准**:
```
✅ 用户只需选 profile
✅ 不需要调参数
```

**完成记录**: 待完成

---

# Phase 3: MCP 接口收敛

**目标**: 只暴露"最终能力"

---

## 6.1 收敛 MCP 接口

**前置条件**: Phase 2 完成

- [ ] 创建 `backend/src/mcp_server/tools/v2/` 目录
- [ ] 实现 `query` 工具（调用 Pipeline）
  ```python
  @mcp.tool()
  async def query(query: str, strategy: str = "balanced") -> str:
      result = await pipeline.run(query, options[strategy])
      return result
  ```
- [ ] 实现 `ingest` 工具
  ```python
  @mcp.tool()
  async def ingest(documents: list[dict]) -> str:
      ...
  ```
- [ ] 标记旧工具为 deprecated（保留兼容）

| 保留 ✅ | 删除 ❌ |
|--------|--------|
| `query` | `search` |
| `ingest` | `rerank` |
| | `embed` |

- [ ] 编写测试用例
- [ ] Git 提交

**完成记录**: 待完成

---

## 6.2 MCP 调用 Pipeline

**前置条件**: 6.1 完成

- [ ] 确保所有 MCP 调用都经过 `pipeline.run(query)`
- [ ] 更新 MCP 配置生成器
- [ ] 编写测试用例
- [ ] Git 提交

**完成记录**: 待完成

---

## Phase 3 验收

**前置条件**: 6.1 - 6.2 完成

- [ ] 运行全部测试
- [ ] 手动测试 MCP 集成（Cursor/CherryStudio）
- [ ] 更新 CHANGELOG.md
- [ ] Git 提交

**验证标准**:
```
✅ Cursor / CherryStudio 可直接用
✅ 用户无需理解 RAG
✅ MCP 调用只需一个 query
```

**完成记录**: 待完成

---

# Phase 4: 验证体系（必须执行）

**目标**: 建立完整的质量验证机制

---

## 7.1 构建测试集

**前置条件**: Phase 3 完成

- [ ] 创建 `backend/tests/evaluation/test_questions.json`
- [ ] 至少 20 个问题：
  - 精确问题（明确的技术问题）
  - 模糊问题（开放性问题）
  - 长文问题（需要上下文理解）
- [ ] 标注每个问题的期望答案
- [ ] Git 提交

**完成记录**: 待完成

---

## 7.2 对比维度

**前置条件**: 7.1 完成

- [ ] 实现评估指标计算：

| 指标 | 说明 |
|------|------|
| TopK命中率 | 正确 chunk 是否在前 3 |
| 相关性 | 是否明显更准 |
| 噪声 | 无关内容是否减少 |

- [ ] 创建 `backend/tests/evaluation/metrics.py`
- [ ] 编写测试用例
- [ ] Git 提交

**完成记录**: 待完成

---

## 7.3 对比方式

**前置条件**: 7.2 完成

- [ ] 实现 V1（无 rerank）vs V2（+rerank + pipeline）对比脚本
- [ ] 创建 `backend/tests/evaluation/compare.py`
- [ ] 生成对比报告（Markdown 格式）
- [ ] 编写测试用例
- [ ] Git 提交

**对比方式**:
```
V1（无rerank）
VS
V2（+rerank + pipeline）
```

**完成记录**: 待完成

---

## Phase 4 验收

**前置条件**: 7.1 - 7.3 完成

- [ ] 运行全部评估测试
- [ ] 生成最终对比报告
- [ ] 更新 CHANGELOG.md
- [ ] Git 提交

**最低通过标准**:
```
✅ Top3 命中率提升 ≥ 20%
✅ 错误召回明显下降
```

**完成记录**: 待完成

---

# Phase 5: 可选增强（V2 后期）

**目标**: 进一步提升能力（非必须）

---

## 8.1 Query Rewrite（可选）

**前置条件**: Phase 4 完成

- [ ] 研究 Query Rewrite 技术
- [ ] 实现基础版本（可选接入）
- [ ] 评估效果
- [ ] Git 提交

**完成记录**: 待完成

---

## 8.2 Multi-query（可选）

**前置条件**: Phase 4 完成

- [ ] 实现 Multi-query 生成
- [ ] 集成到 accurate profile
- [ ] 评估效果
- [ ] Git 提交

**完成记录**: 待完成

---

## 8.3 简单 Eval（可选）

**前置条件**: Phase 4 完成

- [ ] 设计简单评估机制
- [ ] 实现自动评估脚本
- [ ] 集成到 CI/CD
- [ ] Git 提交

**完成记录**: 待完成

---

# 最终验收

**前置条件**: Phase 1-4 完成（Phase 5 可选）

## 验收清单

- [ ] 运行全量测试
- [ ] 运行全量评估
- [ ] 验证 MCP 集成（Cursor/CherryStudio）
- [ ] 验证 Provider 切换（Chroma ↔ Qdrant）
- [ ] 验证 Profile 切换
- [ ] 更新 CHANGELOG.md
- [ ] 更新 README.md
- [ ] Git 提交

## 最终验收标准

```
✅ MCP 调用只需一个 query
✅ 结果明显优于 V1
✅ 可切换模型/数据库
✅ 代码结构清晰（Pipeline 中心）
✅ Top3 命中率提升 ≥ 20%
```

---

## V2 成功标准

- 用户无需理解 RAG 即可使用
- 不同模型组合可稳定工作
- 检索质量明显优于 V1
- MCP 调用稳定

---

## 禁止事项

| ❌ 禁止 | 原因 |
|--------|------|
| 重写全部代码 | 渐进式重构 |
| 引入复杂 DAG | 保持简单 |
| 增加过多配置项 | 降低用户复杂度 |
| 跳过验证 | 每步必须可验证 |
| 在模块中直接依赖具体实现 | 必须通过接口 |

---

## V2 架构图

```
┌─────────────────────────────────────────────────────┐
│                   MCP / REST                         │
│              query() / ingest()                      │
└──────────────────────────┬──────────────────────────┘
                           │
┌──────────────────────────┴──────────────────────────┐
│              RAG Pipeline（统一入口）                 │
│  ┌─────────────────────────────────────────────┐    │
│  │           async run(query, profile)          │    │
│  │                     ↓                         │    │
│  │  ┌─────────┐ ┌─────────┐ ┌────────────────┐ │    │
│  │  │Retriever│→│Reranker │→│ContextBuilder  │ │    │
│  │  │(Hybrid) │ │(必须)   │ │  (质量优化)     │ │    │
│  │  └─────────┘ └─────────┘ └────────────────┘ │    │
│  └─────────────────────────────────────────────┘    │
└──────────────────────────┬──────────────────────────┘
                           │
┌──────────────────────────┴──────────────────────────┐
│                   Providers                          │
│  ┌──────────────┐ ┌──────────────┐ ┌─────────────┐  │
│  │ Embedding    │ │  VectorDB    │ │   Rerank    │  │
│  │ Provider     │ │  Provider    │ │  Provider   │  │
│  └──────────────┘ └──────────────┘ └─────────────┘  │
└─────────────────────────────────────────────────────┘
```

---

## 演进路线

```
Phase 1: 重构核心
    ├── Module 1: Pipeline Core
    ├── Module 2: Rerank Integration
    └── Module 3: Provider 抽象

Phase 2: 质量提升
    ├── Module 4: Context Builder
    └── Module 5: Profile 系统

Phase 3: MCP 收敛
    └── 收敛为 query + ingest 两个工具

Phase 4: 验证体系（必须执行）
    ├── 构建测试集（20+ 问题）
    ├── 对比维度定义
    └── V1 vs V2 对比

Phase 5: 可选增强（V2 后期）
    ├── Query Rewrite（可选）
    ├── Multi-query（可选）
    └── 简单 Eval（可选）
```

---

*最后更新: 2026-03-20*