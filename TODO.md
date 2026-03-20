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

## Phase V2.1: Pipeline Core（最高优先级）

### V2.1.1 定义 Pipeline 接口

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
  ```python
  @dataclass
  class RAGResult:
      contexts: list[Context]
      metadata: dict
      latency_ms: float
  ```
- [ ] 编写测试用例
- [ ] Git 提交

**测试用例**:
```
TC-V2.1.1.1: RAGPipeline 抽象类不可直接实例化
TC-V2.1.1.2: RAGResult 数据类正确初始化
TC-V2.1.1.3: RAGResult contexts 可迭代
```

**完成记录**: 待完成

---

### V2.1.2 实现 DefaultPipeline

**前置条件**: V2.1.1 完成

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

**测试用例**:
```
TC-V2.1.2.1: DefaultPipeline 可实例化
TC-V2.1.2.2: run() 返回 RAGResult
TC-V2.1.2.3: 结果与 V1 search 一致（初期无 rerank）
TC-V2.1.2.4: topK 参数生效
TC-V2.1.2.5: 空查询返回空结果
```

**完成记录**: 待完成

---

### V2.1.3 Pipeline 工厂

**前置条件**: V2.1.2 完成

- [ ] 创建 `backend/src/pipeline/factory.py` — PipelineFactory
- [ ] 支持配置驱动创建 Pipeline
- [ ] 支持热重载
- [ ] 编写测试用例
- [ ] Git 提交

**测试用例**:
```
TC-V2.1.3.1: 工厂创建 DefaultPipeline
TC-V2.1.3.2: 配置变更后重新创建
TC-V2.1.3.3: 单例模式正确
```

**完成记录**: 待完成

---

### V2.1.4 Phase V2.1 验收

**前置条件**: V2.1.1 - V2.1.3 完成

- [ ] 运行全部测试
- [ ] 更新 CHANGELOG.md
- [ ] Git 提交

**验收标准**:
```
AC-V2.1.1: 所有 TC-V2.1.x.x 测试通过
AC-V2.1.2: 输入 query → 返回 docs
AC-V2.1.3: 结果与 V1 search 一致
```

**完成记录**: 待完成

---

## Phase V2.2: Rerank Integration（质量核心）

**目标**: 引入"最终排序层"  

### V2.2.1 定义 Reranker 接口

**前置条件**: V2.1 完成

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

**测试用例**:
```
TC-V2.2.1.1: Reranker 抽象类不可直接实例化
TC-V2.2.1.2: rerank 返回排序后的 docs
TC-V2.2.1.3: score 在有效范围
```

**完成记录**: 待完成

---

### V2.2.2 接入 Pipeline

**前置条件**: V2.2.1 完成

- [ ] 修改 `DefaultRAGPipeline.run()` 调用 reranker
- [ ] 添加 rerank 配置项
- [ ] 支持 fallback（rerank 失败时返回原始结果）
- [ ] 编写测试用例
- [ ] Git 提交

**测试用例**:
```
TC-V2.2.2.1: rerank 后结果顺序改变
TC-V2.2.2.2: rerank_top_k 参数生效
TC-V2.2.2.3: rerank 失败时 fallback
TC-V2.2.2.4: 空文档列表返回空结果
```

**完成记录**: 待完成

---

### V2.2.3 对比测试（必须执行）

**前置条件**: V2.2.2 完成

- [ ] 创建 `backend/tests/test_pipeline/test_comparison.py`
- [ ] 构建测试问题集（至少 20 个问题）
- [ ] 对比 V1（无 rerank）vs V2（+rerank）
- [ ] 记录 Top3 命中率
- [ ] 生成对比报告
- [ ] Git 提交

**测试用例**:
```
TC-V2.2.3.1: Top3 命中率提升 ≥ 20%
TC-V2.2.3.2: 错误召回明显下降
TC-V2.2.3.3: 延迟可接受（< 500ms）
```

**完成记录**: 待完成

---

### V2.2.4 Phase V2.2 验收

**前置条件**: V2.2.1 - V2.2.3 完成

- [ ] 运行全部测试
- [ ] 更新 CHANGELOG.md
- [ ] Git 提交

**验收标准**:
```
AC-V2.2.1: 所有 TC-V2.2.x.x 测试通过
AC-V2.2.2: Top3 命中率提升 ≥ 20%
AC-V2.2.3: 错误召回明显下降
```

**完成记录**: 待完成

---

## Phase V2.3: Provider 抽象（解耦）

**目标**: 彻底解耦模型和数据库  
**预计时间**: 2 天

### V2.3.1 定义 VectorDBProvider 接口

**前置条件**: V2.2 完成

- [ ] 创建 `backend/src/providers/vectorstore/base.py`（已存在，需审查）
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

**测试用例**:
```
TC-V2.3.1.1: VectorDBProvider 接口完整
TC-V2.3.1.2: ChromaProvider 实现正确
TC-V2.3.1.3: QdrantProvider 实现正确
```

**完成记录**: 待完成

---

### V2.3.2 重构 Pipeline 使用 Provider

**前置条件**: V2.3.1 完成

- [ ] 修改 `Retriever` 使用 `VectorDBProvider` 接口
- [ ] 移除对 `ChromaService` 的直接依赖
- [ ] 验证 Chroma → Qdrant 切换无需改业务代码
- [ ] 编写测试用例
- [ ] Git 提交

**测试用例**:
```
TC-V2.3.2.1: 替换 Chroma → Qdrant 不改业务代码
TC-V2.3.2.2: embedding 模型切换无影响
TC-V2.3.2.3: Provider 工厂正确创建实例
```

**完成记录**: 待完成

---

### V2.3.3 Phase V2.3 验收

**前置条件**: V2.3.1 - V2.3.2 完成

- [ ] 运行全部测试
- [ ] 更新 CHANGELOG.md
- [ ] Git 提交

**验收标准**:
```
AC-V2.3.1: 所有 TC-V2.3.x.x 测试通过
AC-V2.3.2: Chroma ↔ Qdrant 切换无业务代码改动
AC-V2.3.3: embedding 模型切换无影响
```

**完成记录**: 待完成

---

## Phase V2.4: Context Builder（质量优化）

**目标**: 构建"最优上下文"  
**预计时间**: 1-2 天

### V2.4.1 定义 ContextBuilder 接口

**前置条件**: V2.3 完成

- [ ] 创建 `backend/src/pipeline/context_builder.py`
  ```python
  class ContextBuilder(ABC):
      def build(self, docs: list[Doc], limit: int) -> list[Context]:
          pass
  ```
- [ ] 编写测试用例
- [ ] Git 提交

**测试用例**:
```
TC-V2.4.1.1: ContextBuilder 抽象类不可直接实例化
TC-V2.4.1.2: build 返回指定数量的 contexts
```

**完成记录**: 待完成

---

### V2.4.2 实现 DefaultContextBuilder

**前置条件**: V2.4.1 完成

- [ ] 创建 `backend/src/pipeline/builders/default_builder.py`
- [ ] 实现功能：
  - [ ] 去重（简单 hash）
  - [ ] 排序（按 score）
  - [ ] 截断（topK）
  - [ ] 合并（连续内容，可选）
- [ ] 接入 Pipeline
- [ ] 编写测试用例
- [ ] Git 提交

**测试用例**:
```
TC-V2.4.2.1: 去重功能正确
TC-V2.4.2.2: 按 score 降序排列
TC-V2.4.2.3: limit 参数生效
TC-V2.4.2.4: 上下文无重复
TC-V2.4.2.5: 相关性更集中
```

**完成记录**: 待完成

---

### V2.4.3 Phase V2.4 验收

**前置条件**: V2.4.1 - V2.4.2 完成

- [ ] 运行全部测试
- [ ] 更新 CHANGELOG.md
- [ ] Git 提交

**验收标准**:
```
AC-V2.4.1: 所有 TC-V2.4.x.x 测试通过
AC-V2.4.2: 上下文无重复
AC-V2.4.3: 相关性更集中
```

**完成记录**: 待完成

---

## Phase V2.5: MCP 接口收敛

**目标**: 只暴露"最终能力"  
**预计时间**: 1 天

### V2.5.1 收敛 MCP 接口

**前置条件**: V2.4 完成

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
- [ ] 编写测试用例
- [ ] Git 提交

**测试用例**:
```
TC-V2.5.1.1: query 工具返回结果
TC-V2.5.1.2: ingest 工具返回成功
TC-V2.5.1.3: strategy 参数生效
TC-V2.5.1.4: Cursor / CherryStudio 可直接用
```

**完成记录**: 待完成

---

### V2.5.2 更新 MCP 配置生成器

**前置条件**: V2.5.1 完成

- [ ] 更新 `scripts/config/generate-mcp-config.py`
- [ ] 添加 V2 工具说明
- [ ] 编写测试用例
- [ ] Git 提交

**完成记录**: 待完成

---

### V2.5.3 Phase V2.5 验收

**前置条件**: V2.5.1 - V2.5.2 完成

- [ ] 运行全部测试
- [ ] 手动测试 MCP 集成（Cursor/CherryStudio）
- [ ] 更新 CHANGELOG.md
- [ ] Git 提交

**验收标准**:
```
AC-V2.5.1: 所有 TC-V2.5.x.x 测试通过
AC-V2.5.2: MCP 调用只需一个 query
AC-V2.5.3: 用户无需理解 RAG
```

**完成记录**: 待完成

---

## Phase V2.6: Profile 配置系统

**目标**: 降低用户复杂度  
**预计时间**: 1 天

### V2.6.1 定义 Profile

**前置条件**: V2.5 完成

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

**测试用例**:
```
TC-V2.6.1.1: fast profile 正确加载
TC-V2.6.1.2: balanced profile 正确加载
TC-V2.6.1.3: accurate profile 正确加载
TC-V2.6.1.4: 无效 profile 报错
```

**完成记录**: 待完成

---

### V2.6.2 接入 Pipeline

**前置条件**: V2.6.1 完成

- [ ] 修改 `Pipeline.run()` 支持 profile 参数
- [ ] 更新 `query` 工具支持 profile 选择
- [ ] 编写测试用例
- [ ] Git 提交

**测试用例**:
```
TC-V2.6.2.1: profile 参数生效
TC-V2.6.2.2: 不同 profile 结果不同
```

**完成记录**: 待完成

---

### V2.6.3 Phase V2.6 验收

**前置条件**: V2.6.1 - V2.6.2 完成

- [ ] 运行全部测试
- [ ] 更新 CHANGELOG.md
- [ ] Git 提交

**验收标准**:
```
AC-V2.6.1: 所有 TC-V2.6.x.x 测试通过
AC-V2.6.2: 用户只需选 profile
AC-V2.6.3: 不需要调参数
```

**完成记录**: 待完成

---

## Phase V2.7: 最终验收

**前置条件**: V2.1 - V2.6 全部完成

### 验收清单

- [ ] 运行全量测试
- [ ] 构建 20+ 测试问题集
- [ ] 对比 V1 vs V2 结果质量
- [ ] 验证 MCP 集成（Cursor/CherryStudio）
- [ ] 验证 Provider 切换（Chroma ↔ Qdrant）
- [ ] 验证 Profile 切换
- [ ] 更新 CHANGELOG.md
- [ ] 更新 README.md
- [ ] Git 提交

**最终验收标准**:
```
AC-V2.7.1: MCP 调用只需一个 query ✅
AC-V2.7.2: 结果明显优于 V1 ✅
AC-V2.7.3: 可切换模型/数据库 ✅
AC-V2.7.4: 代码结构清晰（Pipeline 中心） ✅
AC-V2.7.5: Top3 命中率提升 ≥ 20% ✅
```

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

*最后更新: 2026-03-20*