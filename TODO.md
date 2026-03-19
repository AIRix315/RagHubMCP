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

### 1.2 MCP Server 基础实现

- [ ] 创建 MCP Server 入口 (src/mcp/server.py)
- [ ] 实现 FastMCP 基础框架
- [ ] 配置 MCP 工具注册机制
- [ ] 实现配置加载逻辑

**测试用例**:
```
TC-1.2.1: MCP Server 启动成功
TC-1.2.2: MCP 客户端可连接
TC-1.2.3: list_tools 返回工具列表
TC-1.2.4: 配置热重载成功
```

---

### 1.3 Provider 抽象层

- [ ] 定义 EmbeddingProvider 抽象基类
- [ ] 定义 RerankProvider 抽象基类
- [ ] 定义 LLMProvider 抽象基类
- [ ] 实现 Provider 工厂模式

**测试用例**:
```
TC-1.3.1: 抽象类实例化报错（抽象方法未实现）
TC-1.3.2: 具体实现类实例化成功
TC-1.3.3: Provider 工厂根据配置创建正确实例
TC-1.3.4: 不支持的 provider 类型抛出明确异常
```

---

### 1.4 FlashRank Rerank 实现

- [ ] 实现 FlashRankRerankProvider
- [ ] 支持模型选择 (TinyBERT/MiniLM/MultiBERT)
- [ ] 实现 rerank 接口
- [ ] 添加模型缓存机制

**测试用例**:
```
TC-1.4.1: 模型首次加载成功
TC-1.4.2: 模型缓存命中，二次调用更快
TC-1.4.3: rerank 返回正确排序结果
TC-1.4.4: rerank 返回 score 在有效范围 [0, 1]
TC-1.4.5: 空文档列表返回空结果
TC-1.4.6: 单文档返回正确结果
TC-1.4.7: 不同模型切换成功
```

---

### 1.5 chroma_query_with_rerank 工具

- [ ] 实现向量检索 + Rerank 组合逻辑
- [ ] 支持 n_results / rerank_top_k 参数
- [ ] 支持元数据过滤
- [ ] 返回带分数的重排结果

**测试用例**:
```
TC-1.5.1: 查询空 collection 返回空结果
TC-1.5.2: 查询返回正确数量文档
TC-1.5.3: rerank_top_k 生效
TC-1.5.4: where 条件过滤生效
TC-1.5.5: 返回结果包含 scores
TC-1.5.6: 结果按 score 降序排列
TC-1.5.7: 无效 collection_name 抛出明确错误
```

---

### 1.6 benchmark_search_config 工具

- [ ] 实现多配置对比测试
- [ ] 计算 Recall 指标
- [ ] 计算 MRR 指标
- [ ] 计算延迟统计
- [ ] 返回最优配置推荐

**测试用例**:
```
TC-1.6.1: 单配置 benchmark 成功
TC-1.6.2: 多配置对比成功
TC-1.6.3: Recall 计算正确
TC-1.6.4: MRR 计算正确
TC-1.6.5: 延迟统计正确 (avg/min/max)
TC-1.6.6: 推荐配置是 MRR 最高的
TC-1.6.7: 空查询列表处理正确
```

---

### 1.7 rerank_documents 工具

- [ ] 实现独立 Rerank 工具
- [ ] 支持传入文档列表
- [ ] 返回重排后的文档和分数

**测试用例**:
```
TC-1.7.1: 文档列表重排成功
TC-1.7.2: 返回结果包含原文档内容
TC-1.7.3: 返回结果包含 score
TC-1.7.4: top_k 参数生效
```

---

### 1.8 文件扫描器

- [ ] 实现目录递归扫描
- [ ] 支持文件类型过滤 (.py, .ts, .js, .md)
- [ ] 支持排除规则 (.gitignore, node_modules 等)
- [ ] 实现最大文件大小限制

**测试用例**:
```
TC-1.8.1: 扫描空目录返回空列表
TC-1.8.2: 文件类型过滤生效
TC-1.8.3: 排除规则生效
TC-1.8.4: 大文件被跳过并记录
TC-1.8.5: 递归深度正确
TC-1.8.6: 符号链接处理正确
```

---

### 1.9 代码切分器

- [ ] 定义 ChunkerPlugin 抽象基类
- [ ] 实现 SimpleChunker (字符数切分)
- [ ] 实现 LineChunker (行数切分)
- [ ] 实现 MarkdownChunker (标题切分)
- [ ] 实现 ChunkerRegistry (插件注册中心)

**测试用例**:
```
TC-1.9.1: SimpleChunker 切分结果不超出 chunk_size
TC-1.9.2: overlap 参数生效
TC-1.9.3: LineChunker 切分正确
TC-1.9.4: MarkdownChunker 按标题切分
TC-1.9.5: Registry 选择正确 chunker
TC-1.9.6: 未知语言使用默认 chunker
```

---

### 1.10 索引编排

- [ ] 实现 Indexer 主逻辑
- [ ] 集成 Embedding Provider
- [ ] 实现批量入库逻辑
- [ ] 添加进度回调机制

**测试用例**:
```
TC-1.10.1: 索引单个文件成功
TC-1.10.2: 索引目录成功
TC-1.10.3: 增量索引只处理变更文件
TC-1.10.4: 进度回调正确触发
TC-1.10.5: 入库后可检索到内容
TC-1.10.6: 大批量索引不 OOM
```

---

### 1.11 前端项目初始化

- [ ] 创建 Vue 3 项目 (Vite + TypeScript)
- [ ] 安装 shadcn-vue 组件库
- [ ] 配置 Pinia 状态管理
- [ ] 配置 Vue Router
- [ ] 配置 API 请求封装

**测试用例**:
```
TC-1.11.1: npm run dev 启动成功
TC-1.11.2: 页面可访问
TC-1.11.3: TypeScript 编译无错误
TC-1.11.4: shadcn-vue 组件可用
```

---

### 1.12 配置管理页面

- [ ] 数据库配置组件
- [ ] 模型选择组件 (Embedding + Rerank)
- [ ] 参数配置表单
- [ ] 配置保存/加载功能

**测试用例**:
```
TC-1.12.1: 配置表单渲染正确
TC-1.12.2: 配置保存成功
TC-1.12.3: 配置加载成功
TC-1.12.4: 无效配置提示错误
TC-1.12.5: 连接测试成功/失败反馈
```

---

### 1.13 Collection 管理页面

- [ ] Collection 列表展示
- [ ] 文档统计信息
- [ ] 删除/清空操作
- [ ] 文档预览功能

**测试用例**:
```
TC-1.13.1: Collection 列表正确显示
TC-1.13.2: 文档统计准确
TC-1.13.3: 删除操作成功
TC-1.13.4: 清空操作成功
TC-1.13.5: 文档预览正确
```

---

### 1.14 效果对比页面

- [ ] 测试配置表单
- [ ] 对比结果表格
- [ ] 基础图表展示
- [ ] 配置推荐展示

**测试用例**:
```
TC-1.14.1: 测试配置表单提交成功
TC-1.14.2: 对比结果表格渲染正确
TC-1.14.3: 图表数据正确
TC-1.14.4: 推荐配置高亮显示
TC-1.14.5: 结果可导出
```

---

### 1.15 REST API 实现

- [ ] 配置管理 API
- [ ] 索引任务 API
- [ ] 检索测试 API
- [ ] Benchmark API

**测试用例**:
```
TC-1.15.1: GET /api/config 返回配置
TC-1.15.2: POST /api/config 更新配置
TC-1.15.3: POST /api/index 启动索引
TC-1.15.4: GET /api/index/status 查询状态
TC-1.15.5: POST /api/search 执行检索
TC-1.15.6: POST /api/benchmark 执行对比
TC-1.15.7: 错误响应格式统一
```

---

### 1.16 MVP 验收

- [ ] 端到端测试通过
- [ ] 性能基准达标
- [ ] 文档完善

**验收标准**:
```
AC-1.16.1: 所有 Phase 1 测试用例通过
AC-1.16.2: 索引 1000 文件 < 60s
AC-1.16.3: 检索延迟 < 500ms
AC-1.16.4: Rerank 延迟 < 200ms
AC-1.16.5: README 包含快速开始指南
```

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