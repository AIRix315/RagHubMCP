# RagHubMCP PROJECT KNOWLEDGE BASE

**Generated:** 2026-03-23
**Commit:** 3c5c7d9
**Branch:** main

> **⚠️ 最高规则**: 本项目所有任务必须遵守 `RULE.md` 的执行准则。任何开发、修改、发布都需遵循该文档。

## OVERVIEW

通用代码 RAG 中枢 - MCP Server + FlashRank Rerank + 效果对比仪表盘。Python (FastAPI) 后端 + Vue 3 前端，支持 Chroma/Qdrant 向量检索、混合搜索、Pipeline 架构。

**核心价值**: 与竞品不同，本项目把封装全部打开，让用户测试、调配、找到最优配置。

## STRUCTURE

```
RagHubMCP/
├── backend/           # Python 3.11+ FastAPI 服务
│   ├── src/raghub_mcp/   # 核心包
│   │   ├── api/          # REST API 路由
│   │   ├── mcp_server/    # MCP 工具实现
│   │   ├── pipeline/      # RAG Pipeline 核心架构
│   │   ├── providers/     # LLM/Embedding/Rerank/VectorStore
│   │   ├── rerank_engine/ # 重排引擎 (core/scorers/strategies)
│   │   ├── chunkers/      # 代码分块 (AST-based)
│   │   ├── indexer/       # 文件索引/增量更新
│   │   └── ...
│   ├── tests/         # pytest 测试 (81 files)
│   └── config.yaml    # 服务配置
├── frontend/          # Vue 3 + TypeScript + Vite
│   └── src/
│       ├── views/     # 页面组件
│       ├── stores/    # Pinia 状态管理
│       ├── api/       # API 客户端
│       └── __tests__/ # Vitest 测试
├── scripts/          # 部署/安装脚本
├── pack/             # 多平台打包
│   ├── go/           # Go 分发器 (RHM.exe)
│   │   ├── main.go   # 入口点，服务编排
│   │   ├── process.go # Python 进程管理
│   │   ├── proxy.go  # HTTP 反向代理
│   │   ├── tray.go   # 系统托盘
│   │   ├── cli.go    # CLI 命令处理
│   │   └── embed.go  # 资源嵌入
│   ├── python/       # PyInstaller 打包
│   └── embed/        # 嵌入式资源
├── Docs/             # 设计文档 (01-24 编号排列)
└── schemas/          # JSON Schema 配置
```

## WHERE TO LOOK

| Task | Location | Notes |
|------|----------|-------|
| 添加新 MCP 工具 | `backend/src/raghub_mcp/mcp_server/tools/` | v2 工具在 `v2/__init__.py` |
| 修改 Pipeline 流程 | `backend/src/raghub_mcp/pipeline/` | 参考 RULE.md 架构规则 |
| 添加新 Provider | `backend/src/raghub_mcp/providers/{embedding,llm,rerank,vectorstore}/` | 需实现 Base 类 |
| 修改 Rerank 策略 | `backend/src/raghub_mcp/rerank_engine/{scorers,strategies}/` | 可组合策略 |
| 前端页面修改 | `frontend/src/views/` | 使用 shadcn-vue 组件 |
| API 客户端修改 | `frontend/src/api/` | 对应 backend API |
| 打包分发程序 | `pack/go/` | Go 分发器 (main.go 入口) |
| 系统托盘功能 | `pack/go/tray.go` | 跨平台托盘菜单 |
| 服务进程管理 | `pack/go/process.go` | Python 进程启动/监控 |
| HTTP 代理配置 | `pack/go/proxy.go` | 反向代理到 Python 服务 |
| 配置管理 | `backend/config.yaml` + `backend/src/raghub_mcp/utils/config.py` | YAML + Pydantic |
| 测试后端 | `backend/tests/test_*/` | pytest + asyncio |
| 测试前端 | `frontend/src/__tests__/` | Vitest + jsdom |

## CONVENTIONS

### Python (Backend)

- **Line length**: 100 chars (ruff)
- **Type hints**: Required (mypy strict mode)
- **Imports**: `raghub_mcp.*` 绝对导入，禁止相对导入
- **Docstrings**: Google style
- **Tests**: `tests/` 目录，`test_*.py` 命名

### TypeScript (Frontend)

- **Path alias**: `@/*` → `src/*` (tsconfig)
- **Strict mode**: enabled
- **Component naming**: PascalCase (`.vue` files)
- **Tests**: `__tests__/` 目录，`*.test.ts` 命名

### Git

- **Commit types**: feat/fix/docs/style/refactor/test/chore
- **Branches**: main (stable), develop, feature/*, fix/*
- **Version source**: 根目录 `version.txt` (唯一版本号来源)

## ANTI-PATTERNS (THIS PROJECT)

### ❌ FORBID-1: 重写全部代码
→ 渐进式重构，每步可验证

### ❌ FORBID-2: 引入复杂 DAG
→ Pipeline 保持线性流程

### ❌ FORBID-3: 增加过多配置项
→ 用户只需选择 Profile (fast/balanced/accurate)

### ❌ FORBID-4: 跳过验证
→ V2 命中率必须 ≥ V1 + 20%

### ❌ FORBID-5: 直接依赖具体实现
```python
# ❌ 错误
from chroma_service import ...

# ✅ 正确
vector_db.search(...)  # 通过接口
```

### ❌ Shell 命令禁止 `nul`
```bash
# ❌ Git Bash 会创建 nul 文件
mkdir -p some/path 2>nul

# ✅ 正确
mkdir -p some/path 2>/dev/null
```

### ❌ 版本号禁止手动修改
- 不得手动修改 `pyproject.toml` 或 `package.json`
- 版本号唯一来源: `version.txt`

## UNIQUE STYLES

### Pipeline 唯一入口
所有 RAG 流程必须通过 `pipeline.run()` 调用，MCP/REST 只调用 Pipeline：

```python
from raghub_mcp.pipeline import get_pipeline, execute_search

# 获取已配置的 pipeline
pipeline = get_pipeline()
result = await pipeline.run(query="...", options=PipelineOptions(...))
```

### Provider 工厂模式
所有 Provider 通过工厂创建，配置驱动：

```python
from raghub_mcp.providers import factory

embedding = factory.get_embedding_provider("ollama-bge")
rerank = factory.get_rerank_provider("flashrank-tiny")
vectorstore = factory.get_vectorstore_provider("chroma-local")
```

### 前端 API 类型生成
```bash
cd frontend
npm run gen:types  # 从 OpenAPI Schema 生成 TypeScript 类型
```

## COMMANDS

### Backend (Python 3.11+)

```bash
cd backend

# 安装 (dev)
pip install -e ".[dev]"

# 运行测试
pytest tests/ -v --tb=short --cov=src

# Lint
ruff check .
ruff format --check .

# Type check
mypy src --ignore-missing-imports

# 启动服务
python -m src.raghub_mcp.main
# 或通过入口脚本
raghub-mcp  # pyproject.toml [project.scripts]
```

### Frontend (Node.js 20)

```bash
cd frontend

# 安装依赖
npm install

# 开发模式
npm run dev  # http://localhost:3315

# 构建
npm run build

# 类型检查
npm run type-check

# 测试
npm run test       # watch mode
npm run test:run   # single run

# 生成 API 类型
npm run gen:types
```

### Scripts

```bash
# 配置初始化
python scripts/config/init-config.py

# 环境检查
python scripts/check/check-env.py

# MCP 配置生成
python scripts/config/generate-mcp-config.py --ide cursor --write
```

### CI/CD

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| `ci.yml` | push/PR to main/develop | Tests, lint, build, security |
| `eval.yml` | manual dispatch | RAG Pipeline 评估 |

### 打包分发 (Go)

**完整流程参考**: `Docs/24-Packaging-Attentions.md`

```bash
# Windows
cd pack && build.bat

# Linux/macOS  
cd pack && ./build.sh
```

| 模式 | 说明 | 文件大小 |
|------|------|---------|
| Go Wrapper Only | Go + 系统 Python | ~10MB |
| Full Bundle | Go + PyInstaller | ~150-300MB |

### 发布流程

详见 `Docs/24-Packaging-Attentions.md` 和 `RULE.md` 第三节。

## NOTES

### 入口文件

| 入口 | 类型 | 命令/路径 |
|------|------|---------|
| Backend Server | FastAPI | `raghub_mcp.main:main` 或 `python -m src.raghub_mcp.main` |
| Backend CLI | Click | `raghub` 命令 (query/provider/config/pipeline/status) |
| MCP Server | MCP | `raghub_mcp.mcp_server.server:main` |
| Frontend | Vue 3 | `frontend/src/main.ts` |
| **Go 分发器** | Go binary | `pack/go/main.go` → `RHM.exe` |

### 服务端口

| 服务 | 端口 |
|------|------|
| Frontend (Vite) | 3315 |
| Backend API | 8818 |
| MCP Server | 8818 (共享) |

### Go 分发器架构

详见 `pack/go/README.md`。

### 参考文档

| 文档 | 路径 |
|------|------|
| **最高规则** | `RULE.md` |
| 打包流程 | `Docs/24-Packaging-Attentions.md` |
| 变更日志 | `CHANGELOG.md` |
| 设计文档 | `Docs/01-*.md` ~ `Docs/24-*.md` |