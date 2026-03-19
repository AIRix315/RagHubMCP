# RagHubMCP 开发计划

**项目名称**: RagHubMCP - 通用代码 RAG 中枢  
**创建日期**: 2026-03-19

---

## 项目定位

**核心价值**: 效果对比仪表盘 - 让用户测试、调配、找到最优配置

**核心洞察**: 模型在迅速发展，用户希望得到更好的结果。本项目与其他竞品的区别在于：竞品提供便捷的封装方案，本项目的便捷之上，把封装全部打开，让用户自己去调配。

**用户收益**:
- 测试自己最需要的配置
- 找到效果最好的组合
- 理解每个参数的影响

---

## 技术栈

| 层级 | 技术选型 |
|------|---------|
| 后端语言 | Python 3.11+ |
| 后端框架 | FastAPI |
| 协议层 | MCP (modelcontextprotocol/python-sdk) |
| 向量数据库 | Chroma |
| Rerank | FlashRank |
| 前端框架 | Vue 3 + TypeScript |
| UI 组件 | shadcn-vue |
| 状态管理 | Pinia |

---

## 参考资源

| 资源 | 链接 | 用途 |
|------|------|------|
| MCP 协议规范 | https://modelcontextprotocol.io/ | 协议规范 |
| FastMCP 框架 | https://github.com/modelcontextprotocol/python-sdk | 服务端开发 |
| chroma-mcp 源码 | https://github.com/chroma-core/chroma-mcp | 实现参考 |
| FlashRank 文档 | https://github.com/PrithivirajDamodaran/FlashRank | Rerank 集成 |
| Chroma 文档 | https://docs.trychroma.com/ | 向量数据库 |
| shadcn-vue | https://www.shadcn-vue.com/ | UI 组件 |

---

## Phase 1: MVP

### 1.1 项目初始化 ✅

- [x] 创建项目目录结构
- [x] 配置 Python 虚拟环境
- [x] 初始化 pyproject.toml
- [x] 配置基础依赖
- [x] 创建配置文件模板

**测试用例**: ✅ 全部通过
```
TC-1.1.1: 虚拟环境激活成功 ✅
TC-1.1.2: pip install 无报错 ✅
TC-1.1.3: python -c "import fastapi; import chromadb; import flashrank" 成功 ✅
TC-1.1.4: 配置文件加载成功 ✅
```

**完成时间**: 2026-03-19 09:15

---

### 1.2 MCP Server 基础实现 ✅

- [x] 创建配置模块 (src/utils/config.py)
- [x] 创建 MCP Server 入口 (src/mcp_server/server.py)
- [x] 实现 FastMCP 基础框架
- [x] 配置 MCP 工具注册机制
- [x] 实现配置加载逻辑
- [x] 创建基础工具 (ping, get_config, reload_config, list_tools, get_server_info)

**测试用例**: ✅ 全部通过
```
TC-1.2.1: MCP Server 启动成功 ✅
TC-1.2.2: MCP 客户端可连接 ✅
TC-1.2.3: list_tools 返回工具列表 ✅
TC-1.2.4: 配置热重载成功 ✅
```

**完成时间**: 2026-03-19 09:54

---

### 1.3 Provider 抽象层 ✅

- [x] 定义 EmbeddingProvider 抽象基类
- [x] 定义 RerankProvider 抽象基类
- [x] 定义 LLMProvider 抽象基类
- [x] 实现 Provider 工厂模式

**测试用例**: ✅ 全部通过
```
TC-1.3.1: 抽象类实例化报错（抽象方法未实现） ✅
TC-1.3.2: 具体实现类实例化成功 ✅
TC-1.3.3: Provider 工厂根据配置创建正确实例 ✅
TC-1.3.4: 不支持的 provider 类型抛出明确异常 ✅
```

**完成时间**: 2026-03-19 10:16

---

### 1.4 FlashRank Rerank 实现 ✅

- [x] 实现 FlashRankRerankProvider
- [x] 支持模型选择 (TinyBERT/MiniLM/MultiBERT)
- [x] 实现 rerank 接口
- [x] 添加模型缓存机制

**测试用例**: ✅ 全部通过
```
TC-1.4.1: 模型首次加载成功 ✅
TC-1.4.2: 模型缓存命中，二次调用更快 ✅
TC-1.4.3: rerank 返回正确排序结果 ✅
TC-1.4.4: rerank 返回 score 在有效范围 [0, 1] ✅
TC-1.4.5: 空文档列表返回空结果 ✅
TC-1.4.6: 单文档返回正确结果 ✅
TC-1.4.7: 不同模型切换成功 ✅
```

**完成时间**: 2026-03-19 10:30

---

### 1.5a Ollama Embedding Provider ✅

- [x] 实现 OllamaEmbeddingProvider 类
- [x] 支持多种模型 (nomic-embed-text, bge-m3, mxbai-embed-large)
- [x] 实现同步和异步 embedding 方法
- [x] 实现批量 embedding 方法
- [x] 装饰器自动注册到 registry

**测试用例**: ✅ 全部通过
```
TC-1.5a.1: Provider 注册成功 ✅
TC-1.5a.2: 默认参数初始化 ✅
TC-1.5a.3: 自定义 base_url ✅
TC-1.5a.4: from_config 工厂方法 ✅
TC-1.5a.5: embed_documents 成功 ✅
TC-1.5a.6: embed_query 成功 ✅
TC-1.5a.7: dimension 属性 ✅
TC-1.5a.8: async embed_documents ✅
TC-1.5a.9: async embed_query ✅
TC-1.5a.10: batch 处理 ✅
```

**完成时间**: 2026-03-19

---

### 1.5 chroma_query_with_rerank 工具 ✅

- [x] 实现向量检索 + Rerank 组合逻辑
- [x] 支持 n_results / rerank_top_k 参数
- [x] 支持元数据过滤
- [x] 返回带分数的重排结果
- [x] 创建 ChromaService 单例服务

**测试用例**: ✅ 全部通过
```
TC-1.5.1: 查询空 collection 返回空结果 ✅
TC-1.5.2: 查询返回正确数量文档 ✅
TC-1.5.3: rerank_top_k 生效 ✅
TC-1.5.4: where 条件过滤生效 ✅
TC-1.5.5: 返回结果包含 scores ✅
TC-1.5.6: 结果按 score 降序排列 ✅
TC-1.5.7: 无效 collection_name 抛出明确错误 ✅
```

**完成时间**: 2026-03-19

---

### 1.6 benchmark_search_config 工具 ✅

- [x] 实现多配置对比测试
- [x] 计算 Recall@K 指标
- [x] 计算 MRR 指标
- [x] 计算延迟统计
- [x] 返回最优配置推荐

**测试用例**: ✅ 全部通过
```
TC-1.6.1: 单配置 benchmark 成功 ✅
TC-1.6.2: 多配置对比成功 ✅
TC-1.6.3: Recall 计算正确 ✅
TC-1.6.4: MRR 计算正确 ✅
TC-1.6.5: 延迟统计正确 (avg/min/max) ✅
TC-1.6.6: 推荐配置是 MRR 最高的 ✅
TC-1.6.7: 空查询列表处理正确 ✅
```

**完成时间**: 2026-03-19

---

### 1.7 rerank_documents 工具 ✅

- [x] 实现独立 Rerank 工具
- [x] 支持传入文档列表
- [x] 返回重排后的文档和分数

**测试用例**: ✅ 全部通过
```
TC-1.7.1: 文档列表重排成功 ✅
TC-1.7.2: 返回结果包含原文档内容 ✅
TC-1.7.3: 返回结果包含 score ✅
TC-1.7.4: top_k 参数生效 ✅
```

**完成时间**: 2026-03-19

---

### 1.8 文件扫描器 ✅

- [x] 实现目录递归扫描
- [x] 支持文件类型过滤 (.py, .ts, .js, .md)
- [x] 支持排除规则 (.gitignore, node_modules 等)
- [x] 实现最大文件大小限制

**测试用例**: ✅ 全部通过 (14 个测试)
```
TC-1.8.1: 扫描单个文件 ✅
TC-1.8.2: 递归扫描目录 ✅
TC-1.8.3: 文件类型过滤 ✅
TC-1.8.4: 排除目录 ✅
TC-1.8.5: 大文件跳过 ✅
TC-1.8.6: 空目录处理 ✅
```

**完成时间**: 2026-03-19

---

### 1.9 代码切分器 ✅

- [x] 定义 ChunkerPlugin 抽象基类
- [x] 实现 SimpleChunker (字符数切分)
- [x] 实现 LineChunker (行数切分)
- [x] 实现 MarkdownChunker (标题切分)
- [x] 实现 ChunkerRegistry (插件注册中心)

**测试用例**: ✅ 全部通过 (51 个测试)
```
TC-1.9.1: SimpleChunker 切分结果不超出 chunk_size ✅
TC-1.9.2: overlap 参数生效 ✅
TC-1.9.3: LineChunker 切分正确 ✅
TC-1.9.4: MarkdownChunker 按标题切分 ✅
TC-1.9.5: Registry 选择正确 chunker ✅
TC-1.9.6: 未知语言使用默认 chunker ✅
```

**完成时间**: 2026-03-19

---

### 1.10 索引编排 ✅

- [x] 实现 Indexer 主逻辑
- [x] 集成 Embedding Provider
- [x] 实现批量入库逻辑
- [x] 添加进度回调机制

**测试用例**: ✅ 全部通过 (12 个测试)
```
TC-1.10.1: 索引单个文件成功 ✅
TC-1.10.2: 索引目录成功 ✅
TC-1.10.3: 增量索引只处理变更文件 ✅
TC-1.10.4: 进度回调正确触发 ✅
TC-1.10.5: 入库后可检索到内容 ✅
TC-1.10.6: 大批量索引不 OOM ✅
```

**完成时间**: 2026-03-19

---

### 1.11 前端项目初始化 ✅

- [x] 创建 Vue 3 项目 (Vite + TypeScript)
- [x] 安装 shadcn-vue 组件库
- [x] 配置 Pinia 状态管理
- [x] 配置 Vue Router
- [x] 配置 API 请求封装
- [x] 创建视图组件 (Home, Config, Collections, Benchmark)

**测试用例**: ✅ 全部通过
```
TC-1.11.1: npm run dev 启动成功 ✅
TC-1.11.2: 页面可访问 ✅
TC-1.11.3: TypeScript 编译无错误 ✅
TC-1.11.4: shadcn-vue 组件可用 ✅
```

**完成时间**: 2026-03-19 18:29

---

### 1.12 配置管理页面 ✅

- [x] Provider 展示组件 (Embedding + Rerank)
- [x] 索引参数配置表单
- [x] 配置保存/加载功能
- [x] 集成 useConfigStore

**测试用例**: ✅ 全部通过
```
TC-1.12.1: 配置表单渲染正确 ✅
TC-1.12.2: 配置保存成功 ✅
TC-1.12.3: 配置加载成功 ✅
TC-1.12.4: 无效配置提示错误 ✅
```

**完成时间**: 2026-03-19 18:29

---

### 1.13 Collection 管理页面 ✅

- [x] Collection 列表展示
- [x] 文档统计信息
- [x] 删除操作 (含确认弹窗)
- [x] 集成 useCollectionStore

**测试用例**: ✅ 全部通过
```
TC-1.13.1: Collection 列表正确显示 ✅
TC-1.13.2: 文档统计准确 ✅
TC-1.13.3: 删除操作成功 ✅
```

**完成时间**: 2026-03-19 18:29

---

### 1.14 效果对比页面 ✅

- [x] 测试配置表单 (多配置支持)
- [x] 对比结果表格
- [x] 配置推荐展示 (最快配置高亮)
- [x] 详细结果展示

**测试用例**: ✅ 全部通过
```
TC-1.14.1: 测试配置表单提交成功 ✅
TC-1.14.2: 对比结果表格渲染正确 ✅
TC-1.14.3: 配置推荐高亮显示 ✅
```

**完成时间**: 2026-03-19 18:29

---

### 1.15 REST API 实现 ✅

- [x] 配置管理 API
- [x] 索引任务 API
- [x] 检索测试 API
- [x] Benchmark API

**测试用例**: ✅ 全部通过 (17 个测试)
```
TC-1.15.1: GET /api/config 返回配置 ✅
TC-1.15.2: POST /api/config 更新配置 ✅
TC-1.15.3: POST /api/index 启动索引 ✅
TC-1.15.4: GET /api/index/status 查询状态 ✅
TC-1.15.5: POST /api/search 执行检索 ✅
TC-1.15.6: POST /api/benchmark 执行对比 ✅
TC-1.15.7: 错误响应格式统一 ✅
```

**完成时间**: 2026-03-19

---

### 1.16 MVP 验收 ✅

- [x] 端到端测试通过
- [x] 性能基准定义
- [x] 文档完善

**验收标准**:
```
AC-1.16.1: 所有 Phase 1 测试用例通过 ✅ (214 tests)
AC-1.16.2: 索引 1000 文件 < 60s (需实际环境验证)
AC-1.16.3: 检索延迟 < 500ms (需实际环境验证)
AC-1.16.4: Rerank 延迟 < 200ms (FlashRank 模型已优化)
AC-1.16.5: README 包含快速开始指南 ✅
```

**完成时间**: 2026-03-19

---

## Phase 1.5: MVP 完善

> **说明**: 本阶段任务基于 `Docs/06-MVP-Upgrade-Analysis_20260319.md` 分析，在进入 Phase 2 前补齐 MVP 基础设施。

### 1.17 测试覆盖完善

**目标**: 建立完善的测试基础，支撑后续开发

- [ ] 创建 test_llm/ 目录结构
- [ ] 编写 test_llm_base.py — LLM 基类测试
- [ ] 编写 test_ollama_llm.py — OllamaLLM 测试
- [ ] 创建 test_integration/ 目录
- [ ] 编写 test_index_search.py — 索引→搜索集成测试
- [ ] 编写 test_mcp_api.py — MCP + API 联合测试
- [ ] 扩充 test_services/ — Embedding/Rerank 服务测试
- [ ] 运行全量测试验证
- [ ] 更新 TODO.md 标记完成
- [ ] 记录 CHANGELOG.md
- [ ] Git 提交，创建分支 mvp/v0.2.2

**参考位置**: `backend/tests/test_providers/`, `backend/tests/test_indexer/`

**测试用例**:
```
TC-1.17.1: test_llm/ 目录存在且非空
TC-1.17.2: test_integration/ 目录存在且非空
TC-1.17.3: 所有测试通过 (≥230 tests)
TC-1.17.4: 覆盖率 ≥ 70%
```

**完成记录**: （待填写日期+时刻）

---

### 1.18 Provider 层补全

**目标**: 补齐缺失的 Provider 实现，实现核心价值"效果对比"

**前置条件**: 1.17 完成

- [ ] 实现 OpenAIEmbeddingProvider — 参考 `backend/src/providers/embedding/ollama.py`，Context7: `openai embeddings`
- [ ] 编写 test_openai_embedding.py
- [ ] 实现 HTTPEmbeddingProvider — Context7: `httpx async client`
- [ ] 编写 test_http_embedding.py
- [ ] 实现 OllamaLLMProvider — 参考 `backend/src/providers/llm/base.py`，Context7: `ollama api chat`
- [ ] 实现 OpenAILLMProvider — Context7: `openai chat completions`
- [ ] 编写 test_openai_llm.py
- [ ] 实现 CohereRerankProvider — 参考 `backend/src/providers/rerank/flashrank.py`，Context7: `cohere rerank api`
- [ ] 编写 test_cohere_rerank.py
- [ ] 实现 JinaRerankProvider — Context7: `jina rerank api`
- [ ] 编写 test_jina_rerank.py
- [ ] 添加 get_model_info() 接口 — `backend/src/providers/base.py`
- [ ] 更新 config.yaml 配置示例
- [ ] 运行全量测试验证
- [ ] 更新 TODO.md 标记完成
- [ ] 记录 CHANGELOG.md
- [ ] Git 提交，创建分支 mvp/v0.3.0

**测试用例**:
```
TC-1.18.1: OpenAIEmbeddingProvider 可用
TC-1.18.2: HTTPEmbeddingProvider 可用
TC-1.18.3: OllamaLLMProvider 可用
TC-1.18.4: OpenAILLMProvider 可用
TC-1.18.5: CohereRerankProvider 可用
TC-1.18.6: JinaRerankProvider 可用
TC-1.18.7: get_model_info() 返回正确数据
TC-1.18.8: 所有测试通过 (≥250 tests)
```

**完成记录**: （待填写日期+时刻）

---

### 1.19 前端完善

**目标**: 补齐前端缺失功能，完善用户界面

**前置条件**: 1.18 完成

- [ ] 创建 Settings.vue 页面 — 参考 `frontend/src/views/Config.vue`，shadcn-vue 组件
- [ ] 添加 Settings 路由 — `frontend/src/router/index.ts`
- [ ] 创建 benchmark.ts Store — 参考 `frontend/src/stores/config.ts`，Pinia 最佳实践
- [ ] 更新 AppLayout.vue 导航 — `frontend/src/components/layout/AppLayout.vue`
- [ ] 前端测试补充 — `frontend/src/__tests__/`，Vitest
- [ ] 运行前端测试验证 — `npm run test`
- [ ] 前端构建验证 — `npm run build`
- [ ] 更新 TODO.md 标记完成
- [ ] 记录 CHANGELOG.md
- [ ] Git 提交，创建分支 mvp/v0.3.1

**测试用例**:
```
TC-1.19.1: Settings 页面可访问
TC-1.19.2: Settings 路由正常工作
TC-1.19.3: benchmark.ts Store 正常工作
TC-1.19.4: 前端构建成功
TC-1.19.5: 前端测试通过 (≥15 tests)
```

**完成记录**: （待填写日期+时刻）

---

### 1.20 Phase 1.5 验收

**目标**: 全面验收 Phase 1.5 完成情况，准备进入 Phase 2

**前置条件**: 1.17-1.19 全部完成

- [ ] 运行后端全量测试 — `pytest --tb=short`
- [ ] 运行前端全量测试 — `npm run test`
- [ ] 验证效果对比功能 — 手动测试 Ollama vs OpenAI
- [ ] 检查 Git 分支结构 — `git branch -a`
- [ ] 检查 CHANGELOG.md 记录完整
- [ ] 更新 TODO.md 标记 Phase 1.5 完成
- [ ] 记录 CHANGELOG.md 验收完成
- [ ] Git 合并到 main — 合并 mvp/v0.3.1 → main
- [ ] 推送到远程 — `git push --all`

**验收标准**:
```
AC-1.20.1: 后端测试全部通过 (≥250 tests)
AC-1.20.2: 前端测试全部通过 (≥15 tests)
AC-1.20.3: 效果对比功能可用（对比 Ollama vs OpenAI）
AC-1.20.4: Git 分支结构清晰
AC-1.20.5: CHANGELOG.md 更新完整
```

**完成记录**: （待填写日期+时刻）

---

## Phase 2: 功能增强

### 2.1 混合搜索

- [ ] 实现 TF-IDF 索引
- [ ] 实现混合检索融合算法
- [ ] 支持 BM25 + Vector 混合
- [ ] 可配置融合权重

**测试用例**:
```
TC-2.1.1: TF-IDF 索引成功
TC-2.1.2: 混合检索返回结果
TC-2.1.3: 融合权重生效
TC-2.1.4: 混合检索效果优于单一检索
```

---

### 2.2 多语言 AST 切分

- [ ] Tree-sitter 集成
- [ ] Python AST 切分
- [ ] TypeScript AST 切分
- [ ] Go AST 切分

**测试用例**:
```
TC-2.2.1: Python 函数级别切分
TC-2.2.2: Python 类级别切分
TC-2.2.3: TypeScript 函数切分
TC-2.2.4: Go 函数切分
```

---

### 2.3 Web 控制台增强

- [ ] 详细统计仪表盘
- [ ] 复杂可视化图表
- [ ] 实时进度展示 (WebSocket)

**测试用例**:
```
TC-2.3.1: 统计数据正确
TC-2.3.2: 图表交互正常
TC-2.3.3: WebSocket 连接成功
TC-2.3.4: 进度实时更新
```

---

### 2.4 Qdrant 支持

- [ ] 实现 Qdrant Provider
- [ ] 支持向量库切换
- [ ] 迁移工具

**测试用例**:
```
TC-2.4.1: Qdrant 连接成功
TC-2.4.2: 切换向量库成功
TC-2.4.3: Chroma → Qdrant 迁移成功
TC-2.4.4: 迁移后数据完整
```

---

### 2.5 增量索引

- [ ] 文件监听 (watchdog)
- [ ] 增量更新逻辑
- [ ] 变更检测

**测试用例**:
```
TC-2.5.1: 文件变更检测成功
TC-2.5.2: 新文件自动索引
TC-2.5.3: 修改文件自动更新
TC-2.5.4: 删除文件自动清理
```

---

## Phase 3: 企业级功能

### 3.1 代码图谱

- [ ] 依赖关系分析
- [ ] 调用链可视化
- [ ] 图谱存储

**测试用例**:
```
TC-3.1.1: Python import 分析
TC-3.1.2: 函数调用链提取
TC-3.1.3: 图谱可视化渲染
```

---

### 3.2 团队协作

- [ ] 共享索引
- [ ] 权限管理
- [ ] 多用户支持

**测试用例**:
```
TC-3.2.1: 用户注册/登录
TC-3.2.2: 索引共享
TC-3.2.3: 权限控制生效
```

---

### 3.3 CI/CD 集成

- [ ] GitHub Actions 集成
- [ ] Pre-commit hooks
- [ ] 自动索引更新

**测试用例**:
```
TC-3.3.1: Actions 触发索引
TC-3.3.2: Pre-commit 检查
TC-3.3.3: 自动更新成功
```

---

## 依赖清单

```toml
[project]
name = "raghub-mcp"
version = "0.1.0"
requires-python = ">=3.11"

dependencies = [
    "fastapi>=0.109.0",
    "uvicorn[standard]>=0.27.0",
    "modelcontextprotocol>=0.1.0",
    "chromadb>=0.4.22",
    "ollama>=0.1.0",
    "openai>=1.12.0",
    "httpx>=0.26.0",
    "flashrank>=0.2.0",
    "pydantic>=2.5.0",
    "pydantic-settings>=2.1.0",
    "python-dotenv>=1.0.0",
    "PyYAML>=6.0.0",
    "watchdog>=4.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
    "ruff>=0.2.0",
    "mypy>=1.8.0",
]
```

---

## 关键决策

| 决策项 | 选择 | 理由 |
|--------|------|------|
| 后端语言 | Python | RAG 生态最丰富 |
| 向量数据库 | Chroma | 已安装，零配置 |
| Rerank | FlashRank | 最小 4MB，无需 Torch |
| 前端框架 | Vue 3 + TypeScript | 适合管理界面 |
| 代码切分 | 简单切分优先 | 快速实现 |

---

*项目结构详见: Docs/04-Project-Structure_20260319.md*