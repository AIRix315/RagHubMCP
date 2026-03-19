# 通用代码 RAG 中枢 (Code-RAG Hub) 项目可行性分析报告

**文档版本**: v1.0  
**分析日期**: 2026-03-19  
**分析师**: OpenCode AI  

---

## 📋 目录

1. [项目概述](#一项目概述)
2. [技术可行性评估](#二技术可行性评估)
3. [GitHub 竞品项目分析](#三github-竞品项目分析)
4. [市场机会与差异化分析](#四市场机会与差异化分析)
5. [技术架构建议](#五技术架构建议)
6. [实施建议](#六实施建议)
7. [参考资源](#七参考资源)
8. [结论与行动建议](#八结论与行动建议)

---

## 一、项目概述

### 1.1 项目愿景
构建一个**通用代码 RAG 中枢 (Code-RAG Hub)**，作为 IDE 与 AI 模型之间的智能桥梁，实现代码库的语义化检索与问答。

### 1.2 目标架构

```
┌─────────────────────────────────────────────────────────────┐
│  Web 可视化控制台 (Streamlit/Vue)                            │
│  - 配置中心：选定代码目录、模型、数据库                       │
│  - 任务监控：查看入库进度、切分状态                           │
│  - 调试面板：测试检索质量、调整 Rerank 阈值                   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  RAG 核心引擎 (Python)                                      │
│  ├── [ 接口层 ] MCP Handler (处理检索请求)                    │
│  ├── [ 编排层 ] 1. 粗搜 2. 精排 (Reranker)                   │
│  └── [ 插件适配层 ]                                         │
│      ├── 模型适配: Ollama(Qwen3), 本地 BGE-M3, OpenAI...     │
│      └── 存储适配: Chroma, Qdrant, FAISS...                  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  [ 本地大模型 (Ollama) ] & [ 向量数据库 (Qdrant/Chroma) ]      │
└─────────────────────────────────────────────────────────────┘
```

### 1.3 支持 IDE
- Opencode
- Cursor
- Zed
- VS Code + Copilot
- Windsurf
- Claude Desktop

---

## 二、技术可行性评估

### 2.1 核心优势

| 架构组件 | 技术选型 | 可行性 | 说明 |
|---------|---------|--------|------|
| **协议层** | MCP (Model Context Protocol) | ⭐⭐⭐⭐⭐ | 官方支持，生态成熟 |
| **向量数据库** | Chroma/Qdrant | ⭐⭐⭐⭐⭐ | 两者均为成熟开源方案 |
| **本地模型** | Ollama | ⭐⭐⭐⭐⭐ | 本地部署标准方案 |
| **前端控制台** | Streamlit/Vue | ⭐⭐⭐⭐⭐ | 技术栈成熟 |
| **编排引擎** | Python RAG框架 | ⭐⭐⭐⭐⭐ | 生态丰富 |

### 2.2 MCP 协议的关键价值

MCP (Model Context Protocol) 是 Anthropic 推出的开放标准，已被主流 IDE 广泛支持：

| IDE | 支持状态 | 配置方式 |
|-----|---------|---------|
| **VS Code + Copilot** | ✅ 官方支持 | `settings.json` |
| **Cursor** | ✅ 原生支持 | `~/.cursor/mcp.json` |
| **Claude Desktop** | ✅ 原生支持 | `claude_desktop_config.json` |
| **Windsurf** | ✅ 原生支持 | `~/.codeium/windsurf/mcp_config.json` |
| **Zed** | ✅ 官方支持 | 配置文件 |
| **Opencode** | ✅ 原生支持 | 内置 MCP 客户端 |

**核心优势**: MCP 是连接您的服务与多种 IDE 的最佳桥梁，避免了为每个 IDE 单独开发适配器。

### 2.3 技术栈兼容性矩阵

| 组件 | 推荐方案 | 备选方案 | 说明 |
|------|---------|---------|------|
| **后端框架** | FastAPI | Flask, Django | Python 生态首选 |
| **向量数据库** | Qdrant | Chroma, Milvus | Qdrant 性能更优 |
| **Embedding** | BGE-M3 | mxbai-embed-large | 中文支持好 |
| **本地 LLM** | Qwen3 (Ollama) | Llama3, Phi4 | 中文场景推荐 |
| **前端** | Vue3 | Streamlit, React | Vue 适合复杂管理界面 |
| **代码解析** | Tree-sitter | AST parsers | 多语言支持 |

---

## 三、GitHub 竞品项目分析

### 3.1 高度相关项目（Top 10）

| 项目 | Stars | 语言 | 特点 | 与您架构的差异 |
|------|-------|------|------|--------------|
| **[cline/cline](https://github.com/cline/cline)** | 59K | TypeScript | 全功能 AI 编码助手 | 内置 Agent 能力，非 RAG 专用 |
| **[continuedev/continue](https://github.com/continuedev/continue)** | 32K | TypeScript | 开源 AI 代码助手 | 直接集成到 IDE，非独立 RAG 服务 |
| **[RooCodeInc/Roo-Code](https://github.com/RooCodeInc/Roo-Code)** | 22.7K | TypeScript | AI 编码 Agent | 强调多 Agent 协作 |
| **[qdrant/qdrant](https://github.com/qdrant/qdrant)** | 29.6K | Rust | 向量数据库 | 您的底层依赖 |
| **[chroma-core/chroma](https://github.com/chroma-core/chroma)** | 26.7K | Rust/Python | 向量数据库 | 您的底层依赖 |
| **[punkpeye/awesome-mcp-servers](https://github.com/punkpeye/awesome-mcp-servers)** | 83K | Markdown | MCP 服务器合集 | 资源汇总 |

### 3.2 直接竞品深度分析（MCP + Code RAG）

#### 🥇 项目 1: rag-code-mcp

| 属性 | 详情 |
|------|------|
| **GitHub** | https://github.com/doITmagic/rag-code-mcp |
| **Stars** | 26 |
| **语言** | Go |
| **技术栈** | Go + Qdrant + Ollama |
| **维护状态** | 活跃 (v1.1.21, 2026-02-01) |

**核心特点**:
- ✅ 100% 本地运行，零云依赖
- ✅ 隐私优先设计
- ✅ 多语言支持 (Go, PHP/Laravel, Python, JS/TS/React)
- ✅ 深度 AST 分析
- ✅ 自动 IDE 配置 (Cursor, VS Code, Windsurf, Claude Desktop)
- ✅ 9 个 MCP 工具 (search_code, hybrid_search, get_function_details 等)
- ✅ 增量索引支持

**功能对比**:

| 功能 | rag-code-mcp | 您的项目规划 | 差距 |
|------|--------------|--------------|------|
| MCP 支持 | ✅ | ✅ | 持平 |
| Web 控制台 | ❌ | ✅ | 您领先 |
| 代码图谱 | ❌ | 规划 | 您领先 |
| 团队协作 | ❌ | 规划 | 您领先 |
| 多语言 AST | ✅ | 规划 | 需追赶 |
| 自动配置 | ✅ | 规划 | 需追赶 |

**评估**: ⚠️ **最相似直接竞品**，技术栈高度重合

---

#### 🥈 项目 2: SylphxAI/coderag

| 属性 | 详情 |
|------|------|
| **GitHub** | https://github.com/SylphxAI/coderag |
| **Stars** | 7 |
| **语言** | TypeScript |
| **技术栈** | TypeScript + SQLite + LanceDB |
| **维护状态** | 活跃 (@sylphx/coderag-mcp@0.3.33) |

**核心特点**:
- ✅ 零外部依赖（除可选 OpenAI）
- ✅ 混合搜索：TF-IDF + 向量
- ✅ StarCoder2 Tokenizer（代码感知）
- ✅ **<50ms 搜索延迟**
- ✅ SQLite 持久化（<100ms 启动）
- ✅ 增量更新 + 文件监听
- ✅ AST Chunking（15+ 语言）
- ✅ MCP 服务器支持

**性能基准**:

| 代码库规模 | 索引时间 | 搜索时间 |
|-----------|---------|---------|
| 100 文件 | 0.5s | <10ms |
| 1,000 文件 | 2s | <30ms |
| 10,000 文件 | 15s | <50ms |

**评估**: ⚠️ **技术创新型竞品**，TF-IDF + 向量混合搜索值得借鉴

---

#### 🥉 项目 3: Neverdecel/CodeRAG

| 属性 | 详情 |
|------|------|
| **GitHub** | https://github.com/Neverdecel/CodeRAG |
| **Stars** | 190 |
| **语言** | Python |
| **技术栈** | Python + FAISS + OpenAI + Streamlit |
| **维护状态** | 维护中（最后更新 2025-09） |

**核心特点**:
- ✅ 教育价值高（RAG 实现参考）
- ✅ Streamlit Web 界面
- ✅ FAISS 向量搜索
- ✅ 实时文件监控
- ❌ 依赖 OpenAI API（非本地）
- ❌ 仅支持 Python 文件

**评估**: 📚 **参考价值**，Streamlit UI 可作为参考

---

#### 📌 其他相关项目

| 项目 | Stars | 特点 | 参考价值 |
|------|-------|------|---------|
| **[qdrant/demo-code-search](https://github.com/qdrant/demo-code-search)** | 59 | Qdrant 官方 Demo | ⭐⭐⭐⭐ |
| **[agentika-labs/grepika](https://github.com/agentika-labs/grepika)** | 94 | Rust 实现，三引擎搜索 | ⭐⭐⭐ |
| **[stevenbecht/codequery](https://github.com/stevenbecht/codequery)** | 4 | Python CLI 工具 | ⭐⭐ |
| **[zilliztech/claude-context](https://github.com/zilliztech/claude-context)** | - | Milvus + MCP | ⭐⭐⭐ |
| **[hashir-ayaz/codebase-rag](https://github.com/hashir-ayaz/codebase-rag)** | 3 | TypeScript 轻量级 | ⭐⭐ |

### 3.3 竞品技术栈对比矩阵

| 项目 | 语言 | 向量库 | Embedding | LLM | MCP | Web UI |
|------|------|--------|-----------|-----|-----|--------|
| rag-code-mcp | Go | Qdrant | Ollama | Ollama | ✅ | ❌ |
| SylphxAI/coderag | TS | SQLite/LanceDB | StarCoder2 | 可选 | ✅ | ❌ |
| Neverdecel/CodeRAG | Python | FAISS | OpenAI | OpenAI | ❌ | ✅ |
| qdrant/demo | TS/Python | Qdrant | OpenAI | - | ❌ | ✅ |
| grepika | Rust | 内置 | 内置 | - | ✅ | ❌ |

---

## 四、市场机会与差异化分析

### 4.1 市场趋势分析

#### 📈 有利因素

| 趋势 | 说明 | 对您的影响 |
|------|------|-----------|
| **MCP 生态爆发** | 2024 Q4 发布后快速增长 | 抢占早期红利 |
| **隐私需求上升** | 企业代码不愿上传云端 | 本地优先是优势 |
| **多 IDE 痛点** | 开发者使用多种工具 | 统一服务有需求 |
| **开源替代** | Cursor/Copilot 商业锁 | 开源方案机会 |
| **AI Coding 普及** | 开发者接受度提高 | 市场教育完成 |

#### ⚠️ 风险因素

| 风险 | 说明 | 应对策略 |
|------|------|---------|
| **竞品先发** | rag-code-mcp 已实现 | 差异化功能竞争 |
| **技术门槛** | MCP 协议学习成本 | 完善文档示例 |
| **模型依赖** | Ollama 硬件要求 | 提供云端备选 |
| **维护成本** | 多语言 AST 支持 | 优先核心语言 |

### 4.2 差异化机会矩阵

| 差异化维度 | 建议方案 | 竞品覆盖 | 实施难度 | 用户价值 |
|-----------|---------|---------|---------|---------|
| **Web 可视化控制台** | Vue3 管理界面 | ⚠️ 鲜有 | ⭐⭐ | ⭐⭐⭐⭐⭐ |
| **代码图谱可视化** | 依赖关系图、调用链 | ❌ 空白 | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **团队协作功能** | 共享索引、权限管理 | ❌ 空白 | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| **CI/CD 集成** | GitHub Actions、预提交 | ❌ 空白 | ⭐⭐ | ⭐⭐⭐⭐ |
| **混合检索策略** | TF-IDF + 向量 + AST | ⚠️ 部分 | ⭐⭐ | ⭐⭐⭐⭐⭐ |
| **智能代码切片** | 基于 AST 的语义分块 | ⚠️ 部分 | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| **多模型路由** | 自动选择最优模型 | ❌ 空白 | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| **检索质量反馈** | 用户标记改进结果 | ❌ 空白 | ⭐⭐ | ⭐⭐⭐⭐ |

### 4.3 目标用户画像

#### 主要用户群体

| 用户类型 | 核心需求 | 痛点 | 您的价值主张 |
|---------|---------|------|-------------|
| **独立开发者** | 高效代码检索 | IDE 搜索不够智能 | 语义搜索 + 本地优先 |
| **小团队** | 知识共享 | 新人上手慢 | 团队知识库 |
| **企业开发** | 代码安全 | 商业产品隐私担忧 | 100% 本地部署 |
| **开源贡献者** | 快速理解代码库 | 大型项目难导航 | 代码图谱 + 问答 |
| **AI 工具链集成** | 标准化接口 | 各 IDE 配置不同 | MCP 统一协议 |

---

## 五、技术架构建议

### 5.1 优化后的架构设计

```
┌─────────────────────────────────────────────────────────────────┐
│  🎨 前端层 (Vue3 + TypeScript)                                   │
│  ├── 配置中心: 代码目录、模型、数据库设置                        │
│  ├── 任务监控: 索引进度、队列状态、系统资源                      │
│  ├── 调试面板: 查询测试、结果调优、阈值调整                      │
│  └── 代码图谱: 依赖可视化、调用链分析                            │
├─────────────────────────────────────────────────────────────────┤
│  ⚙️  API 层 (FastAPI)                                            │
│  ├── REST API: 管理操作                                          │
│  ├── WebSocket: 实时进度推送                                     │
│  └── MCP Server: 标准化工具接口                                  │
├─────────────────────────────────────────────────────────────────┤
│  🧠 RAG 核心引擎 (Python)                                        │
│  ├── [MCP Handler]                                               │
│  │   └── Tools: search_code, get_context, find_definitions...    │
│  ├── [检索编排]                                                  │
│  │   ├── 粗筛: BM25/TF-IDF 快速召回                              │
│  │   ├── 精排: Vector 相似度计算                                 │
│  │   ├── Rerank: Cross-encoder 重排序                            │
│  │   └── 融合: 多路召回结果合并                                  │
│  ├── [代码理解]                                                  │
│  │   ├── AST Parser: Tree-sitter 多语言解析                      │
│  │   ├── Chunker: 语义边界智能切分                               │
│  │   └── Graph Builder: 代码依赖图谱构建                         │
│  └── [索引管理]                                                  │
│      ├── 全量索引: 初始代码库扫描                                │
│      ├── 增量更新: 文件变更监听                                  │
│      └── 索引优化: 压缩、分片、缓存                              │
├─────────────────────────────────────────────────────────────────┤
│  💾 存储层                                                       │
│  ├── 向量数据库: Qdrant (生产) / Chroma (开发)                   │
│  ├── 元数据存储: PostgreSQL / SQLite                             │
│  ├── 代码图谱: Neo4j / NetworkX                                  │
│  └── 文件缓存: Redis / 本地磁盘                                  │
├─────────────────────────────────────────────────────────────────┤
│  🤖 模型层                                                       │
│  ├── Embedding:                                                  │
│  │   ├── 本地: BGE-M3 / mxbai-embed-large (Ollama)              │
│  │   └── 云端: text-embedding-3-small (OpenAI)                   │
│  └── LLM (可选):                                                 │
│      ├── 本地: Qwen3 / Llama3 (Ollama)                          │
│      └── 云端: Claude / GPT-4 (增强问答)                         │
└─────────────────────────────────────────────────────────────────┘
```

### 5.2 关键技术选型理由

#### 为什么选择 Qdrant 而非 Chroma？

| 维度 | Qdrant | Chroma | 建议 |
|------|--------|--------|------|
| **性能** | 更高（Rust 实现） | 中等 | 生产用 Qdrant |
| **部署复杂度** | 中等（需 Docker） | 低（嵌入式） | 开发用 Chroma |
| **扩展性** | 优秀（集群支持） | 有限 | 大项目选 Qdrant |
| **社区活跃度** | 高 | 高 | 两者皆可 |

**建议**: 开发阶段使用 Chroma（零配置），生产阶段迁移至 Qdrant（高性能）。

#### 为什么选择 BGE-M3？

| 模型 | 维度 | 语言支持 | 特点 |
|------|------|---------|------|
| **BGE-M3** | 1024 | 多语言（含中文） | 开源 SOTA，跨语言效果好 |
| **mxbai-embed-large** | 1024 | 英语为主 | rag-code-mcp 选用 |
| **nomic-embed-text** | 768 | 多语言 | 体积小，适合边缘设备 |

**建议**: 优先 BGE-M3，中文场景表现更佳。

---

## 六、实施建议

### 6.1 分阶段路线图

#### 🚀 Phase 1: MVP 阶段（4-6 周）

**目标**: 验证核心功能，获得首批用户反馈

| 模块 | 功能 | 优先级 | 工作量 |
|------|------|--------|--------|
| MCP Server | search_code, get_context | P0 | 1 周 |
| 索引引擎 | Python/TS 支持、基础分块 | P0 | 2 周 |
| 向量存储 | Chroma 集成 | P0 | 1 周 |
| Embedding | Ollama BGE-M3 | P0 | 0.5 周 |
| 基础配置 | 配置文件管理 | P1 | 1 周 |
| 文档 | README、Quickstart | P1 | 0.5 周 |

**交付物**:
- ✅ MCP Server 可运行
- ✅ 支持 Python/TypeScript 代码检索
- ✅ CLI 基础配置工具
- ✅ 安装文档

---

#### 📈 Phase 2: 功能增强（6-8 周）

**目标**: 提升搜索质量，支持更多语言

| 模块 | 功能 | 优先级 | 工作量 |
|------|------|--------|--------|
| 混合搜索 | TF-IDF + Vector 融合 | P0 | 2 周 |
| 多语言支持 | Go/Java/Rust 等 | P1 | 2 周 |
| AST 分块 | Tree-sitter 语义切分 | P1 | 2 周 |
| Web 控制台 | Vue3 基础界面 | P1 | 3 周 |
| Qdrant 支持 | 生产级向量库 | P2 | 1 周 |
| 增量索引 | 文件监听更新 | P1 | 1 周 |

**交付物**:
- ✅ 混合搜索提升准确性
- ✅ Web 管理界面 v1.0
- ✅ 10+ 语言支持
- ✅ 自动增量更新

---

#### 🏭 Phase 3: 企业级功能（8-10 周）

**目标**: 团队协作、企业级部署

| 模块 | 功能 | 优先级 | 工作量 |
|------|------|--------|--------|
| 代码图谱 | 依赖关系可视化 | P1 | 3 周 |
| 团队协作 | 共享索引、权限 | P2 | 3 周 |
| CI 集成 | GitHub Actions | P2 | 2 周 |
| 性能优化 | 缓存、并发、压缩 | P1 | 2 周 |
| 监控告警 | 系统状态、异常检测 | P2 | 2 周 |
| 云端同步 | 可选云端备份 | P3 | 2 周 |

**交付物**:
- ✅ 代码依赖图谱
- ✅ 团队版功能
- ✅ CI/CD 集成
- ✅ 性能优化完成

---

### 6.2 技术债务管理

| 阶段 | 技术债务 | 缓解策略 |
|------|---------|---------|
| MVP | 硬编码配置 | 配置文件抽象 |
| MVP | 单线程索引 | 异步队列设计 |
| Phase 2 | SQLite 元数据 | 预留 PostgreSQL 接口 |
| Phase 2 | 内存缓存 | 预留 Redis 接口 |
| Phase 3 | 单机部署 | 预留集群模式设计 |

---

## 七、参考资源

### 7.1 必读开源项目

| 项目 | 链接 | 学习重点 |
|------|------|---------|
| rag-code-mcp | https://github.com/doITmagic/rag-code-mcp | MCP 实现、多语言 AST |
| SylphxAI/coderag | https://github.com/SylphxAI/coderag | 混合搜索、性能优化 |
| Neverdecel/CodeRAG | https://github.com/Neverdecel/CodeRAG | Streamlit UI、FAISS 使用 |
| qdrant/demo-code-search | https://github.com/qdrant/demo-code-search | Qdrant 最佳实践 |
| awesome-mcp-servers | https://github.com/punkpeye/awesome-mcp-servers | MCP 生态大全 |

### 7.2 官方文档

| 资源 | 链接 | 用途 |
|------|------|------|
| MCP 官方文档 | https://modelcontextprotocol.io/ | 协议规范 |
| MCP Python SDK | https://github.com/modelcontextprotocol/python-sdk | 服务端开发 |
| Qdrant 文档 | https://qdrant.tech/documentation/ | 向量数据库 |
| Chroma 文档 | https://docs.trychroma.com/ | 向量数据库 |
| Tree-sitter | https://tree-sitter.github.io/ | 代码解析 |
| Ollama | https://ollama.com/ | 本地模型 |

### 7.3 社区资源

| 资源 | 链接 | 说明 |
|------|------|------|
| PulseMCP | https://pulsemcp.com/ | MCP 服务器市场 |
| LobeHub MCP | https://lobehub.com/mcp | MCP 插件市场 |
| Grep.app | https://grep.app/ | 代码搜索参考 |

---

## 八、结论与行动建议

### 8.1 可行性结论

| 维度 | 评估 | 说明 |
|------|------|------|
| **技术可行性** | ✅ 高 | 技术栈成熟，有成功先例 |
| **市场时机** | ✅ 好 | MCP 生态早期，红利期 |
| **竞争态势** | ⚠️ 中等 | 有直接竞品，但差异化空间存在 |
| **资源需求** | ⚠️ 中等 | 2-3 人团队，6 个月 MVP |
| **商业潜力** | ✅ 高 | 企业需求明确，可商业变现 |

**总体评估**: 🟢 **项目值得投入**，建议尽快启动

### 8.2 关键成功因素

1. **速度优先**: 在 rag-code-mcp 完善前抢占市场
2. **差异化定位**: Web 控制台和代码图谱是核心差异化
3. **用户体验**: 安装简单、配置傻瓜化
4. **社区建设**: 开源策略、快速响应 Issue

### 8.3 即刻行动清单

#### 📋 本周任务

- [ ] 创建 GitHub 仓库，初始化项目结构
- [ ] 搭建 FastAPI + MCP Server 基础框架
- [ ] 配置 Chroma 向量数据库连接
- [ ] 实现 Python 文件索引器
- [ ] 编写 MCP `search_code` 工具
- [ ] 创建 README 和 Quickstart 文档

#### 📋 本月任务

- [ ] 完成 MVP 功能开发
- [ ] 支持 Cursor/VS Code MCP 配置
- [ ] 发布 v0.1.0 预览版
- [ ] 收集早期用户反馈
- [ ] 规划 Phase 2 功能优先级

---

## 附录

### A. 竞品功能详细对比表

| 功能 | rag-code-mcp | SylphxAI/coderag | Neverdecel/CodeRAG | 您的项目 |
|------|--------------|------------------|-------------------|---------|
| MCP 协议 | ✅ | ✅ | ❌ | ✅ |
| 本地 LLM | ✅ | ✅ | ❌ | ✅ |
| 云端 LLM | ❌ | ✅ | ✅ | ✅ |
| 向量数据库 | Qdrant | SQLite/LanceDB | FAISS | Chroma/Qdrant |
| Web 控制台 | ❌ | ❌ | ✅ (Streamlit) | ✅ (Vue3) |
| 混合搜索 | ❌ | ✅ | ❌ | ✅ |
| AST 切分 | ✅ | ✅ | ❌ | ✅ |
| 增量索引 | ✅ | ✅ | ✅ | ✅ |
| 多语言支持 | ✅ (4+) | ✅ (15+) | ✅ (1) | ✅ (10+) |
| 代码图谱 | ❌ | ❌ | ❌ | ✅ |
| 团队协作 | ❌ | ❌ | ❌ | ✅ |
| CI/CD 集成 | ❌ | ❌ | ❌ | ✅ |
| 开源协议 | MIT | MIT | Apache | 待定 |

### B. 技术选型决策树

```
选择向量数据库:
├── 开发阶段?
│   ├── 是 → Chroma (零配置)
│   └── 否 → 继续
├── 需要集群?
│   ├── 是 → Qdrant (原生集群)
│   └── 否 → 继续
├── 性能优先?
│   ├── 是 → Qdrant (Rust 实现)
│   └── 否 → Chroma (简单易用)

选择 Embedding 模型:
├── 中文场景?
│   ├── 是 → BGE-M3 (中文优化)
│   └── 否 → 继续
├── 资源受限?
│   ├── 是 → nomic-embed-text (小体积)
│   └── 否 → mxbai-embed-large (高性能)
```

---

**文档结束**

*本文档由 OpenCode AI 于 2026-03-19 生成，基于公开信息整理分析。*
