# RagHubMCP 更新日志

本文件记录项目所有重要变更。

格式遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
版本本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

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
   - 向后兼容旧工具

4. **测试用例**
   - 新增13个pipeline单元测试

### 架构改进

- Pipeline作为唯一执行入口 (RULE-1)
- 所有模块接口化 (RULE-2)
- 禁止直接依赖具体实现 (RULE-3)
- 全部能力可配置 (RULE-4)

---

