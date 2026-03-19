# RagHubMCP 更新日志

本文件记录项目所有重要变更。

格式遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
版本本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

---

## [Unreleased]

### 待开发

- Phase 3: 企业级功能

## [0.4.0] - 2026-03-19

### Phase 2 功能增强

#### 2.4 迁移工具 ✅

- **时间**: 2026-03-19
- **状态**: 完成
- **内容**:
  - 创建 `src/utils/migrate.py`: VectorStoreMigrator核心类
    - 支持 Chroma → Qdrant 迁移
    - 批量处理、进度回调、数据完整性验证
  - 创建 `src/mcp_server/tools/migrate.py`: MCP工具
    - `migrate_vectorstore`: 迁移指定collections
    - `list_vectorstore_collections`: 列出collections
  - 创建 `src/cli/migrate.py`: 命令行工具
    - 支持 `--dry-run`, `--collections`, `--batch-size` 等参数
- **验证结果**: 14 tests passed ✅

#### 2.3c 可视化图表 ✅

- **时间**: 2026-03-19
- **状态**: 完成
- **内容**:
  - 安装 chart.js + vue-chartjs (轻量级图表库)
  - 创建 `frontend/src/components/charts/BenchmarkChart.vue`:
    - 综合对比柱状图 (延迟/分数/结果数)
    - 双Y轴设计
  - 创建 `frontend/src/components/charts/LatencyChart.vue`:
    - 延迟分析水平条形图
    - 颜色编码指示快慢
  - 更新 Benchmark.vue 添加 Tab 切换 (表格/图表)
- **验证结果**: 13 tests passed ✅

#### 2.3b 统计仪表盘 ✅

- **时间**: 2026-03-19
- **状态**: 完成
- **内容**:
  - 创建 `frontend/src/components/dashboard/StatsCard.vue`:
    - 可复用统计卡片组件
    - 支持图标、趋势、变体样式
  - 创建 `frontend/src/components/dashboard/ProviderStatus.vue`:
    - Provider状态展示组件
  - 更新 `frontend/src/views/Home.vue`:
    - Collection统计卡片 (总数、文档数、平均)
    - 索引任务状态展示
    - Provider配置状态
  - 扩展 collection store 添加统计计算属性
- **验证结果**: 14 tests passed ✅

#### 2.5: 增量索引 ✅

- **时间**: 2026-03-19
- **状态**: 完成
- **内容**:
  - 创建 `src/indexer/watcher.py`: 文件监听服务
    - 使用 watchdog.Observer 实现
    - 支持递归监听、排除目录、文件类型过滤
    - 防抖处理避免频繁操作
  - 创建 `src/indexer/incremental.py`: 增量索引器
    - 基于 content_hash 检测变更
    - 支持新增/修改/删除文件处理
    - 包含 SimpleChunker fallback 机制
  - 创建 MCP工具: `start_watcher`, `stop_watcher`, `get_watcher_status`, `sync_directory`
- **验证结果**:
  - 新增测试: 34 passed ✅
  - 总索引器测试: 60 passed ✅

#### 2.4: Qdrant 支持 ✅

- **时间**: 2026-03-19
- **状态**: 完成
- **内容**:
  - 创建 `src/providers/vectorstore/base.py`: VectorStoreProvider 抽象基类
    - 统一接口: create_collection, add, query, delete, count
    - SearchResult, QueryResult 数据类
  - 创建 `src/providers/vectorstore/chroma.py`: ChromaProvider
    - 包装现有 ChromaService，零侵入性
  - 创建 `src/providers/vectorstore/qdrant.py`: QdrantProvider
    - 支持 memory, local, remote, cloud 模式
    - 自动嵌入生成
  - 更新 `src/providers/factory.py`: get_vectorstore_provider() 方法
- **验证结果**:
  - 新增测试: 22 passed, 19 skipped (qdrant-client未安装) ✅

#### 2.3a: WebSocket 实时进度 ✅

- **时间**: 2026-03-19
- **状态**: 完成
- **内容**:
  - 创建 `backend/src/api/websocket.py`: ConnectionManager
    - 连接管理、广播进度、心跳机制
  - 添加 WebSocket 端点: `/ws/progress/{task_id}`
  - 创建 `frontend/src/composables/useWebSocket.ts`: Vue composable
  - 更新 IndexStore 使用 WebSocket + REST 回退
- **验证结果**:
  - 后端测试: 13 passed ✅
  - 前端测试: 8 passed ✅

#### 2.2: 多语言 AST 切分 ✅

- **时间**: 2026-03-19
- **状态**: 完成
- **内容**:
  - 创建 `src/chunkers/ast_base.py`: AST切分器抽象基类
    - Tree-sitter 解析和查询通用逻辑
    - 优雅降级处理
  - 创建 `src/chunkers/python_ast.py`: Python AST切分器
    - 函数级别切分 (function_definition)
    - 类级别切分 (class_definition)
  - 创建 `src/chunkers/typescript_ast.py`: TypeScript/TSX AST切分器
    - 函数声明、类声明、方法定义、箭头函数
  - 创建 `src/chunkers/go_ast.py`: Go AST切分器
    - 函数声明、方法声明、类型声明
  - 更新 ChunkerRegistry 自动注册 AST 切分器
  - 添加可选依赖组 `[ast]`
- **验证结果**:
  - 新增测试: 36 passed ✅
  - 总切分器测试: 87 passed ✅

#### 2.1: 混合搜索 ✅

- **时间**: 2026-03-19
- **状态**: 完成
- **内容**:
  - 创建 `src/services/bm25_service.py`: BM25索引服务
    - 使用 bm25s 库 (100x faster than rank_bm25)
    - 支持 per-collection 索引管理
    - 持久化存储
  - 创建 `src/services/hybrid_search.py`: 混合搜索服务
    - RRF (Reciprocal Rank Fusion) 算法
    - 可配置权重 alpha (向量) / beta (BM25)
  - 创建 MCP工具: `hybrid_search`, `bm25_index_documents`, `bm25_query`
  - 更新配置: HybridConfig
- **验证结果**:
  - 新增测试: 26 passed ✅

### 测试统计变更

| 阶段 | 测试数 |
|------|--------|
| Phase 1.5 | 240 |
| Phase 2 | 334 (+94) |

---

### Phase 1.5 进展

#### 验证修复 (2026-03-19)

- **时间**: 2026-03-19 21:50
- **状态**: 完成
- **问题**: MCP SDK 1.26.0 的 `call_tool` 返回格式为 `tuple(list[TextContent], dict)`
- **修复**: 更正测试文件中的结果访问方式：`result[0].text` → `result[0][0].text`
- **影响文件**:
  - `tests/test_mcp_server/test_server.py`
  - `tests/test_mcp_server/test_search_tool.py`
  - `tests/test_mcp_server/test_rerank_tool.py`
  - `tests/test_mcp_server/test_benchmark_tool.py`
  - `tests/test_integration/test_mcp_api.py`
  - `tests/test_integration/test_index_search.py`
- **验证结果**:
  - 后端测试: 240 passed ✅
  - 前端测试: 8 passed ✅

#### 1.20: Phase 1.5 验收 ✅

- **时间**: 2026-03-19 22:20
- **状态**: 完成
- **验收结果**:
  - 后端测试: 281 passed ✅
  - 前端测试: 8 passed ✅
  - HTTPEmbeddingProvider: 可用 ✅
  - Settings 页面: 可访问 ✅
  - CHANGELOG.md: 更新完整 ✅

**Phase 1.5 完成总结**:
- 新增集成测试目录 test_integration/ (18 tests)
- 新增 HTTPEmbeddingProvider 支持 OpenAI 兼容 API
- 新增 Settings 页面支持 MCP 配置导出
- 修复 MCP 测试 API 兼容性问题
- 总测试数: 270 → 281

#### 1.19: 前端基础补全 ✅

- **时间**: 2026-03-19 22:15
- **状态**: 完成
- **内容**:
  - 创建 `frontend/src/views/Settings.vue`: 系统设置页面
    - 系统信息展示 (服务器地址、数据目录、日志级别)
    - MCP 配置导出 (复制/下载 claude_desktop_config.json)
    - 快速链接 (GitHub、MCP 文档)
  - 更新 `frontend/src/router/index.ts`: 添加 /settings 路由
  - 更新 `frontend/src/components/layout/AppLayout.vue`: 添加导航链接
- **验证结果**:
  - 前端测试: 8 passed ✅
  - 前端构建: 成功 ✅

#### 1.18: Provider 基础补全 ✅

- **时间**: 2026-03-19 22:00
- **状态**: 完成
- **内容**:
  - 创建 `src/providers/embedding/http.py`: `HTTPEmbeddingProvider`
    - 通用 HTTP Embedding Provider，支持所有 OpenAI-compatible APIs
    - 支持: OpenAI、Azure OpenAI、LM Studio、LocalAI、vLLM 等
    - 支持自定义 headers（适配 Azure OpenAI）
    - 支持批量处理 (embed_batch)
  - 创建 `tests/test_providers/test_http_embedding.py`: 11 个测试用例
    - TC-1.18.1~4: 核心功能测试
    - OpenAI API 格式验证
  - 更新 `config.yaml`: 添加 HTTP Provider 配置示例
- **验证结果**:
  - HTTP Provider 测试: 11 passed ✅
  - 全量测试: 281 passed ✅

#### 1.17: 测试覆盖完善 ✅

- **时间**: 2026-03-19 21:30
- **状态**: 完成
- **内容**:
  - 创建 `backend/tests/test_integration/` 目录
  - 创建 `test_index_search.py` - 6 个集成测试
    - TC-INT-1~5: 索引→MCP 搜索流程测试
    - 覆盖: 单文件索引、多文件类型、元数据保留、清除验证
  - 创建 `test_mcp_api.py` - 12 个集成测试
    - TC-INT-6~13: MCP + REST API 联合测试
    - 覆盖: 配置一致性、搜索工具注册、工作流测试、错误处理
  - 修复 MCP 测试 API 兼容性问题 (`result[0][0].text` → `result[0].text`)
- **验证结果**:
  - 集成测试: 18 passed ✅
  - 全量测试: 270 passed ✅

### Phase 1.5 规划

- **时间**: 2026-03-19 19:45
- **状态**: 规划完成
- **内容**: 完成 MVP 升级分析，创建 Phase 1.5 任务规划文档
  - 文档: `Docs/06-MVP-Upgrade-Analysis_20260319.md`
  - 识别关键差距: Provider 实现不完整 (30%)、前端组件拆分不足 (55%)、测试覆盖缺失 LLM/集成测试
  - 定义 4 个任务阶段: 1.17 测试完善、1.18 Provider 补全、1.19 前端完善、1.20 验收
  - 包含任务参考位置、Context7 最佳实践指南、CHANGELOG 模板

---

## [0.2.1] - 2026-03-19

### Bug Fixes: 导入路径与类型定义修复

- **时间**: 2026-03-19 18:55
- **状态**: 完成
- **问题发现**:
  - 后端导入路径缺失 `src.` 前缀导致模块无法加载
  - 前端类型定义循环引用
  - 前端缺少 `IndexRequest`, `IndexResponse`, `IndexTaskStatus` 类型
  - TypeScript 配置缺少 `vite/client` 类型
  - vite.config.ts 与 vitest 类型冲突

- **修复内容**:
  
  **后端修复**:
  - `src/main.py`: 添加 `src.` 前缀到导入路径
  - `src/api/benchmark.py`: 修复 `from utils.config` → `from src.utils.config`
  - `src/api/search.py`: 同上
  - `src/api/index.py`: 同上
  - `src/api/config.py`: 同上
  - `src/providers/factory.py`: 同上
  
  **前端修复**:
  - `src/types/index.ts`: 移除循环引用，添加 `indexing` 导出
  - `src/types/indexing.ts`: 新增 Index 相关类型定义
  - `tsconfig.app.json`: 添加 `"types": ["vite/client"]`
  - `tsconfig.node.json`: 添加 `"types": ["vitest/config"]`
  - `vite.config.ts`: 移除 test 配置（已存在于 vitest.config.ts）
  - `src/views/Benchmark.vue`: 修复 rerank_provider 类型问题
  - `src/views/Config.vue`: 移除未使用的导入
  - `src/stores/collection.ts`: 移除未使用的导入
  - `src/components/layout/AppLayout.vue`: 移除未使用的 RouterView 导入

- **验证结果**:
  - 后端测试: 214 tests passed ✅
  - 前端测试: 8 tests passed ✅
  - FastAPI 应用加载成功 ✅
  - MCP Server 工具注册成功 (8 tools) ✅
  - 前端生产构建成功 ✅

### Maintenance: 清理与文档更新

- **时间**: 2026-03-19 19:05
- **状态**: 完成
- **内容**:

  **临时文件清理**:
  - 删除 `backend/temp_test_cache/` - 测试缓存目录
  - 删除 `backend/.pytest_cache/` - pytest 缓存
  - 删除根目录错误创建的 `frontend*/` 空文件夹 (14个)
  - 删除错误创建的 `nul` 文件

  **新增文档**:
  - `Docs/05-MVP-Architecture_20260319.md` - MVP 实际架构说明
    - 记录设计文档与实际实现的差异
    - 列出已实现功能和测试覆盖
    - Phase 2 规划

### Git: MVP 分支创建

- **时间**: 2026-03-19 19:10
- **状态**: 完成
- **提交记录** (4 commits):

  | Hash | Message |
  |------|---------|
  | `b5ec220` | fix(backend): add src. prefix to import paths |
  | `9c69490` | feat(frontend): add Vue 3 web console |
  | `480a841` | docs: add MVP architecture document |
  | `5e21490` | docs: update CHANGELOG for v0.2.1 bug fixes |

- **分支创建**:
  ```
  * main            (当前分支, 19 commits ahead of origin/main)
    mvp/v0.2.1      (MVP 保存点)
  ```

- **分支说明**:
  - `mvp/v0.2.1` 保存完整 MVP 状态
  - 包含所有测试通过的代码
  - 可作为 Phase 2 开发的基准点

---

## [0.2.0] - 2026-03-19

### 1.14: 效果对比页面 ✅

- **时间**: 2026-03-19 18:29
- **状态**: 完成
- **内容**:
  - 创建 `frontend/src/views/Benchmark.vue`
  - 支持多配置对比测试
  - 对比结果表格展示
  - 最快配置高亮推荐
  - 详细结果分页展示
- **测试**: TC-1.14.1 ~ TC-1.14.3 全部通过

### 1.13: Collection 管理页面 ✅

- **时间**: 2026-03-19 18:29
- **状态**: 完成
- **内容**:
  - 创建 `frontend/src/views/Collections.vue`
  - Collection 列表展示
  - 文档统计信息
  - 删除操作 (含确认弹窗)
  - 集成 useCollectionStore
- **测试**: TC-1.13.1 ~ TC-1.13.3 全部通过

### 1.12: 配置管理页面 ✅

- **时间**: 2026-03-19 18:29
- **状态**: 完成
- **内容**:
  - 创建 `frontend/src/views/Config.vue`
  - Provider 展示组件 (Embedding + Rerank)
  - 索引参数配置表单
  - 配置保存/加载功能
  - 集成 useConfigStore
- **测试**: TC-1.12.1 ~ TC-1.12.4 全部通过

### 1.11: 前端项目初始化 ✅

- **时间**: 2026-03-19 18:29
- **状态**: 完成
- **内容**:
  - 创建 Vue 3 + Vite + TypeScript 项目
  - 配置 shadcn-vue 组件库 (Tailwind CSS)
  - 配置 Pinia 状态管理
  - 配置 Vue Router (4 路由)
  - 配置 API 请求封装 (Axios)
  - 创建类型定义 (匹配后端 schemas)
  - 创建视图组件 (Home, Config, Collections, Benchmark)
  - 创建 Pinia Stores (config, collection, index)
  - 创建 API 层 (config, indexing, search, benchmark)
  - 编写单元测试 (8 tests passing)
- **测试**: TC-1.11.1 ~ TC-1.11.4 全部通过 (8 tests)

---

## [0.1.0] - 2026-03-19

### 1.16: MVP 验收 ✅

- **时间**: 2026-03-19
- **状态**: 完成
- **内容**:
  - 所有 Phase 1 后端任务完成
  - 214 个测试用例全部通过
  - README 快速开始指南完善
  - 性能目标定义完成
- **验收结果**:
  - AC-1.16.1: 214 tests passed ✅
  - AC-1.16.5: README 快速开始指南 ✅
  - AC-1.16.2~1.16.4: 性能目标待实际环境验证

### 1.15: REST API 实现 ✅

- **时间**: 2026-03-19
- **状态**: 完成
- **内容**:
  - 创建 `src/api/router.py`: FastAPI 路由器
  - 创建 `src/api/schemas.py`: Pydantic 请求/响应模型
  - 创建 `src/api/config.py`: 配置管理 API (GET/POST)
  - 创建 `src/api/index.py`: 索引任务 API (POST/GET)
  - 创建 `src/api/search.py`: 检索测试 API (POST)
  - 创建 `src/api/benchmark.py`: Benchmark API (POST)
  - 创建 `src/main.py`: FastAPI 应用入口
  - 统一错误响应格式
- **测试**: 17 个测试用例全部通过

### 1.10: 索引编排 ✅

- **时间**: 2026-03-19
- **状态**: 完成
- **内容**:
  - 创建 `src/indexer/indexer.py`: `Indexer` 主类
  - 集成 FileScanner + ChunkerRegistry + OllamaEmbeddingProvider
  - 实现批量入库逻辑 (ChromaDB batch insert)
  - 添加进度回调机制 (ProgressCallback)
  - 支持增量索引 (基于 content_hash)
- **测试**: 12 个测试用例全部通过

### 1.6: benchmark_search_config MCP 工具 ✅

- **时间**: 2026-03-19
- **状态**: 完成
- **内容**:
  - 创建 `src/mcp_server/tools/benchmark.py`: `benchmark_search_config` MCP 工具
  - 支持多配置对比测试
  - 计算 Recall@K 指标
  - 计算 MRR (Mean Reciprocal Rank) 指标
  - 计算延迟统计 (avg/min/max/p95)
  - 返回最优配置推荐
- **测试**: 20 个测试用例全部通过

### 1.5: chroma_query_with_rerank MCP 工具 ✅

- **时间**: 2026-03-19
- **状态**: 完成
- **内容**:
  - 创建 `src/services/chroma_service.py`: `ChromaService` 单例服务
  - 创建 `src/mcp_server/tools/search.py`: `chroma_query_with_rerank` MCP 工具
  - 支持向量检索 + Rerank 组合
  - 支持 n_results / rerank_top_k 参数
  - 支持元数据过滤 (where 条件)
  - 返回带分数的重排结果
- **测试**: 10 个测试用例全部通过

### 1.9: 代码切分器 ✅

- **时间**: 2026-03-19
- **状态**: 完成
- **内容**:
  - 创建 `src/chunkers/base.py`: `Chunk` dataclass + `ChunkerPlugin` 抽象基类
  - 创建 `src/chunkers/simple.py`: `SimpleChunker` - 按字符数切分
  - 创建 `src/chunkers/line.py`: `LineChunker` - 按行数切分
  - 创建 `src/chunkers/markdown.py`: `MarkdownChunker` - 按标题切分
  - 创建 `src/chunkers/registry.py`: `ChunkerRegistry` - 插件注册中心
  - 支持语言感知选择 chunker
  - 支持 overlap 参数
- **测试**: 51 个测试用例全部通过

### 1.8: 文件扫描器 ✅

- **时间**: 2026-03-19
- **状态**: 完成
- **内容**:
  - 创建 `src/indexer/scanner.py`: `FileScanner` + `FileInfo` dataclass
  - 支持递归扫描目录
  - 支持文件类型过滤
  - 支持排除目录
  - 支持大文件跳过
  - 支持内容 hash 计算
- **测试**: 14 个测试用例全部通过

### 1.7: rerank_documents MCP 工具 ✅

- **时间**: 2026-03-19
- **状态**: 完成
- **内容**:
  - 创建 `src/mcp_server/tools/rerank.py`: `rerank_documents` MCP 工具
  - 支持文档列表重排
  - 支持 top_k 参数
  - 返回 JSON 格式结果 (index, score, text)
- **测试**: 7 个测试用例全部通过

### 1.5a: Ollama Embedding Provider ✅

- **时间**: 2026-03-19
- **状态**: 完成
- **内容**:
  - 创建 `src/providers/embedding/ollama.py`: `OllamaEmbeddingProvider`
  - 支持多种模型 (nomic-embed-text, bge-m3, mxbai-embed-large)
  - 实现同步和异步 embedding 方法
  - 实现批量 embedding 方法 (embed_batch)
  - 装饰器自动注册到 registry
- **测试**: 12 个测试用例全部通过

### 1.4: FlashRank Rerank 实现 ✅

- **时间**: 2026-03-19 10:30
- **状态**: 完成
- **内容**:
  - 创建 `src/providers/rerank/flashrank.py`:
    - `FlashRankRerankProvider` 类，继承 `BaseRerankProvider`
    - 支持多种模型: TinyBERT (4MB), MiniLM (34MB), MultiBERT (150MB)
    - 类级别单例缓存，避免重复加载模型
    - 装饰器自动注册到 registry
  - 模型缓存机制:
    - 自动下载到 `./data/flashrank_cache/`
    - 相同配置复用 Ranker 实例
  - 创建测试套件 `tests/test_providers/test_flashrank.py`:
    - 13 个测试用例覆盖全部 TC-1.4.1 ~ TC-1.4.7
- **测试**: TC-1.4.1 ~ TC-1.4.7 全部通过 (13 个测试用例，总计 61 个测试)

### 1.3: Provider 抽象层 ✅

- **时间**: 2026-03-19 10:16
- **状态**: 完成
- **内容**:
  - 创建 Provider 基类模块 `src/providers/base.py`:
    - `ProviderCategory` 枚举 (EMBEDDING, RERANK, LLM)
    - `BaseProvider` 抽象基类
    - 自定义异常类 (`UnsupportedProviderError`, `ProviderInitializationError`, `ProviderNotFoundError`)
  - 创建 Provider 注册表 `src/providers/registry.py`:
    - 装饰器注册模式 `@registry.register()`
    - 单例模式实现
  - 创建 Provider 工厂 `src/providers/factory.py`:
    - 配置驱动实例化
    - 单例缓存 (相同配置复用实例)
  - 创建各分类 Provider 基类:
    - `BaseEmbeddingProvider` (`src/providers/embedding/base.py`)
    - `BaseRerankProvider` + `RerankResult` (`src/providers/rerank/base.py`)
    - `BaseLLMProvider` (`src/providers/llm/base.py`)
  - 异步方法默认实现 (asyncio.to_thread 包装同步方法)
- **测试**: TC-1.3.1 ~ TC-1.3.4 全部通过 (29 个测试用例)

### 1.2: MCP Server 基础实现 ✅

- **时间**: 2026-03-19 09:55
- **状态**: 完成
- **内容**:
  - 创建配置模块 `src/utils/config.py` (Config dataclass, YAML 加载, 热重载)
  - 创建 MCP Server 入口 `src/mcp_server/server.py` (FastMCP 实例)
  - 创建基础工具 `src/mcp_server/tools/base.py`:
    - `ping` - 测试服务器连通性
    - `get_config` - 获取当前配置
    - `reload_config` - 热重载配置
    - `list_tools` - 列出所有工具
    - `get_server_info` - 获取服务器信息
  - 目录结构: 将 `src/mcp/` 重命名为 `src/mcp_server/` 避免 MCP SDK 包名冲突
- **测试**: TC-1.2.1 ~ TC-1.2.4 全部通过 (12 个测试用例)

### 1.1: 项目初始化 ✅

- **时间**: 2026-03-19 09:15
- **状态**: 完成
- **内容**: 创建项目结构、Git仓库、虚拟环境、配置文件
- **测试**: TC-1.1.1 ~ TC-1.1.4 全部通过

---

## 版本说明

- **[Major]**: 不兼容的 API 变更
- **[Minor]**: 向后兼容的功能新增
- **[Patch]**: 向后兼容的问题修复