# RagHubMCP 更新日志

本文件记录项目所有重要变更。

格式遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

---

## [Unreleased]

### 待开发

- Web 控制台
- 效果对比仪表盘

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