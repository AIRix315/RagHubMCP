# RagHubMCP 项目结构

**文档版本**: v1.0  
**创建日期**: 2026-03-19

---

## 目录结构

```
RagHubMCP/
│
├── backend/                          # 后端服务
│   ├── src/
│   │   ├── __init__.py
│   │   ├── main.py                   # FastAPI 入口
│   │   ├── config.py                 # 配置管理
│   │   │
│   │   ├── api/                      # REST API
│   │   │   ├── __init__.py
│   │   │   ├── routes.py             # 路由定义
│   │   │   └── schemas.py            # 请求/响应模型
│   │   │
│   │   ├── mcp/                      # MCP Server
│   │   │   ├── __init__.py
│   │   │   ├── server.py             # MCP Server 实现
│   │   │   └── tools/                # MCP 工具
│   │   │       ├── __init__.py
│   │   │       ├── query_with_rerank.py  # 带 Rerank 的查询
│   │   │       ├── benchmark.py          # 效果对比测试
│   │   │       ├── rerank.py             # 独立 Rerank
│   │   │       └── collection.py         # Collection 管理
│   │   │
│   │   ├── providers/                # 模型 Provider
│   │   │   ├── __init__.py
│   │   │   ├── base.py               # 抽象基类定义
│   │   │   ├── factory.py            # Provider 工厂
│   │   │   ├── embedding/            # Embedding Provider
│   │   │   │   ├── __init__.py
│   │   │   │   ├── ollama.py         # Ollama 实现
│   │   │   │   ├── openai.py         # OpenAI 实现
│   │   │   │   └── http.py           # 自定义 HTTP
│   │   │   ├── rerank/               # Rerank Provider
│   │   │   │   ├── __init__.py
│   │   │   │   ├── flashrank.py      # FlashRank 实现
│   │   │   │   ├── cohere.py         # Cohere API
│   │   │   │   └── jina.py           # Jina API
│   │   │   └── llm/                  # LLM Provider (可选)
│   │   │       ├── __init__.py
│   │   │       ├── ollama.py
│   │   │       └── openai.py
│   │   │
│   │   ├── chunkers/                 # 代码切分
│   │   │   ├── __init__.py
│   │   │   ├── base.py               # Chunker 抽象基类
│   │   │   ├── registry.py           # 插件注册中心
│   │   │   ├── simple.py             # 简单字符切分
│   │   │   ├── line.py               # 行切分
│   │   │   └── markdown.py           # Markdown 标题切分
│   │   │
│   │   ├── indexer/                  # 代码索引
│   │   │   ├── __init__.py
│   │   │   ├── scanner.py            # 文件扫描
│   │   │   ├── indexer.py            # 索引编排
│   │   │   └── watcher.py            # 文件监听 (Phase 2)
│   │   │
│   │   ├── storage/                  # 存储层
│   │   │   ├── __init__.py
│   │   │   ├── chroma_store.py       # Chroma 向量存储
│   │   │   └── metadata.py           # 元数据管理
│   │   │
│   │   └── utils/                    # 工具函数
│   │       ├── __init__.py
│   │       ├── logger.py             # 日志配置
│   │       └── helpers.py            # 通用工具
│   │
│   ├── tests/                        # 测试
│   │   ├── __init__.py
│   │   ├── conftest.py               # pytest 配置
│   │   ├── test_providers/
│   │   ├── test_chunkers/
│   │   ├── test_indexer/
│   │   ├── test_mcp/
│   │   └── test_api/
│   │
│   ├── pyproject.toml                # 项目配置
│   ├── requirements.txt              # 依赖锁定
│   ├── config.yaml                   # 应用配置
│   └── .env.example                  # 环境变量模板
│
├── frontend/                         # Web 控制台
│   ├── src/
│   │   ├── main.ts                   # 入口文件
│   │   ├── App.vue                   # 根组件
│   │   │
│   │   ├── components/               # 组件
│   │   │   ├── layout/               # 布局组件
│   │   │   │   ├── Sidebar.vue
│   │   │   │   ├── Header.vue
│   │   │   │   └── Footer.vue
│   │   │   ├── config/               # 配置组件
│   │   │   │   ├── DatabaseConfig.vue
│   │   │   │   ├── ModelConfig.vue
│   │   │   │   └── ParamsConfig.vue
│   │   │   ├── collection/           # Collection 组件
│   │   │   │   ├── CollectionList.vue
│   │   │   │   ├── CollectionStats.vue
│   │   │   │   └── DocumentPreview.vue
│   │   │   └── benchmark/            # 效果对比组件
│   │   │       ├── TestConfig.vue
│   │   │       ├── ResultTable.vue
│   │   │       ├── ResultChart.vue
│   │   │       └── Recommendation.vue
│   │   │
│   │   ├── views/                    # 页面
│   │   │   ├── Home.vue              # 首页
│   │   │   ├── Config.vue            # 配置管理
│   │   │   ├── Collections.vue       # Collection 管理
│   │   │   ├── Benchmark.vue         # 效果对比
│   │   │   └── Settings.vue          # 设置
│   │   │
│   │   ├── stores/                   # 状态管理 (Pinia)
│   │   │   ├── config.ts             # 配置状态
│   │   │   ├── collection.ts         # Collection 状态
│   │   │   └── benchmark.ts          # Benchmark 状态
│   │   │
│   │   ├── api/                      # API 请求
│   │   │   ├── index.ts              # 请求封装
│   │   │   ├── config.ts             # 配置 API
│   │   │   ├── collection.ts         # Collection API
│   │   │   └── benchmark.ts          # Benchmark API
│   │   │
│   │   ├── types/                    # 类型定义
│   │   │   ├── config.ts
│   │   │   ├── collection.ts
│   │   │   └── benchmark.ts
│   │   │
│   │   └── router/                   # 路由
│   │       └── index.ts
│   │
│   ├── public/
│   ├── package.json
│   ├── vite.config.ts
│   ├── tsconfig.json
│   └── index.html
│
├── docker/                           # Docker 配置
│   ├── Dockerfile.backend            # 后端镜像
│   ├── Dockerfile.frontend           # 前端镜像
│   └── docker-compose.yaml           # 编排配置
│
├── Docs/                             # 文档
│   ├── 01-RagHubMCP_20260319.md      # 可行性分析
│   ├── 02-RagHubMCP-Tech_20260319.md # 技术选型
│   ├── 03-RagHubMCP-MVP_20260319.md  # MVP 范围
│   └── 04-Project-Structure_20260319.md # 本文档
│
├── data/                             # 数据目录 (gitignore)
│   └── chroma/                       # Chroma 持久化
│
├── logs/                             # 日志目录 (gitignore)
│
├── .gitignore
├── TODO.md                           # 开发计划
└── README.md                         # 项目说明
```

---

## 模块职责

### 后端模块

| 模块 | 职责 | 关键文件 |
|------|------|---------|
| api | REST API 路由与请求处理 | routes.py, schemas.py |
| mcp | MCP Server 与工具实现 | server.py, tools/*.py |
| providers | 模型后端抽象与实现 | base.py, factory.py, */*.py |
| chunkers | 代码切分插件 | base.py, registry.py, *.py |
| indexer | 文件扫描与索引编排 | scanner.py, indexer.py |
| storage | 向量存储与元数据管理 | chroma_store.py, metadata.py |

### 前端模块

| 模块 | 职责 | 关键文件 |
|------|------|---------|
| views | 页面组件 | Home.vue, Config.vue, ... |
| components | 可复用组件 | config/*, collection/*, ... |
| stores | 状态管理 | config.ts, collection.ts, ... |
| api | API 请求封装 | index.ts, config.ts, ... |
| types | TypeScript 类型定义 | config.ts, collection.ts, ... |

---

## 文件命名规范

### Python

- 模块文件：小写下划线 (`scanner.py`)
- 类名：大驼峰 (`ChunkerPlugin`)
- 函数名：小写下划线 (`get_chunker`)
- 常量：大写下划线 (`MAX_FILE_SIZE`)

### TypeScript/Vue

- 组件文件：大驼峰 (`CollectionList.vue`)
- 类型文件：小写 (`config.ts`)
- Store 文件：小写 (`collection.ts`)
- 接口名：大驼峰 (`IConfig`)

---

## 配置文件说明

### backend/config.yaml

```yaml
# 服务配置
server:
  host: "0.0.0.0"
  port: 8000

# Chroma 配置
chroma:
  persist_dir: "./data/chroma"

# Provider 配置
providers:
  embedding:
    default: ollama-bge
    instances:
      - name: ollama-bge
        type: ollama
        base_url: "http://localhost:11434"
        model: "bge-m3"
        
  rerank:
    default: flashrank
    instances:
      - name: flashrank
        type: flashrank
        model: "ms-marco-TinyBERT-L-2-v2"

# 索引配置
indexer:
  chunk_size: 500
  chunk_overlap: 50
  max_file_size: 1048576  # 1MB
  file_types:
    - ".py"
    - ".ts"
    - ".js"
    - ".md"
  exclude_dirs:
    - "node_modules"
    - ".git"
    - "__pycache__"
```

### backend/.env.example

```bash
# 环境
APP_ENV=development

# Ollama
OLLAMA_BASE_URL=http://localhost:11434

# OpenAI (可选)
OPENAI_API_KEY=sk-xxx

# Cohere (可选)
COHERE_API_KEY=xxx
```

---

*最后更新: 2026-03-19*