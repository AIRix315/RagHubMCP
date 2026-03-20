# RagHubMCP 更新日志

本文件记录项目所有重要变更。

格式遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
版本本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

---

## [V2.0.1] - 2026-03-21

### 任务编号: V2架构合规修复

- **时间**: 2026-03-21
- **内容**: V2架构合规性修复 + 清理

### 移除的废弃功能

1. **MCP V1 工具完全移除** (`backend/src/mcp_server/tools/`)
   - 删除: `base.py`, `benchmark.py`, `hybrid.py`, `rerank.py`, `search.py`, `watcher.py`, `migrate.py`
   - **保留**: V2 `query` 和 `ingest` 工具
   - 遵循 RULE-10: V2 MCP接口收敛

### 新增功能

1. **CORS 安全配置** (`backend/src/utils/config.py`)
   - 新增 `CORSConfig` 配置模型
   - 默认限制 origins 为 `localhost:3315` 和 `127.0.0.1:3315`
   - `config.yaml` 新增 `cors` 配置节

2. **依赖注入容器** (`backend/src/utils/container.py`)
   - `Container` 类管理单例和瞬态依赖
   - `injectable` 和 `inject` 装饰器
   - 全局容器实例管理

3. **公共错误处理** (`backend/src/mcp_server/tools/_errors.py`)
   - `error_response()` - 统一错误响应格式
   - `validate_collection_name()` - 集合名称验证
   - `validate_query()` - 查询字符串验证
   - `validate_documents()` - 文档列表验证

### 架构改进

| 规则 | 状态 | 说明 |
|------|------|------|
| RULE-1 | ✅ | V2 工具使用 Pipeline 作为唯一执行入口 |
| RULE-2 | ✅ | 所有模块接口化 (ABC 定义完整) |
| RULE-3 | ✅ | HybridSearchService 使用 VectorStore Provider 接口 |
| RULE-4 | ✅ | 全部能力可配置 (Profile/CORS) |
| RULE-10 | ✅ | MCP 接口收敛，仅保留 query/ingest |

### 测试结果

- 后端测试: **895 passed, 1 skipped**
- 前端测试: **247 passed**

### 删除的测试文件

- `test_server.py` - 测试 V1 base 工具
- `test_benchmark_tool.py` - 测试 V1 benchmark 工具
- `test_rerank_tool.py` - 测试 V1 rerank 工具
- `test_search_tool.py` - 测试 V1 search 工具
- `test_mcp_api.py` - 测试 MCP API 集成
- `test_index_search.py` - 测试索引搜索集成

---

## [V2.0.0] - 2026-03-20

### 任务编号: V2开发 - Phase 1-3

- **时间**: 2026-03-20 23:57
- **内容**: V2 Pipeline架构核心实现

### 新增功能

1. **Pipeline模块** (`backend/src/pipeline/`)
   - RAGPipeline抽象基类定义
   - RAGResult和Document数据类
   - DefaultRAGPipeline默认实现
   - PipelineFactory配置驱动工厂
   - Retriever接口 (HybridRetriever, VectorRetriever)
   - Reranker接口 (PipelineReranker, NoOpReranker, FallbackReranker)
   - ContextBuilder接口 (DefaultContextBuilder)

2. **Profile配置系统**
   - fast/balanced/accurate三种配置
   - 配置驱动Pipeline创建

3. **MCP V2接口** (`backend/src/mcp_server/tools/v2/`)
   - query工具 - 统一检索入口
   - ingest工具 - 统一索引入口
   - V1 工具已在 V2.0.1 中移除

4. **测试用例**
   - 新增13个pipeline单元测试

### 架构改进

- Pipeline作为唯一执行入口 (RULE-1)
- 所有模块接口化 (RULE-2)
- 禁止直接依赖具体实现 (RULE-3)
- 全部能力可配置 (RULE-4)

---

