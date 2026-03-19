# Code-RAG Hub MVP 范围与实现路径

**文档版本**: v1.0  
**分析日期**: 2026-03-19  
**关联文档**: 01-RagHubMCP_20260319.md, 02-RagHubMCP-Tech_20260319.md  

---

## 📋 目录

1. [现状分析](#一现状分析)
2. [核心价值定位](#二核心价值定位)
3. [MVP 范围定义](#三mvp-范围定义)
4. [技术实现路径](#四技术实现路径)
5. [项目结构](#五项目结构)
6. [下一步行动](#六下一步行动)

---

## 一、现状分析

### 1.1 已有基础

| 组件 | 状态 | 说明 |
|------|------|------|
| **Chroma MCP** | ✅ 已配置 | 官方 chroma-mcp (515 stars) |
| **Opencode** | ✅ 可用 | 已配置 MCP，可调用工具 |
| **VS Code** | ✅ 可用 | 开源 IDE，MCP 支持 |
| **Rerank** | ❌ 缺失 | chroma-mcp 不提供此能力 |

### 1.2 Chroma 官方 MCP 工具清单

chroma-mcp (v0.2.6) 提供的工具：

| 工具名 | 功能 | 状态 |
|--------|------|------|
| `chroma_list_collections` | 列出所有 Collection | ✅ 可用 |
| `chroma_create_collection` | 创建 Collection | ✅ 可用 |
| `chroma_peek_collection` | 预览 Collection 内容 | ✅ 可用 |
| `chroma_get_collection_info` | 获取 Collection 信息 | ✅ 可用 |
| `chroma_get_collection_count` | 获取文档数量 | ✅ 可用 |
| `chroma_modify_collection` | 修改 Collection | ✅ 可用 |
| `chroma_fork_collection` | 复制 Collection | ✅ 可用 |
| `chroma_delete_collection` | 删除 Collection | ✅ 可用 |
| `chroma_add_documents` | 添加文档 | ✅ 可用 |
| `chroma_query_documents` | 查询文档（向量搜索） | ✅ 可用 |
| `chroma_get_documents` | 获取文档 | ✅ 可用 |
| `chroma_update_documents` | 更新文档 | ✅ 可用 |
| `chroma_delete_documents` | 删除文档 | ✅ 可用 |

**关键缺失**:
- ❌ **没有 Rerank 能力**
- ❌ 没有效果对比功能
- ❌ 没有配置管理界面

### 1.3 chroma-mcp 源码分析

```python
# 核心架构：FastMCP 框架
from mcp.server.fastmcp import FastMCP
mcp = FastMCP("chroma")

# 工具定义示例
@mcp.tool()
async def chroma_query_documents(
    collection_name: str,
    query_texts: List[str],
    n_results: int = 5,
    where: Dict | None = None,
    where_document: Dict | None = None,
    include: List[str] = ["documents", "metadatas", "distances"]
) -> Dict:
    """Query documents using semantic search."""
    # ... 实现
```

**扩展思路**:
1. Fork chroma-mcp 添加 Rerank 工具
2. 或创建独立 MCP Server 提供 Rerank 能力
3. Web 控制台独立部署，通过 API 管理

---

## 二、核心价值定位

### 2.1 项目定位澄清

基于讨论，明确项目定位：

```
┌─────────────────────────────────────────────────────────────────┐
│                    Code-RAG Hub 核心价值                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  "效果对比仪表盘" - RAG 检索效果的基准测试/对比平台              │
│                                                                  │
│  核心问题：                                                      │
│  "同一个代码库，用哪种组合效果最好？"                            │
│                                                                  │
│  对比维度：                                                      │
│  ├── 向量数据库：Chroma vs Qdrant vs ...                        │
│  ├── Embedding 模型：bge-m3 vs nomic vs openai-small vs ...    │
│  ├── Rerank 模型：FlashRank vs Cohere vs Jina vs ...           │
│  └── 检索策略：纯向量 vs 混合 vs ...                            │
│                                                                  │
│  产出：                                                          │
│  "针对你的代码库，推荐使用 X + Y + Z 组合"                       │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 用户使用场景

```
场景：开发者有一个代码库，想知道如何配置 RAG 效果最好

步骤：
1. 通过 Web 控制台配置代码库路径
2. 选择测试组合（Embedding + Rerank）
3. 系统自动索引并测试
4. 仪表盘展示对比结果：
   - 检索准确率（可用标注数据评估）
   - 检索延迟
   - Token 消耗
   - 资源占用
5. 推荐最优配置
6. 一键生成 MCP 配置文件
```

### 2.3 与现有工具的关系

| 工具 | 定位 | 与本项目关系 |
|------|------|-------------|
| **Chroma MCP** | 向量存储 | 底层依赖，本项目增强其能力 |
| **Opencode** | IDE + AI | 本项目的使用场景/客户端 |
| **FlashRank** | Rerank 库 | 本项目集成的核心能力 |

**本项目不是替代 Chroma MCP，而是：**
1. **增强**：添加 Rerank 能力
2. **管理**：提供 Web 配置界面
3. **对比**：提供效果基准测试
4. **推荐**：提供最优配置建议

---

## 三、MVP 范围定义

### 3.1 MVP 功能范围

基于讨论确认的 MVP 范围：

```
┌─────────────────────────────────────────────────────────────────┐
│                        MVP 功能范围                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ✅ 核心能力层（必须有）                                         │
│  ├── MCP Server：提供 Rerank 工具                               │
│  ├── 代码索引：支持 Python/TypeScript                           │
│  └── 检索 API：search_code + rerank                             │
│                                                                  │
│  ✅ Web 控制台（您定义的 MVP）                                   │
│  ├── 数据库配置：Chroma 连接管理                                │
│  ├── 模型选择：Embedding + Rerank 配置                          │
│  ├── 参数配置：切分大小、检索数量等                             │
│  └── Collection 管理：查看/删除/统计                            │
│                                                                  │
│  ✅ 效果对比（核心价值）                                         │
│  ├── 基准测试：不同组合对比                                     │
│  ├── 指标展示：延迟、准确率等                                    │
│  └── 配置推荐：最优组合建议                                      │
│                                                                  │
│  ⚠️ 简化实现                                                    │
│  ├── 仪表盘：基础指标展示（详细统计 Phase 2）                    │
│  └── 可视化：简单图表（复杂可视化 Phase 2）                      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 功能优先级矩阵

| 功能 | 优先级 | MVP 必须 | 说明 |
|------|--------|---------|------|
| **Rerank MCP 工具** | P0 | ✅ | 核心能力，Chroma MCP 没有 |
| **代码索引** | P0 | ✅ | 基础能力 |
| **检索 API** | P0 | ✅ | 基础能力 |
| **Web 配置界面** | P0 | ✅ | 用户交互入口 |
| **数据库配置** | P0 | ✅ | 连接 Chroma |
| **模型选择** | P0 | ✅ | Embedding + Rerank |
| **参数配置** | P0 | ✅ | 切分参数等 |
| **Collection 查看** | P1 | ✅ | 基础管理 |
| **效果对比仪表盘** | P1 | ✅ | 核心价值，简化版 |
| **详细统计** | P2 | ❌ | Phase 2 |
| **复杂可视化** | P2 | ❌ | Phase 2 |

### 3.3 MVP 不包含

| 功能 | 原因 | 计划 |
|------|------|------|
| 多向量库支持 | MVP 聚焦 Chroma | Phase 2 支持 Qdrant |
| AST 切分 | 开发成本高 | 作为可选插件 |
| 团队协作 | 企业级功能 | Phase 3 |
| CI/CD 集成 | 非核心场景 | Phase 3 |

---

## 四、技术实现路径

### 4.1 架构设计

```
┌─────────────────────────────────────────────────────────────────┐
│                        架构总览                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Opencode / VS Code / Cursor                                    │
│         │                                                        │
│         │ MCP 协议                                               │
│         ▼                                                        │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  Code-RAG Hub MCP Server (本项目)                        │    │
│  │  ├── chroma_query_with_rerank  # 新增：带 Rerank 的查询  │    │
│  │  ├── rerank_documents          # 新增：独立 Rerank 工具  │    │
│  │  ├── benchmark_search          # 新增：效果对比测试      │    │
│  │  └── (复用 chroma-mcp 现有工具)                          │    │
│  └─────────────────────────────────────────────────────────┘    │
│         │                                                        │
│         ▼                                                        │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  Web 控制台 (Vue3 + shadcn-vue)                          │    │
│  │  ├── 配置管理：数据库、模型、参数                         │    │
│  │  ├── Collection 管理：查看、删除                          │    │
│  │  └── 效果对比仪表盘：基准测试结果                         │    │
│  └─────────────────────────────────────────────────────────┘    │
│         │                                                        │
│         ▼                                                        │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  后端服务 (FastAPI)                                       │    │
│  │  ├── REST API：管理操作                                   │    │
│  │  ├── MCP Server：工具提供                                 │    │
│  │  └── Rerank 服务：FlashRank 集成                          │    │
│  └─────────────────────────────────────────────────────────┘    │
│         │                                                        │
│         ▼                                                        │
│  Chroma (向量存储) + FlashRank (Rerank)                         │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 4.2 MCP 工具设计

#### 新增工具 1：`chroma_query_with_rerank`

```python
@mcp.tool()
async def chroma_query_with_rerank(
    collection_name: str,
    query_text: str,
    n_results: int = 10,
    rerank_top_k: int = 5,
    rerank_model: str = "ms-marco-TinyBERT-L-2-v2",
    where: Dict | None = None,
    include: List[str] = ["documents", "metadatas", "scores"]
) -> Dict:
    """
    查询文档并使用 Rerank 重排序。
    
    流程：
    1. 调用 Chroma 向量检索，获取 n_results 个候选
    2. 使用 FlashRank 对候选进行重排序
    3. 返回 rerank_top_k 个最相关结果
    
    Args:
        collection_name: Collection 名称
        query_text: 查询文本
        n_results: 初始检索数量（召回数）
        rerank_top_k: Rerank 后返回数量
        rerank_model: Rerank 模型名称
        where: 元数据过滤条件
        include: 返回字段
    """
    # Step 1: 向量检索
    collection = client.get_collection(collection_name)
    results = collection.query(
        query_texts=[query_text],
        n_results=n_results,
        where=where,
        include=["documents", "metadatas", "distances"]
    )
    
    # Step 2: Rerank
    from flashrank import Ranker, RerankRequest
    
    ranker = Ranker(model_name=rerank_model)
    passages = [
        {"id": i, "text": doc, "meta": meta}
        for i, (doc, meta) in enumerate(zip(
            results["documents"][0],
            results["metadatas"][0]
        ))
    ]
    
    rerank_request = RerankRequest(query=query_text, passages=passages)
    reranked = ranker.rerank(rerank_request)
    
    # Step 3: 返回 top_k
    return {
        "ids": [[r["id"] for r in reranked[:rerank_top_k]]],
        "documents": [[r["text"] for r in reranked[:rerank_top_k]]],
        "metadatas": [[r["meta"] for r in reranked[:rerank_top_k]]],
        "scores": [[r["score"] for r in reranked[:rerank_top_k]]]
    }
```

#### 新增工具 2：`benchmark_search_config`

```python
@mcp.tool()
async def benchmark_search_config(
    collection_name: str,
    test_queries: List[Dict],  # [{"query": "...", "expected_ids": [...]}]
    configs: List[Dict],  # [{"name": "...", "rerank_model": "...", "n_results": ...}]
) -> Dict:
    """
    对比不同检索配置的效果。
    
    Args:
        collection_name: Collection 名称
        test_queries: 测试查询列表（含期望结果）
        configs: 配置列表
    
    Returns:
        各配置的效果对比结果
    """
    results = []
    
    for config in configs:
        config_results = {
            "name": config["name"],
            "latency_ms": [],
            "recall": [],
            "mrr": []  # Mean Reciprocal Rank
        }
        
        for test in test_queries:
            start_time = time.time()
            
            # 执行检索
            search_result = await chroma_query_with_rerank(
                collection_name=collection_name,
                query_text=test["query"],
                n_results=config.get("n_results", 10),
                rerank_top_k=config.get("rerank_top_k", 5),
                rerank_model=config.get("rerank_model", "default")
            )
            
            latency = (time.time() - start_time) * 1000
            config_results["latency_ms"].append(latency)
            
            # 计算 Recall 和 MRR
            returned_ids = set(search_result["ids"][0])
            expected_ids = set(test["expected_ids"])
            
            recall = len(returned_ids & expected_ids) / len(expected_ids)
            config_results["recall"].append(recall)
            
            # MRR 计算
            for rank, id in enumerate(search_result["ids"][0]):
                if id in expected_ids:
                    config_results["mrr"].append(1 / (rank + 1))
                    break
            else:
                config_results["mrr"].append(0)
        
        # 计算平均值
        config_results["avg_latency_ms"] = sum(config_results["latency_ms"]) / len(config_results["latency_ms"])
        config_results["avg_recall"] = sum(config_results["recall"]) / len(config_results["recall"])
        config_results["avg_mrr"] = sum(config_results["mrr"]) / len(config_results["mrr"])
        
        results.append(config_results)
    
    return {
        "benchmark_results": results,
        "recommendation": max(results, key=lambda x: x["avg_mrr"])
    }
```

### 4.3 FlashRank 集成

**推荐模型选择**:

| 模型 | 大小 | 适用场景 | 推荐度 |
|------|------|---------|--------|
| `ms-marco-TinyBERT-L-2-v2` | ~4MB | 快速、轻量 | ⭐⭐⭐⭐⭐ 默认 |
| `ms-marco-MiniLM-L-12-v2` | ~34MB | 最佳效果 | ⭐⭐⭐⭐ |
| `ms-marco-MultiBERT-L-12` | ~150MB | 多语言 | ⭐⭐⭐ |
| `rank-T5-flan` | ~110MB | Zero-shot | ⭐⭐⭐ |

**集成代码**:

```python
# providers/rerank/flashrank.py
from flashrank import Ranker, RerankRequest
from typing import List, Dict
from ..base import RerankProvider, ScoredDocument

class FlashRankReranker(RerankProvider):
    def __init__(self, model_name: str = "ms-marco-TinyBERT-L-2-v2"):
        self.ranker = Ranker(model_name=model_name)
    
    async def rerank(
        self, 
        query: str, 
        documents: List[str],
        top_k: int = 5
    ) -> List[ScoredDocument]:
        passages = [
            {"id": i, "text": doc}
            for i, doc in enumerate(documents)
        ]
        
        request = RerankRequest(query=query, passages=passages)
        results = self.ranker.rerank(request)
        
        return [
            ScoredDocument(
                document=r["text"],
                score=r["score"],
                index=r["id"]
            )
            for r in results[:top_k]
        ]
```

### 4.4 Web 控制台设计

**页面结构**:

```
Web 控制台 (Vue3 + shadcn-vue)
│
├── 首页
│   └── 系统状态概览
│
├── 配置管理
│   ├── 数据库配置
│   │   ├── Chroma 连接设置
│   │   └── 测试连接
│   │
│   ├── 模型配置
│   │   ├── Embedding 模型选择
│   │   ├── Rerank 模型选择
│   │   └── 参数调整
│   │
│   └── 索引配置
│       ├── 代码目录
│       ├── 文件类型过滤
│       └── 切分参数
│
├── Collection 管理
│   ├── Collection 列表
│   ├── 文档统计
│   └── 删除/清空
│
├── 效果对比 (核心页面)
│   ├── 测试配置
│   │   ├── 选择对比维度
│   │   └── 上传测试查询
│   │
│   ├── 运行测试
│   │
│   └── 结果展示
│       ├── 对比表格
│       ├── 延迟图表
│       └── 推荐配置
│
└── 设置
    └── MCP 配置导出
```

---

## 五、项目结构

```
coderag-hub/
│
├── backend/                          # 后端服务
│   ├── src/
│   │   ├── main.py                   # FastAPI 入口
│   │   ├── config.py                 # 配置管理
│   │   │
│   │   ├── mcp/                      # MCP Server
│   │   │   ├── __init__.py
│   │   │   ├── server.py             # MCP Server 实现
│   │   │   └── tools/
│   │   │       ├── __init__.py
│   │   │       ├── query_with_rerank.py  # 带 Rerank 的查询
│   │   │       ├── benchmark.py          # 效果对比测试
│   │   │       └── collection.py         # Collection 管理
│   │   │
│   │   ├── providers/                # 模型 Provider
│   │   │   ├── __init__.py
│   │   │   ├── base.py
│   │   │   ├── embedding/            # Embedding Provider
│   │   │   └── rerank/               # Rerank Provider
│   │   │       ├── __init__.py
│   │   │       ├── flashrank.py      # FlashRank 实现
│   │   │       └── cohere.py         # Cohere API (可选)
│   │   │
│   │   ├── indexer/                  # 代码索引
│   │   │   ├── __init__.py
│   │   │   ├── scanner.py            # 文件扫描
│   │   │   └── chunker.py            # 代码切分
│   │   │
│   │   └── api/                      # REST API
│   │       ├── __init__.py
│   │       ├── routes.py
│   │       └── schemas.py
│   │
│   ├── tests/
│   ├── pyproject.toml
│   └── config.yaml
│
├── frontend/                         # Web 控制台
│   ├── src/
│   │   ├── App.vue
│   │   ├── main.ts
│   │   ├── components/
│   │   │   ├── layout/
│   │   │   ├── config/
│   │   │   ├── collection/
│   │   │   └── benchmark/
│   │   ├── views/
│   │   │   ├── Home.vue
│   │   │   ├── Config.vue
│   │   │   ├── Collections.vue
│   │   │   └── Benchmark.vue
│   │   └── stores/
│   ├── package.json
│   └── vite.config.ts
│
├── docker/
│   ├── Dockerfile
│   └── docker-compose.yaml
│
└── README.md
```

---

## 六、下一步行动

### 6.1 立即开始

1. **创建项目结构**
   ```bash
   mkdir -p coderag-hub/{backend,frontend,docker}
   cd coderag-hub/backend
   python -m venv venv
   ```

2. **安装依赖**
   ```bash
   pip install fastapi uvicorn chromadb flashrank mcp
   ```

3. **实现 MCP Server 基础框架**
   - 参考 chroma-mcp 源码
   - 添加 Rerank 工具

4. **集成 FlashRank**
   - 实现 RerankProvider 接口
   - 添加模型选择配置

### 6.2 MVP 里程碑

| 里程碑 | 目标 | 预计内容 |
|--------|------|---------|
| **M1** | MCP Server 可用 | Rerank 工具实现 |
| **M2** | 基础索引功能 | Python/TS 代码索引 |
| **M3** | Web 控制台 v1 | 配置管理页面 |
| **M4** | 效果对比 | Benchmark 功能 |
| **M5** | MVP 完成 | 完整可用版本 |

---

## 附录

### A. FlashRank 模型详情

| 模型 | 大小 | 语言 | 特点 |
|------|------|------|------|
| `ms-marco-TinyBERT-L-2-v2` | ~4MB | 英语 | 最小最快，默认推荐 |
| `ms-marco-MiniLM-L-12-v2` | ~34MB | 英语 | 最佳 Cross-encoder |
| `ms-marco-MultiBERT-L-12` | ~150MB | 100+语言 | 多语言支持 |
| `rank-T5-flan` | ~110MB | 英语 | 最佳 Zero-shot |
| `ce-esci-MiniLM-L12-v2` | - | 英语 | Amazon ESCI 微调 |
| `rank_zephyr_7b_v1_full` | ~4GB | 英语 | LLM-based，最高质量 |

### B. 参考资源

- [chroma-mcp 源码](https://github.com/chroma-core/chroma-mcp)
- [FlashRank 文档](https://github.com/PrithivirajDamodaran/FlashRank)
- [MCP 协议规范](https://modelcontextprotocol.io/)
- [FastMCP 框架](https://github.com/modelcontextprotocol/python-sdk)

---

**文档结束**

*本文档由 OpenCode AI 于 2026-03-19 生成，用于 Code-RAG Hub MVP 规划。*