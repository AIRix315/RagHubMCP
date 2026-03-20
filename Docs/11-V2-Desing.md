# V2 Design

- 核心：Python ✅
- UI：TS ✅
- MCP：Python ✅

## 正确策略（非常关键）

**“核心Python + 外层TS”**

### 分层：

```
Core Engine（Python）✅
    - pipeline
    - retrieval
    - rerank

Adapters（Python）
    - MCP
    - REST

UI（TS）
    - 配置界面
```

# 在V1上做结构重构

## 核心原则：

**不动已有能力，只加“壳”统一它**

---

# 最终版 V2 计划（给你标准.md）

# RagHub V2 Design（最终落地版）

## 1. 核心定位

RagHub V2 是一个：

**面向AI工具（MCP）的RAG执行基础设施**

目标：

- 提供稳定、高质量的知识检索结果
- 支持任意模型（本地 / API）
- 支持任意向量数据库
- 降低用户对RAG的理解成本

---

## 2. 设计原则

- Pipeline First（统一执行入口）
- Quality First（优先结果质量，而非Token节省）
- Provider Decoupled（模型与数据库解耦）
- Simple Config（用户只做少量选择）
- MCP Native（面向AI工具调用）

---

## 3. 系统架构

```
UI (TS)
  ↓
Config Layer
  ↓
RAG Pipeline（Python核心）
  ↓
Retrieval → Rerank → Context Builder
  ↓
Providers（Embedding / DB / Rerank）

Adapters:
- MCP（核心入口）
- REST（辅助）
```

---

## 4. Pipeline设计（核心）

### 4.1 接口

```python
class RAGPipeline:
    async def run(self, query: str, options: dict) -> RAGResult:
        ...
```

---

### 4.2 执行流程

```
1. Query Normalize（可选）
2. Retrieval（Hybrid）
3. Rerank（必须）
4. Context Builder（质量优化）
5. 返回contexts
```

---

## 5. Retrieval设计

### 支持：

- Vector Search
- BM25
- Hybrid（RRF）

### 可选增强（V2后期）：

- Query Rewrite
- Multi-query

---

## 6. Rerank设计（核心能力）

```python
class Reranker:
    async def rerank(query, docs) -> List[Doc]
```

支持：

- 本地模型
- API模型（Cohere / Jina）
- fallback机制

---

## 7. Context Builder（关键升级）

### 目标：

构建“最优上下文”，而非压缩Token

### 功能：

- 去重（相似chunk）
- 排序（按相关性）
- 截断（控制长度）
- 合并（连续内容）

---

## 8. Provider抽象

统一接口：

```python
EmbeddingProvider
RerankProvider
VectorDBProvider
```

要求：

- 可替换
- 配置驱动
- 不与具体实现耦合

---

## 9. MCP接口设计

### 仅提供两个核心能力：

#### query

```json
{
  "query": "...",
  "strategy": "balanced"
}
```

---

#### ingest

```json
{
  "documents": [...]
}
```

---

## 10. 配置系统（Profile）

用户只需选择：

- embedding模型
- rerank模型
- 数据库
- profile（fast / balanced / accurate）

---

## 11. UI设计（轻量）

必须提供：

- 配置切换
- 模型选择
- Debug模式（检索 & rerank可视化）

---

## 12. 技术选型

### Core

- Python ✅（核心引擎）

### UI

- TypeScript ✅

### MCP

- Python ✅

---

## 13. 演进路线

### Phase 1（重构核心）

- 引入Pipeline ✅
- 接入Rerank ✅
- MCP统一query ✅

---

### Phase 2（质量提升）

- Context Builder ✅
- Profile系统 ✅

---

### Phase 3（增强能力）

- Multi-query
- 简单Eval

---

## 14. 验证方法（必须执行）

### 指标：

- TopK命中率
- 用户问题命中准确率
- Rerank前后对比

### 方法：

- 构建测试问题集
- 对比不同配置结果
- 记录命中率变化

---

## 15. 成功标准

- 用户无需理解RAG即可使用
- 不同模型组合可稳定工作
- 检索质量明显优于V1
- MCP调用稳定

---

## 16. 总结

RagHub V2 的目标是：

- **让RAG从“拼工具”变成“稳定可用的基础能力”**

- **不要追求“更先进”.要做到：“AI用你这个，比不用更稳定、更准”**

