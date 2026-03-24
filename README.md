# RagHubMCP

> Code RAG Hub for AI Assistants — Pipeline Architecture, Configurable Components

[![Version](https://img.shields.io/badge/version-2.6.12-blue)](./version.txt)
[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**RagHubMCP** provides code retrieval capabilities for AI coding assistants via the MCP protocol. Built on a configurable Pipeline architecture supporting multiple vector stores and reranking strategies.

[中文介绍](#中文介绍)

---

## Quick Start

### Single Binary (Recommended)

```bash
# Download for your platform
# macOS
wget https://github.com/your-username/RagHubMCP/releases/latest/download/RHM-2.6.12-darwin

# Linux
wget https://github.com/your-username/RagHubMCP/releases/latest/download/RHM-2.6.12-linux

# Windows (PowerShell)
Invoke-WebRequest -Uri "https://github.com/.../RHM-2.6.12.exe" -OutFile "RHM.exe"

# Run
chmod +x RHM-*
./RHM-2.6.12-linux
```

Access Web UI at `http://localhost:3315`

### From Source

```bash
git clone https://github.com/your-username/RagHubMCP.git
cd RagHubMCP
python scripts/install/install.py
```

---

## Features

| Module | Status | Description |
|--------|--------|-------------|
| **Pipeline V2** | ✅ Ready | Unified `query` and `ingest` entry points |
| **Profiles** | ✅ Ready | `fast` / `balanced` / `accurate` strategies |
| **Vector Stores** | ✅ Ready | Chroma, Qdrant support |
| **Rerank Engine** | ✅ Ready | Pluggable scorers (BM25, ONNX) with strategies |
| **MCP Tools** | ✅ Ready | query, ingest, chroma management |
| **Go Distributor** | ✅ Ready | ~10MB single binary with tray/proxy/process management |
| **Web Console** | ✅ Ready | Basic search interface |
| **AST Chunking** | 🚧 WIP | Python/TypeScript/Go support (partial) |
| **Hybrid Search** | 🚧 WIP | BM25 + vector fusion |
| **Benchmark Dashboard** | 🚧 WIP | Multi-config comparison |

---

## MCP Integration

Generate IDE configuration:

```bash
python scripts/config/generate-mcp-config.py --ide cursor --write
```

### Available Tools

| Tool | Description |
|------|-------------|
| `query` | Search with Pipeline V2 |
| `ingest` | Index documents |
| `chroma_*` | Collection management |

### Example Usage

```json
// Query
{
  "query": "how to implement authentication",
  "strategy": "accurate",
  "top_k": 5
}

// Ingest
{
  "documents": [{"text": "...", "metadata": {}}],
  "collection": "code_docs"
}
```

---

## CLI Commands

```bash
RHM --version              # Show version
RHM index /path/to/code    # Index directory
RHM search "query"         # Local search test
RHM --no-browser --no-tray # Server mode (no tray)
```

---

## Tech Stack

- **Backend**: Python 3.11, FastAPI, MCP
- **Frontend**: Vue 3, TypeScript
- **Distribution**: Go wrapper (~10MB)

---

## Status

⚠️ **This project is under active development.** V2 Pipeline core is stable. Advanced features (hybrid search, AST chunking, benchmark dashboard) are still evolving.

See [Docs/](Docs/) for architecture design and development plans.

---

## 中文介绍

**RagHubMCP** 是面向 AI 编程助手的代码 RAG 中枢。通过 MCP 协议与 Claude、Cursor 等 IDE 集成，提供可配置的 Pipeline 检索架构。

### 核心特点

- **Pipeline V2** — 统一的 `query` / `ingest` 入口
- **可配置策略** — fast / balanced / accurate 三档切换
- **组件可插拔** — Chroma/Qdrant 向量库，BM25/ONNX 重排器
- **单文件分发** — Go 包装器，~10MB，带系统托盘

### 快速开始

```bash
# 下载单文件版本
wget https://github.com/.../RHM-2.6.12-linux
chmod +x RHM-* && ./RHM-2.6.12-linux
```

访问 `http://localhost:3315`

### 状态说明

⚠️ **活跃开发中**。Pipeline 核心已稳定，高级功能（混合搜索、AST 分块、Benchmark 仪表盘）持续迭代。

---

## License

MIT © RagHubMCP
