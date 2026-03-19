# RagHubMCP MVP 架构说明

**文档版本**: v1.0  
**创建日期**: 2026-03-19  
**关联文档**: 04-Project-Structure_20260319.md

---

## 概述

本文档描述 RagHubMCP MVP (v0.2.1) 的实际架构实现，与原始设计文档的差异及其原因。

---

## 架构设计原则

MVP 阶段遵循 **"最小可用，逐步完善"** 原则：

1. **核心功能优先** - 实现主要业务流程
2. **简化设计** - 避免过度抽象和组件拆分
3. **延迟可选** - Phase 2 再完善非核心功能
4. **实用主义** - 根据实际需求调整设计

---

## 目录结构差异分析

### 后端结构

| 设计文档 | MVP 实现 | 差异原因 |
|---------|---------|---------|
| `src/mcp/` | `src/mcp_server/` | 避免 MCP SDK 包名冲突 |
| `src/config.py` | `src/utils/config.py` | 工具函数归类更合理 |
| `src/api/routes.py` | `src/api/router.py` | FastAPI 惯例命名 |
| `src/storage/` | `src/services/` | 更通用的服务层命名 |
| `src/storage/chroma_store.py` | `src/services/chroma_service.py` | 服务模式命名 |
| `src/utils/logger.py` | 未创建 | 日志配置在 main.py 内联 |
| `src/utils/helpers.py` | 未创建 | MVP 阶段无通用工具需求 |

### Provider 实现状态

| Provider | 设计文档 | MVP 实现 | 状态 |
|----------|---------|---------|------|
| Ollama Embedding | ✅ | ✅ | 已实现 |
| OpenAI Embedding | ✅ | ❌ | Phase 2 |
| HTTP Embedding | ✅ | ❌ | Phase 2 |
| FlashRank Rerank | ✅ | ✅ | 已实现 |
| Cohere Rerank | ✅ | ❌ | Phase 2 |
| Jina Rerank | ✅ | ❌ | Phase 2 |
| Ollama LLM | ✅ | ❌ | Phase 2 |
| OpenAI LLM | ✅ | ❌ | Phase 2 |

### 前端结构

| 设计文档 | MVP 实现 | 差异原因 |
|---------|---------|---------|
| `components/layout/` 多文件 | `AppLayout.vue` 单文件 | MVP 简化设计 |
| `components/config/` | 功能在 `Config.vue` | 页面级组件足够 |
| `components/collection/` | 功能在 `Collections.vue` | 页面级组件足够 |
| `components/benchmark/` | 功能在 `Benchmark.vue` | 页面级组件足够 |
| `views/Settings.vue` | 未创建 | MVP 非必需 |
| `stores/benchmark.ts` | 未创建 | 状态简单，无需store |
| `api/collection.ts` | 合并到 `search.ts` | API 功能关联 |
| `types/collection.ts` | 合并到 `search.ts` | 类型关联性强 |
| `public/` | 未创建 | Vite 项目可选 |

---

## MVP 实际架构

```
RagHubMCP/
│
├── backend/                              # 后端服务
│   ├── src/
│   │   ├── main.py                       # FastAPI 入口 + 日志配置
│   │   │
│   │   ├── api/                          # REST API
│   │   │   ├── router.py                 # 路由定义
│   │   │   ├── schemas.py                # 请求/响应模型
│   │   │   ├── config.py                 # 配置管理 API
│   │   │   ├── index.py                  # 索引任务 API
│   │   │   ├── search.py                 # 检索 API
│   │   │   └── benchmark.py              # 效果对比 API
│   │   │
│   │   ├── mcp_server/                   # MCP Server (重命名)
│   │   │   ├── server.py                 # MCP Server 实现
│   │   │   └── tools/
│   │   │       ├── base.py               # 基础工具
│   │   │       ├── search.py             # chroma_query_with_rerank
│   │   │       ├── rerank.py             # rerank_documents
│   │   │       └── benchmark.py          # benchmark_search_config
│   │   │
│   │   ├── providers/                    # Provider 层
│   │   │   ├── base.py                   # 抽象基类
│   │   │   ├── factory.py                # 工厂模式
│   │   │   ├── registry.py               # 注册中心
│   │   │   ├── embedding/
│   │   │   │   └── ollama.py             # Ollama Embedding
│   │   │   ├── rerank/
│   │   │   │   └── flashrank.py          # FlashRank Rerank
│   │   │   └── llm/
│   │   │       └── base.py               # 基类占位
│   │   │
│   │   ├── chunkers/                     # 代码切分
│   │   │   ├── base.py                   # ChunkerPlugin 抽象
│   │   │   ├── registry.py               # 插件注册
│   │   │   ├── simple.py                 # 字符切分
│   │   │   ├── line.py                   # 行切分
│   │   │   └── markdown.py               # Markdown 切分
│   │   │
│   │   ├── indexer/                      # 索引模块
│   │   │   ├── scanner.py                # 文件扫描
│   │   │   └── indexer.py                # 索引编排
│   │   │
│   │   ├── services/                     # 服务层 (原 storage)
│   │   │   └── chroma_service.py         # Chroma 服务
│   │   │
│   │   └── utils/
│   │       └── config.py                 # 配置管理
│   │
│   ├── tests/                            # 测试 (214 tests)
│   ├── pyproject.toml                    # 项目配置
│   ├── config.yaml                       # 应用配置
│   └── .env.example                      # 环境变量模板
│
├── frontend/                             # Web 控制台
│   ├── src/
│   │   ├── main.ts
│   │   ├── App.vue
│   │   │
│   │   ├── components/
│   │   │   └── layout/
│   │   │       └── AppLayout.vue         # 统一布局组件
│   │   │
│   │   ├── views/
│   │   │   ├── Home.vue                  # 首页
│   │   │   ├── Config.vue                # 配置管理
│   │   │   ├── Collections.vue           # Collection 管理
│   │   │   └── Benchmark.vue             # 效果对比
│   │   │
│   │   ├── stores/
│   │   │   ├── config.ts
│   │   │   ├── collection.ts
│   │   │   └── index.ts
│   │   │
│   │   ├── api/
│   │   │   ├── client.ts                 # Axios 封装
│   │   │   ├── config.ts
│   │   │   ├── indexing.ts
│   │   │   ├── search.ts
│   │   │   └── benchmark.ts
│   │   │
│   │   ├── types/
│   │   │   ├── common.ts
│   │   │   ├── config.ts
│   │   │   ├── indexing.ts
│   │   │   ├── search.ts
│   │   │   └── benchmark.ts
│   │   │
│   │   └── router/
│   │       └── index.ts
│   │
│   ├── package.json
│   ├── vite.config.ts
│   └── vitest.config.ts
│
├── docker/                               # Docker (Phase 2)
│   └── (待实现)
│
├── Docs/
│   ├── 01-RagHubMCP_20260319.md
│   ├── 02-RagHubMCP-Tech_20260319.md
│   ├── 03-RagHubMCP-MVP_20260319.md
│   ├── 04-Project-Structure_20260319.md
│   └── 05-MVP-Architecture_20260319.md   # 本文档
│
├── data/                                 # 数据目录
├── logs/                                 # 日志目录
├── TODO.md
├── CHANGELOG.md
└── README.md
```

---

## 已实现功能

### 后端 MCP 工具

| 工具名称 | 功能 | 测试 |
|---------|------|------|
| `ping` | 服务器连通性测试 | ✅ |
| `get_config` | 获取当前配置 | ✅ |
| `reload_config` | 配置热重载 | ✅ |
| `list_tools` | 列出所有工具 | ✅ |
| `get_server_info` | 获取服务器信息 | ✅ |
| `chroma_query_with_rerank` | 向量检索 + Rerank | ✅ |
| `rerank_documents` | 独立 Rerank | ✅ |
| `benchmark_search_config` | 效果对比测试 | ✅ |

### 后端 REST API

| 端点 | 功能 | 测试 |
|------|------|------|
| `GET /api/config` | 获取配置 | ✅ |
| `POST /api/config` | 更新配置 | ✅ |
| `POST /api/index` | 启动索引任务 | ✅ |
| `GET /api/index/status` | 查询任务状态 | ✅ |
| `POST /api/search` | 执行检索 | ✅ |
| `POST /api/benchmark` | 执行对比测试 | ✅ |

### 前端页面

| 页面 | 功能 | 测试 |
|------|------|------|
| Home | 系统概览 | ✅ |
| Config | 配置管理 | ✅ |
| Collections | Collection 管理 | ✅ |
| Benchmark | 效果对比 | ✅ |

---

## Phase 2 规划

| 功能 | 优先级 | 说明 |
|------|--------|------|
| 混合搜索 | P1 | TF-IDF + Vector |
| 多语言 AST 切分 | P1 | Tree-sitter |
| Web 控制台增强 | P2 | WebSocket 实时进度 |
| Qdrant 支持 | P2 | 向量库切换 |
| 增量索引 | P2 | watchdog 文件监听 |
| Docker 配置 | P2 | 容器化部署 |
| 更多 Provider | P3 | OpenAI, Cohere, Jina |

---

## 测试覆盖

```
后端: 214 tests passed
前端: 8 tests passed

测试文件分布:
├── test_api/          (17 tests)
├── test_chunkers/     (51 tests)
├── test_indexer/      (26 tests)
├── test_mcp_server/   (49 tests)
├── test_providers/    (59 tests)
└── test_services/     (10 tests)
```

---

## 版本信息

- **MVP 版本**: v0.2.1
- **发布日期**: 2026-03-19
- **Python**: 3.11+
- **Node.js**: 18+

---

*本文档记录 MVP 阶段实际架构，后续迭代将更新此文档。*