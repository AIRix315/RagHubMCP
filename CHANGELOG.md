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