# RagHubMCP AI 自主部署指南

**版本**: v1.0  
**创建日期**: 2026-03-20  
**适用范围**: AI Agent（OpenCode、Cursor、Windsurf、CherryStudio 等）

---

## 概述

本文档为 AI Agent 提供自主部署 RagHubMCP 的详细指南。AI Agent 应严格按照以下步骤执行部署，并在每一步完成后向用户报告进度。

---

## 部署流程

### 步骤 1: 环境诊断

**目标**: 全面检查用户环境，确定最佳部署方式

**执行命令**:
```bash
python scripts/check/check-env.py --json
```

**检查项**:
- [ ] Python 版本 >= 3.11
- [ ] Node.js 版本 >= 18
- [ ] Git 已安装
- [ ] Docker 可用性（可选）
- [ ] Ollama 已安装（可选）
- [ ] 端口可用性（8818, 3315）
- [ ] 硬件资源

**输出**: 环境报告 JSON

**决策逻辑**:
```
IF Docker 可用且运行中:
    → 推荐 Docker 部署
ELIF Python >= 3.11 AND Node >= 18:
    → 推荐原生部署
ELIF Python >= 3.11:
    → 推荐仅后端部署
ELSE:
    → 提供手动安装指南
```

---

### 步骤 2: 初始化配置

**目标**: 创建统一的配置文件

**执行命令**:
```bash
python scripts/config/init-config.py --install-dir <path>
```

**配置文件位置**:
- Windows: `%USERPROFILE%\.config\RagHubMCP\config.json`
- macOS/Linux: `~/.config/RagHubMCP/config.json`

**配置内容**:
- 安装目录
- 数据目录
- 端口配置
- 模型配置

---

### 步骤 3: 选择部署模式

根据环境检测结果，选择以下部署方式之一：

#### 方式 A: Docker 部署（推荐）

**前置条件**: Docker 已安装并运行

**执行命令**:
```bash
cd scripts/docker
docker-compose up -d
```

**验证**:
```bash
curl http://localhost:8818/api/config
```

#### 方式 B: 原生部署

**前置条件**: Python >= 3.11, Node >= 18

**后端安装**:
```bash
cd backend
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
pip install -e ".[dev]"
python -m src.main
```

**前端安装**:
```bash
cd frontend
npm install
npm run dev
```

---

### 步骤 4: 组件安装（可选）

#### 安装 Ollama

```bash
python scripts/setup/setup-ollama.py --start
```

#### 安装 Qdrant（可选）

```bash
python scripts/setup/setup-qdrant.py --start
```

#### 验证 Chroma

```bash
python scripts/setup/setup-chroma.py --check
```

---

### 步骤 5: MCP 配置生成

**目标**: 为用户使用的 IDE 生成 MCP 配置

**支持的 IDE**:
- `claude_desktop` - Claude Desktop
- `cursor` - Cursor
- `windsurf` - Windsurf
- `vscode` - VS Code + Copilot
- `opencode` - OpenCode
- `cherystudio` - CherryStudio

**执行命令**:
```bash
# 打印配置
python scripts/config/generate-mcp-config.py --ide <ide_name> --print

# 写入配置文件
python scripts/config/generate-mcp-config.py --ide <ide_name> --write
```

---

### 步骤 6: 验证测试

**验证后端**:
```bash
curl http://localhost:8818/api/config
```

**验证前端**:
```bash
curl http://localhost:3315
```

**验证 MCP**:
- 在 IDE 中检查 RagHub MCP 工具是否可用

---

## 错误处理

### 常见错误及解决方案

| 错误 | 解决方案 |
|------|---------|
| 端口被占用 | 修改 config.json 中的端口配置 |
| Python 版本过低 | 指导用户升级 Python |
| pip 安装失败 | 检查网络，尝试使用镜像源 |
| Docker 未运行 | 启动 Docker 服务 |
| Ollama 未安装 | 提供安装链接或跳过 |

---

## 完成检查清单

部署完成后，AI Agent 应确认以下项目：

```markdown
## 部署完成确认

- [ ] 环境检测完成
- [ ] 配置文件已创建
- [ ] 部署模式已选择
- [ ] 组件安装完成
- [ ] MCP 配置已生成
- [ ] 后端服务可访问 (http://localhost:8818)
- [ ] 前端服务可访问 (http://localhost:3315)
- [ ] 用户已确认 MCP 工具可用
```

---

## 向用户报告

部署完成后，向用户提供以下信息：

```
🎉 RagHubMCP 部署完成！

配置文件: ~/.config/RagHubMCP/config.json

访问地址:
  - 控制台: http://localhost:3315
  - API 文档: http://localhost:8818/docs

启动命令:
  - 后端: cd backend && python -m src.main
  - 前端: cd frontend && npm run dev

MCP 配置:
  - 已生成 <IDE> 配置
  - 配置文件: <config_path>
```

---

*本文档由 RagHubMCP 团队编写*