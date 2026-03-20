# RagHub V2 实施纲领（Execution Blueprint）

## 0. 目标（必须统一认知）

本阶段目标不是“重写系统”，而是：

✅ 在 V1 基础上重构为 **统一 Pipeline 架构**
✅ 提升 RAG 结果质量（优先级 > token）
✅ 建立可扩展的基础设施（非一次性工程）

---

## 1. 总体实施策略（非常关键）

### 原则

- ❌ 不推翻 V1
- ✅ 渐进式重构（Strangler Pattern）
- ✅ 每一步必须“可运行 + 可验证”

---

### 重构路径（固定顺序）

```
Step 1: 引入 Pipeline（不动现有逻辑）
Step 2: 接入 Rerank（质量提升关键）
Step 3: 抽象 Provider（解耦）
Step 4: 引入 Context Builder
Step 5: MCP 接口收敛
```

---

## 2. 模块拆解（可直接分配任务）

---

# 🔹 Module 1：Pipeline Core（最高优先级）

## 目标

统一所有RAG流程入口

---

## 任务

### 1.1 定义接口

```python
class RAGPipeline:
    async def run(self, query: str, options: dict) -> RAGResult:
        pass
```

---

### 1.2 实现 DefaultPipeline

```python
class DefaultRAGPipeline(RAGPipeline):

    async def run(self, query, options):

        # 1. retrieval（调用现有HybridSearch）
        docs = await self.retriever.retrieve(query)

        # 2. rerank（暂时可为空）
        if self.reranker:
            docs = await self.reranker.rerank(query, docs)

        # 3. context build（初版可直接截断）
        docs = docs[:options.get("topK", 5)]

        return docs
```

---

## 验证

✅ 输入query → 返回docs
✅ 结果与V1 search一致（初期允许无rerank）

---

# 🔹 Module 2：Rerank Integration（质量核心）

## 目标

引入“最终排序层”

---

## 任务

### 2.1 定义接口

```python
class Reranker:
    async def rerank(self, query, docs):
        pass
```

---

### 2.2 实现基础版本

- FlashRank（本地）
- API rerank（可选）

---

### 2.3 接入Pipeline

```python
docs = reranker.rerank(query, docs)
```

---

## 验证（必须做对比）

- 对同一query：
  - V1结果
  - V2（+rerank）

✅ Top3是否更相关
✅ 错误结果是否下降

---

# 🔹 Module 3：Provider抽象（防止未来爆炸）

## 目标

彻底解耦模型和数据库

---

## 任务

### 3.1 定义接口

```python
class EmbeddingProvider
class VectorDBProvider
class RerankProvider
```

---

### 3.2 重构现有代码

❌ 不允许：

```python
from chroma_service import ...
```

✅ 必须：

```python
vector_db.search(...)
```

---

## 验证

✅ 替换Chroma → Qdrant不改业务代码
✅ embedding模型切换无影响

---

# 🔹 Module 4：Context Builder（质量优化）

## 目标

构建“最优上下文”

---

## 任务

### 4.1 定义接口

```python
class ContextBuilder:
    def build(self, docs, limit=5):
        pass
```

---

### 4.2 初版实现

- 去重（简单hash）
- 截断（topK）
- 按score排序

---

## 验证

✅ 上下文无重复
✅ 相关性更集中
✅ 长文不过长

---

# 🔹 Module 5：MCP接口重构

## 目标

只暴露“最终能力”

---

## 任务

### 5.1 收敛接口

✅ 保留：

- query
- ingest

❌ 删除：

- search
- rerank
- embed

---

### 5.2 MCP调用Pipeline

```python
result = pipeline.run(query)
```

---

## 验证

✅ Cursor / CherryStudio 可直接用
✅ 用户无需理解RAG

---

# 🔹 Module 6：Profile配置系统

## 目标

降低用户复杂度

---

## 任务

定义：

```json
{
  "balanced": {
    "rerank": true,
    "topK": 5
  }
}
```

---

## 验证

✅ 用户只需选 profile
✅ 不需要调参数

---

## 3. 验证体系（必须执行）

---

### ✅ 1. 构建测试集

至少20个问题：

- 精确问题
- 模糊问题
- 长文问题

---

### ✅ 2. 对比维度

| 指标 | 说明 |
|------|------|
| TopK命中率 | 正确chunk是否在前3 |
| 相关性 | 是否明显更准 |
| 噪声 | 无关内容是否减少 |

---

### ✅ 3. 对比方式

```
V1（无rerank）
VS
V2（+rerank + pipeline）
```

---

### ✅ 4. 最低通过标准

- Top3命中率提升 ≥ 20%
- 错误召回明显下降

---

## 4. 任务编排（给模型用）

---

### 阶段1（1-2天）

- ✅ Pipeline骨架
- ✅ 接入现有retrieval

---

### 阶段2（2-3天）

- ✅ Rerank接入
- ✅ 对比测试

---

### 阶段3（2天）

- ✅ Provider重构

---

### 阶段4（1-2天）

- ✅ Context Builder

---

### 阶段5（1天）

- ✅ MCP收敛

---

## 5. 禁止事项（必须遵守）

❌ 不允许重写全部代码
❌ 不允许引入复杂DAG
❌ 不允许增加过多配置项
❌ 不允许跳过验证

---

## 6. 最终验收标准

✅ MCP调用只需一个query
✅ 结果明显优于V1
✅ 可切换模型/数据库
✅ 代码结构清晰（pipeline中心）

---

## 7. 一句话执行指令

> **“用Pipeline统一一切，用Rerank提升质量，用Provider保证未来”**

