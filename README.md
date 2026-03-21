# RagHubMCP

**通用代码 RAG 中枢** - MCP Server + FlashRank Rerank + 效果对比仪表盘

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![Node](https://img.shields.io/badge/Node.js-18+-green.svg)](https://nodejs.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 项目定位

**核心价值**: 效果对比仪表盘 - 让用户测试、调配、找到最优配置

**核心洞察**: 模型在迅速发展，用户希望得到更好的结果。本项目与其他竞品的区别在于：竞品提供便捷的封装方案，本项目的便捷之上，把封装全部打开，让用户自己去调配。

---

## 快速安装

### 方式一：一键脚本（推荐）

```bash
# 1. 克隆仓库
git clone https://github.com/your-username/RagHubMCP.git
cd RagHubMCP

# 2. 初始化配置
python scripts/config/init-config.py

# 3. 环境检查
python scripts/check/check-env.py

# 4. 一键安装
python scripts/install/install.py
```

### 方式二：Docker 部署

```bash
# 克隆并启动
git clone https://github.com/your-username/RagHubMCP.git
cd RagHubMCP/scripts/docker
docker-compose up -d

# 访问服务
# 前端: http://localhost:3315
# 后端: http://localhost:8818
```

### 方式三：手动安装

**后端**:
```bash
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
pip install -e ".[dev]"
python -m src.main
```

**前端**:
```bash
cd frontend
npm install
npm run dev
```

---

## 访问地址

| 服务 | 地址 |
|------|------|
| Web 控制台 | http://localhost:3315 |
| API 文档 | http://localhost:8818/docs |
| MCP Server | 配置后可在 IDE 中直接调用 |

---

## MCP 集成

生成 MCP 配置文件，支持多种 IDE：

```bash
# 查看支持的 IDE
python scripts/config/generate-mcp-config.py --list

# 生成 Claude Desktop 配置
python scripts/config/generate-mcp-config.py --ide claude_desktop --print

# 写入配置文件
python scripts/config/generate-mcp-config.py --ide cursor --write
```

**支持的 IDE**: Claude Desktop, Cursor, Windsurf, VS Code, OpenCode, CherryStudio

---

## 功能特性

### 核心功能

- **向量检索** - Chroma/Qdrant 向量数据库支持
- **Rerank 重排** - FlashRank 高效重排，提升检索精度
- **混合搜索** - BM25 + 向量检索融合
- **效果对比** - 多配置对比测试，找到最优方案

### MCP 工具

| 工具 | 描述 |
|------|------|
| `chroma_query_with_rerank` | 向量检索 + Rerank 组合 |
| `benchmark_search_config` | 多配置性能对比 |
| `rerank_documents` | 独立文档重排 |
| `hybrid_search` | 混合搜索 |
| `index_directory` | 目录索引 |

---

## 技术栈

| 层级 | 技术选型 |
|------|---------|
| 后端语言 | Python 3.11+ |
| 后端框架 | FastAPI |
| 协议层 | MCP |
| 向量数据库 | Chroma / Qdrant |
| Rerank | FlashRank |
| 前端框架 | Vue 3 + TypeScript |
| UI 组件 | shadcn-vue |

---

## 项目结构

```
RagHubMCP/
├── backend/              # 后端服务
│   ├── src/              # 源代码
│   │   ├── mcp_server/   # MCP 工具
│   │   ├── providers/    # Provider 实现
│   │   ├── services/     # 业务服务
│   │   └── api/          # REST API
│   ├── tests/            # 测试 (512+ tests)
│   └── config.yaml       # 配置文件
├── frontend/             # Web 控制台
│   └── src/
│       ├── views/        # 页面组件
│       ├── stores/       # 状态管理
│       └── composables/  # 组合式函数
├── scripts/              # 部署脚本
│   ├── config/           # 配置管理
│   ├── check/            # 环境检查
│   ├── setup/            # 组件安装
│   ├── install/          # 一键安装
│   └── docker/           # Docker 配置
├── schemas/              # JSON Schema
└── Docs/                 # 文档
```

---

## 部署脚本

每个脚本可独立运行：

```bash
# 配置初始化
python scripts/config/init-config.py --help

# 环境检查
python scripts/check/check-env.py --json

# 安装 Ollama
python scripts/setup/setup-ollama.py --check

# 安装 Qdrant
python scripts/setup/setup-qdrant.py --start

# 验证 Chroma
python scripts/setup/setup-chroma.py

# 生成 MCP 配置
python scripts/config/generate-mcp-config.py --ide claude_desktop
```

---

## 文档

详细安装部署指南请参考项目 Wiki。

---

## License

MIT