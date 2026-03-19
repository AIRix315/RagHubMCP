# RagHubMCP 安装部署指南

**文档版本**: v1.0  
**创建日期**: 2026-03-20  
**适用范围**: 终端用户、DevOps工程师、AI Agent  

---

## 目录

1. [部署方案概述](#一部署方案概述)
2. [环境要求](#二环境要求)
3. [四层部署架构](#三四层部署架构)
4. [部署方式详解](#四部署方式详解)
5. [模型配置策略](#五模型配置策略)
6. [数据库配置建议](#六数据库配置建议)
7. [MCP配置导出](#七mcp配置导出)
8. [常见问题](#八常见问题)
9. [AI自主部署指南](#九ai自主部署指南)

---

## 一、部署方案概述

RagHubMCP 提供**四层递进式部署架构**，满足不同用户群体的需求：

```
┌─────────────────────────────────────────────────────────────┐
│  Layer 4: AI Agent 自主部署层                                │
│  面向Opencode、CheesyStudio等AI平台用户                      │
├─────────────────────────────────────────────────────────────┤
│  Layer 3: Docker 部署层                                      │
│  一键Docker Compose启动，适合有Docker环境的用户              │
├─────────────────────────────────────────────────────────────┤
│  Layer 2: 一键脚本部署层                                     │
│  自动化脚本安装，适合有基础开发环境的用户                    │
├─────────────────────────────────────────────────────────────┤
│  Layer 1: 环境检查与引导层                                   │
│  检查环境、提供修复建议、智能选择部署方式                      │
└─────────────────────────────────────────────────────────────┘
```

**核心理念**: "先诊断，后治疗" — 不假设用户环境，先全面检查，再智能推荐部署方式。

---

## 二、环境要求

### 2.1 基础环境

| 组件 | 最低版本 | 推荐版本 | 说明 |
|------|---------|---------|------|
| Python | 3.11+ | 3.11+ | 后端运行必需 |
| Node.js | 18+ | 20 LTS | 前端构建必需 |
| Git | 2.30+ | 最新 | 代码克隆必需 |
| Docker | 20.10+ | 24+ | Docker部署可选 |
| Docker Compose | 2.0+ | 2.20+ | Docker部署可选 |

### 2.2 模型环境（推荐）

| 模型服务 | 用途 | 推荐版本 |
|---------|------|---------|
| Ollama | Embedding + LLM | 0.3.0+ |
| 或 OpenAI API | 云端Embedding | - |

### 2.3 硬件建议

| 配置 | 适用场景 | 推荐模型 |
|------|---------|---------|
| 4GB内存/无GPU | 快速体验 | nomic-embed-text + TinyBERT |
| 8GB内存/无GPU | 标准使用 | bge-m3 + MiniLM |
| 16GB内存/有GPU | 最佳效果 | bge-m3 + MiniLM + Qwen 7B |

---

## 三四层部署架构

### 3.1 Layer 1: 环境检查与引导

**执行命令**:
```bash
# 跨平台环境检查
python scripts/check/check-env.py
```


**检查内容**:

- Python版本检测1.1+ /pip/uv/ poetry 可2用性
- Node.js 版本18+ /npm/yarn/ pnpm 可性
- Git环境：是否安装，能否访问GitHub
- Docker环境：Docker/Docker Compose 可用性，运行权限
- Ollama环境：是否安装，可用模型列表，硬件资源评估

**智能推荐逻辑**:
```
IF Docker可用:
    → 推荐Docker部署（无需配置Python/Node）
ELIF Python >= 3.11 AND Node >= 18:
    → 推荐一键脚本部署
ELIF 只有Python环境:
    → 推荐仅部署后端，前端稍后Docker部署
ELSE:
    → 提供详细手动安装指南
```

### 3.2 Layer 2: 一键脚本部署

**执行命令**:
```bash
# 跨平台一键部署
python scripts/install/install.py
```

**部署流程**:

| 步骤 | 操作 | 说明 |
|------|------|------|
| 1 | 环境检查 | 复用Layer 1检查 |
| 2 | 克隆代码 | `git clone https://github.com/user/RagHubMCP.git` |
| 3 | 安装后端 | 创建venv，pip install依赖 |
| 4 | 安装前端 | npm install，npm run build |
| 5 | 配置数据库 | 创建data目录，生成默认配置 |
| 6 | 配置模型 | 检测Ollama，提供配置选项 |
| 7 | 导出MCP配置 | 生成IDE配置文件 |
| 8 | 启动服务 | 前台/后台/Docker模式 |

**关键特性**:
- 自动创建虚拟环境
- 支持pip/uv多种安装工具
- 可选自动下载默认模型
- 交互式配置向导

### 3.3 Layer 3: Docker部署

**执行命令**:
```bash
# 一键Docker启动
docker-compose up -d
```

**服务架构**:

```yaml
# docker-compose.yml 结构
services:
  backend:    # Python FastAPI服务，端口8818
  frontend:   # Vue3前端，端口3315
  chroma:     # 向量数据库，端口8001（可选外部）
  # qdrant:   # 高性能向量库（可选）
```

**部署优势**:
- 无需本地Python/Node环境
- 环境隔离，避免冲突
- 一键启动所有服务
- 数据持久化到本地目录

### 3.4 Layer 4: AI自主部署

**适用场景**: Opencode、CheesyStudio、Cursor等AI平台的用户

**AI部署指令协议**:

AI Agent按照以下严格顺序执行部署：

```markdown
## AI部署流程

### 步骤1: 环境诊断
- [ ] 检查Python版本 >= 3.11
- [ ] 检查Node.js版本 >= 18
- [ ] 检查Git可用性
- [ ] 检查Docker（可选）
- [ ] 生成环境报告并告知用户

### 步骤2: 获取代码
- [ ] git clone 项目仓库
- [ ] 进入项目目录

### 步骤3: 选择部署模式
- [ ] 根据环境自动推荐部署方式
- [ ] 与用户确认部署模式

### 步骤4: 执行部署
- [ ] Docker模式: docker-compose up -d
- [ ] 原生模式: 运行install.py脚本

### 步骤5: 模型配置
- [ ] 检测Ollama是否安装
- [ ] 如果没有，提供选项：
  * 选项A: 帮助安装Ollama
  * 选项B: 配置云端API（OpenAI等）
  * 选项C: 跳过，稍后手动配置

### 步骤6: MCP配置导出
- [ ] 询问用户使用的IDE（Claude/Cursor/Windsurf等）
- [ ] 生成对应的MCP配置文件
- [ ] 提供配置文件的复制粘贴内容

### 步骤7: 验证测试
- [ ] 检查MCP工具列表
- [ ] 测试搜索功能
- [ ] 验证前端可访问
```

---

## 四、部署方式详解

### 4.1 方式一：Docker一键部署（推荐）

**适用用户**:
- 有Docker环境的用户
- 不想配置Python/Node环境的用户
- 需要快速体验的用户

**前置条件**:
- Docker >= 20.10
- Docker Compose >= 2.0
- 可用端口：8818（后端）、3315（前端）、8001（Chroma可选）

**执行步骤**:

```bash
# 1. 克隆仓库
git clone https://github.com/user/RagHubMCP.git
cd RagHubMCP

# 2. 复制配置文件模板
cp backend/.env.example backend/.env
# （可选）编辑.env配置模型参数

# 3. 一键启动
docker-compose up -d

# 4. 查看日志
docker-compose logs -f

# 5. 访问服务
# 前端: http://localhost:3315
# 后端API: http://localhost:8818
```

**目录挂载说明**:
- `./data:/app/data` - 数据持久化
- `./config.yaml:/app/config.yaml` - 配置文件
- `./logs:/app/logs` - 日志文件

### 4.2 方式二：一键脚本部署

**适用用户**:
- 已有Python 3.11+和Node 18+环境的用户
- 需要深度定制配置的用户
- 开发者用户

**执行步骤**:

```bash
# 1. 克隆仓库
git clone https://github.com/user/RagHubMCP.git
cd RagHubMCP

# 2. 运行一键安装脚本
python scripts/install/install.py

# 脚本交互流程:
# - 检查环境并报告
# - 询问是否自动安装Ollama（可选）
# - 选择部署模式（dev/prod）
# - 配置模型参数
# - 自动完成安装

# 3. 启动服务（根据脚本提示）
# 方式A: 前台运行
make dev

# 方式B: 后台运行
make start

# 方式C: 仅后端（用于AI工具集成）
cd backend && python -m src.main
```

### 4.3 方式三：手动分步部署

**适用用户**:
- 需要完全控制部署过程的高级用户
- 环境特殊的用户

**后端部署**:
```bash
cd backend

# 1. 创建虚拟环境
python -m venv venv

# 2. 激活环境（Windows）
venv\Scripts\activate
# 或（Linux/Mac）
# source venv/bin/activate

# 3. 安装依赖
pip install -e ".[dev]"

# 4. 复制配置
cp .env.example .env

# 5. 启动服务
python -m src.main
```

**前端部署**:
```bash
cd frontend

# 1. 安装依赖
npm install

# 2. 开发模式
npm run dev

# 或构建生产版本
npm run build
npm run preview
```

### 4.4 方式四：AI自主部署

**用户操作**:
1. 打开AI Agent（如Opencode、CheesyStudio）
2. 提供以下指令：

```
请帮我部署RagHubMCP。请严格按照以下步骤执行：
1. 先检查我的环境（Python、Node、Docker）
2. 根据环境推荐最佳部署方式
3. 自动完成部署
4. 配置模型（优先本地Ollama，如果没有则询问是否安装或使用云端API）
5. 生成我的MCP配置文件（我使用[Claude Desktop/Cursor/Windsurf]）
6. 验证服务是否正常运行

项目地址: https://github.com/user/RagHubMCP
```

**AI执行逻辑**:
- 读取 `AI_DEPLOYMENT_GUIDE.md`
- 严格按照8步骤顺序执行
- 每步完成后向用户报告
- 遇到错误提供解决方案

---

## 五、模型配置策略

### 5.1 智能模型推荐

系统根据硬件自动推荐最优配置：

#### 场景A：快速体验（4GB内存/无GPU）

```yaml
embedding:
  provider: ollama
  model: nomic-embed-text      # 768维，4GB内存可运行
  reason: "资源占用低，启动快速"

rerank:
  provider: flashrank
  model: ms-marco-TinyBERT-L-2-v2  # 仅4MB
  reason: "最小模型，瞬间加载"

llm:  # 可选
  provider: ollama
  model: qwen2.5:1.8b          # 1.8B参数小模型
```

#### 场景B：标准使用（8GB内存/推荐）

```yaml
embedding:
  provider: ollama
  model: bge-m3                # 1024维，多语言优秀

rerank:
  provider: flashrank
  model: ms-marco-MiniLM-L-12-v2  # 34MB，效果最佳

llm:
  provider: ollama
  model: qwen2.5:7b            # 7B参数，效果与速度平衡
```

#### 场景C：云端API（无本地GPU）

```yaml
embedding:
  provider: openai
  model: text-embedding-3-small  # 1536维
  api_key: ${OPENAI_API_KEY}

rerank:
  provider: cohere
  model: rerank-english-v3.0
  api_key: ${COHERE_API_KEY}
```

### 5.2 自动模型检测

部署脚本自动执行以下检测：

```python
# 自动检测逻辑
def auto_detect_models():
    # 1. 检测Ollama
    try:
        ollama_models = ollama.list()
        if 'bge-m3' in ollama_models:
            return "optimal_config"    # 最佳配置
        elif 'nomic-embed-text' in ollama_models:
            return "standard_config"   # 标准配置
    except:
        pass
    
    # 2. 检测硬件资源
    memory = psutil.virtual_memory().total / (1024**3)  # GB
    if memory < 8:
        return "lightweight_config"    # 轻量级配置
    
    # 3. 询问用户选择
    return "ask_user"
```

### 5.3 模型配置交互

```bash
# 部署脚本交互示例
$ python scripts/install.py

✓ 环境检查通过
✓ 检测到Ollama已安装

可用Embedding模型:
  [1] nomic-embed-text  - 快速，低资源（推荐快速体验）
  [2] bge-m3            - 多语言，高质量（推荐）
  [3] mxbai-embed-large - 英语最佳
  [4] 使用云端API（OpenAI等）

请选择 [1-4，默认2]: 2

✓ 已选择bge-m3

可用Rerank模型:
  [1] TinyBERT  - 4MB，最快（推荐快速体验）
  [2] MiniLM    - 34MB，效果最好（推荐）
  [3] MultiBERT - 150MB，多语言

请选择 [1-3，默认2]: 2

✓ 配置完成，正在下载模型（首次使用需要）...
```

---

## 六、数据库配置建议

### 6.1 向量数据库选择

| 模式 | 适用场景 | 配置示例 | 推荐度 |
|------|---------|---------|--------|
| **Chroma本地持久化** | 单用户，长期存储 | `persist_dir: ./data/chroma` | ⭐⭐⭐⭐⭐ 默认 |
| Chroma内存模式 | 临时测试，CI/CD | `:memory:` 或无persist_dir | ⭐⭐⭐ 测试用 |
| Chroma远程 | 团队协作 | 配置host/port | ⭐⭐⭐ 多用户 |
| Qdrant本地 | 大数据量，高性能 | `mode: local, path: ./data/qdrant` | ⭐⭐⭐⭐ 进阶 |
| Qdrant远程 | 企业级部署 | `mode: remote, host: x.x.x.x` | ⭐⭐⭐ 企业 |

### 6.2 默认配置建议

**强烈推荐**：使用Chroma本地持久化作为默认配置

```yaml
# config.yaml 推荐默认配置
vectorstore:
  default: chroma-local
  instances:
    # 默认：本地持久化（数据不丢失，零配置）
    - name: chroma-local
      type: chroma
      persist_dir: ./data/chroma
      embedding_function: default
    
    # 可选：内存模式（仅供测试）
    - name: chroma-memory
      type: chroma
      # persist_dir为null即为内存模式
    
    # Phase 2+：Qdrant高性能选项（可选）
    - name: qdrant-local
      type: qdrant
      mode: local
      path: ./data/qdrant
      embedding_dimension: 1024
```

**推荐理由**:
1. **零配置启动**: 无需外部依赖，用户体验最佳
2. **数据安全**: 本地持久化，数据不会丢失
3. **灵活迁移**: 支持迁移到Qdrant（已实现迁移工具）
4. **性能足够**: 单用户场景下性能完全满足需求

### 6.3 数据目录结构

```
data/
├── chroma/              # Chroma向量数据库
│   ├── chroma.sqlite3
│   └── ...
├── qdrant/              # Qdrant存储（如启用）
│   └── storage/
├── bm25/                # BM25索引（混合搜索）
├── flashrank_cache/     # Rerank模型缓存
│   └── ms-marco-TinyBERT-L-2-v2/
└── logs/                # 日志文件
    └── app.log
```

---

## 七、MCP配置导出

### 7.1 支持的IDE

| IDE | 配置文件位置 | 自动生成 |
|-----|-------------|---------|
| Claude Desktop | `~/claude_desktop_config.json` | ✅ |
| Cursor | `~/.cursor/mcp.json` | ✅ |
| Windsurf | `~/.codeium/windsurf/mcp_config.json` | ✅ |
| VS Code + Copilot | `.vscode/settings.json` | ✅ |
| Opencode | 内置配置 | ✅ |
| Zed | `~/.config/zed/` | 需手动 |

### 7.2 自动生成配置

**执行命令**:
```bash
# 生成MCP配置
python scripts/config/generate-mcp-config.py --ide claude_desktop

# 或交互式
python scripts/config/generate-mcp-config.py
# 提示: 请选择您的IDE [1-Claude, 2-Cursor, 3-Windsurf, ...]: 
```

**生成的配置示例（Claude Desktop）**:

```json
{
  "mcpServers": {
    "raghub": {
      "command": "python",
      "args": [
        "-m",
        "src.mcp_server.server",
        "--config",
        "/path/to/RagHubMCP/backend/config.yaml"
      ],
      "env": {
        "PYTHONPATH": "/path/to/RagHubMCP/backend"
      }
    }
  }
}
```

**生成的配置示例（Docker模式）**:

```json
{
  "mcpServers": {
    "raghub": {
      "command": "docker",
      "args": [
        "exec",
        "-i",
        "raghub-backend",
        "python",
        "-m",
        "src.mcp_server.server"
      ]
    }
  }
}
```

### 7.3 前端界面导出

Web控制台提供可视化配置导出：

```
Settings页面 → MCP配置 → 选择IDE → 复制/下载配置
```

---

## 八、常见问题

### 8.1 环境相关问题

**Q1: 没有Python环境怎么办？**
```bash
# 方案A: 使用Docker部署（无需Python）
docker-compose up -d

# 方案B: 安装Python（脚本自动指导）
# Windows: 从python.org下载安装
# Mac: brew install python@3.11
# Linux: sudo apt install python3.11
```

**Q2: 没有Node环境怎么办？**
```bash
# 方案A: Docker部署
# 方案B: 仅使用后端（前端功能受限）
# 方案C: 安装Node
# Windows: 从nodejs.org下载
# Mac: brew install node
# Linux: sudo apt install nodejs
```

**Q3: 端口被占用怎么办？**
```bash
# 检查占用
lsof -i :8818  # Mac/Linux
netstat -ano | findstr :8818  # Windows

# 修改端口
# 编辑 ~/.config/RagHubMCP/config.json
{
  "ports": {
    "backend": 8819,
    "frontend": 3316
  }
}
```

### 8.2 模型相关问题

**Q4: Ollama安装失败？**
```bash
# 方案A: 使用官方脚本
curl -fsSL https://ollama.com/install.sh | sh

# 方案B: 使用云端API
# 部署脚本会提示配置OpenAI API Key

# 方案C: 跳过模型配置，稍后手动配置
```

**Q5: 模型下载慢/失败？**
```bash
# 使用镜像源（中国用户）
export OLLAMA_HOST=0.0.0.0
ollama pull bge-m3 --insecure

# 或使用代理
export HTTPS_PROXY=http://proxy:port
ollama pull bge-m3
```

### 8.3 部署相关问题

**Q6: Docker部署后无法访问？**
```bash
# 检查容器状态
docker-compose ps

# 查看日志
docker-compose logs -f backend

# 常见问题：
# 1. 端口冲突 - 修改docker-compose.yml端口映射
# 2. 内存不足 - 使用轻量级模型配置
# 3. 权限问题 - Linux/Mac需要sudo
```

**Q7: MCP工具无法连接？**
```bash
# 检查服务是否运行
curl http://localhost:8818/api/config

# 检查MCP配置路径是否正确
# 确保config.yaml路径是绝对路径

# 查看MCP日志
# Claude Desktop: ~/Library/Logs/Claude/
```

---

## 九、AI自主部署指南

### 9.1 AI Agent部署指令模板

**用户发送给AI的指令**:

```markdown
请帮我部署RagHubMCP代码RAG系统。

请严格按照以下步骤执行：

## 步骤1: 环境诊断
- 检查Python版本 >= 3.11
- 检查Node.js版本 >= 18
- 检查Docker是否可用
- 检查Ollama是否已安装
- 向我报告环境检查结果

## 步骤2: 代码获取
- 从 https://github.com/user/RagHubMCP 克隆代码
- 进入项目目录

## 步骤3: 部署方式选择
- 根据环境自动推荐最佳部署方式
- 向我说明推荐理由并确认

## 步骤4: 执行部署
- Docker可用 → docker-compose up -d
- 否则 → python scripts/install.py

## 步骤5: 模型配置
- 如果Ollama未安装，询问我：
  A) 帮我安装Ollama
  B) 使用云端API（OpenAI）
  C) 跳过，稍后手动配置
- 如果已安装，检测可用模型并配置

## 步骤6: MCP配置
- 询问我使用的IDE（Claude Desktop/Cursor/Windsurf/其他）
- 生成对应的MCP配置文件
- 提供配置文件的完整内容，我可以复制粘贴

## 步骤7: 验证测试
- 测试后端API是否可访问
- 测试MCP工具列表
- 测试搜索功能
- 向我报告验证结果

请在每一步完成后向我报告进度，遇到问题时提供解决方案。
```

### 9.2 AI执行检查清单

AI Agent执行部署时的自检清单：

```markdown
## 部署前检查
- [ ] Python版本 >= 3.11 ✓
- [ ] Node.js版本 >= 18 ✓
- [ ] Git已安装 ✓
- [ ] 可用磁盘空间 > 2GB ✓

## 部署中检查
- [ ] 成功克隆代码仓库 ✓
- [ ] 后端依赖安装成功 ✓
- [ ] 前端依赖安装成功 ✓
- [ ] 数据库初始化成功 ✓
- [ ] 模型配置完成 ✓

## 部署后检查
- [ ] 后端服务可访问 http://localhost:8818 ✓
- [ ] 前端服务可访问 http://localhost:3315 ✓
- [ ] MCP工具列表正常 ✓
- [ ] 搜索功能测试通过 ✓

## 用户确认
- [ ] 用户确认MCP配置已粘贴到IDE ✓
- [ ] 用户确认可以从IDE调用RagHub工具 ✓
```

### 9.3 常见错误自动修复

AI应自动处理以下常见错误：

| 错误场景 | 自动修复策略 |
|---------|-------------|
| 端口被占用 | 自动检测并建议修改端口 |
| 模型下载失败 | 提供镜像源或切换轻量级模型 |
| 内存不足 | 建议使用TinyBERT等轻量模型 |
| 权限不足 | 提示使用sudo或修改目录权限 |
| 网络超时 | 建议检查代理设置或重试 |
| 依赖冲突 | 自动创建干净虚拟环境 |

---

## 附录

### A. 文件清单

```
scripts/
├── config/                       # 配置管理
│   ├── init-config.py            # 初始化配置文件
│   └── generate-mcp-config.py    # MCP配置生成
├── check/                        # 环境检查
│   └── check-env.py              # 环境检查脚本
├── setup/                        # 组件安装
│   ├── setup-ollama.py           # Ollama安装
│   ├── setup-qdrant.py           # Qdrant安装
│   └── setup-chroma.py           # Chroma安装
├── install/                      # 安装脚本
│   ├── install.py                # 一键安装主脚本
│   └── install-wizard.py         # 交互向导（可选）
├── docker/                       # Docker部署配置
│   ├── Dockerfile.backend        # 后端镜像
│   ├── Dockerfile.frontend       # 前端镜像
│   ├── docker-compose.yml        # 完整编排
│   ├── docker-compose.dev.yml    # 开发模式
│   └── README.md                 # Docker部署说明
├── lib/                          # 公共库
│   └── config.py                 # 配置读取工具
└── README.md                     # 脚本使用说明
```

| 文件路径 | 用途 | 可独立运行 |
|---------|------|-----------|
| `scripts/config/init-config.py` | 初始化配置 | ✅ |
| `scripts/check/check-env.py` | 环境检查 | ✅ |
| `scripts/setup/setup-ollama.py` | Ollama安装 | ✅ |
| `scripts/setup/setup-qdrant.py` | Qdrant安装 | ✅ |
| `scripts/setup/setup-chroma.py` | Chroma安装 | ✅ |
| `scripts/config/generate-mcp-config.py` | MCP配置生成 | ✅ |
| `scripts/install/install.py` | 一键安装 | 集成 |
| `scripts/docker/docker-compose.yml` | Docker编排 | Docker |

### B. 快速参考命令

```bash
# 初始化配置（首次运行）
python scripts/config/init-config.py

# 环境检查
python scripts/check/check-env.py

# Docker部署（推荐）
docker-compose up -d

# 一键脚本部署
python scripts/install/install.py

# 安装组件（独立）
python scripts/setup/setup-ollama.py
python scripts/setup/setup-qdrant.py
python scripts/setup/setup-chroma.py

# 生成MCP配置
python scripts/config/generate-mcp-config.py --ide claude_desktop

# 手动后端启动
cd backend && python -m venv venv && source venv/bin/activate && pip install -e . && python -m src.main

# 手动前端启动
cd frontend && npm install && npm run dev
```

### C. 配置文件说明

**配置文件位置**:
- Windows: `%USERPROFILE%\.config\RagHubMCP\config.json`
- macOS/Linux: `~/.config/RagHubMCP/config.json`

**配置文件结构**:
```json
{
  "$schema": "https://raw.githubusercontent.com/user/RagHubMCP/main/schemas/config.schema.json",
  "version": "1.0",
  "paths": {
    "install_dir": "~/RagHubMCP",
    "data_dir": "~/RagHubMCP/data",
    "logs_dir": "~/RagHubMCP/logs",
    "docker_data_dir": "~/RagHubMCP/docker-data"
  },
  "ports": {
    "backend": 8818,
    "frontend": 3315,
    "ollama": 11434,
    "qdrant": 6333
  },
  "database": {
    "type": "chroma",
    "persist_dir": "~/RagHubMCP/data/chroma"
  },
  "models": {
    "mode": "ollama",
    "embedding_model": "bge-m3",
    "rerank_model": "ms-marco-TinyBERT-L-2-v2"
  }
}
```

### C. 版本更新记录

| 版本 | 日期 | 变更内容 |
|------|------|---------|
| v1.0 | 2026-03-20 | 初始版本，四层部署架构 |

---

*本文档由 RagHubMCP 团队编写  
*问题反馈: https://github.com/user/RagHubMCP/issues
