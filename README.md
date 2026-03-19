# RagHubMCP

**通用代码 RAG 中枢** - MCP Server + FlashRank Rerank + 效果对比仪表盘

---

## 项目定位

**核心价值**: 效果对比仪表盘 - 让用户测试、调配、找到最优配置

**核心洞察**: 模型在迅速发展，用户希望得到更好的结果。本项目与其他竞品的区别在于：竞品提供便捷的封装方案，本项目的便捷之上，把封装全部打开，让用户自己去调配。

---

## 技术栈

| 层级 | 技术选型 |
|------|---------|
| 后端语言 | Python 3.11+ |
| 后端框架 | FastAPI |
| 协议层 | MCP |
| 向量数据库 | Chroma |
| Rerank | FlashRank |
| 前端框架 | Vue 3 + TypeScript |
| UI 组件 | shadcn-vue |

---

## 快速开始

### 环境要求

- Python 3.11+
- Node.js 18+
- Ollama (可选，用于本地模型)

### 后端启动

```bash
cd backend

# 创建虚拟环境
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# 安装依赖
pip install -e ".[dev]"

# 复制配置文件
copy .env.example .env

# 启动服务
python -m src.main
```

### 前端启动

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

---

## 项目结构

```
RagHubMCP/
├── backend/          # 后端服务
│   ├── src/          # 源代码
│   ├── tests/        # 测试
│   └── config.yaml   # 配置
├── frontend/         # Web 控制台
├── docker/           # Docker 配置
├── Docs/             # 文档
├── TODO.md           # 开发计划
├── CHANGELOG.md      # 更新日志
└── RULE.md           # 执行准则
```

详细结构见: [Docs/04-Project-Structure_20260319.md](Docs/04-Project-Structure_20260319.md)

---

## 文档

- [可行性分析](Docs/01-RagHubMCP_20260319.md)
- [技术选型](Docs/02-RagHubMCP-Tech_20260319.md)
- [MVP 范围](Docs/03-RagHubMCP-MVP_20260319.md)
- [开发计划](TODO.md)

---

## 开发状态

详见 [CHANGELOG.md](CHANGELOG.md)

---

## License

MIT