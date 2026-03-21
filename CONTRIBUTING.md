# Contributing to RagHubMCP

感谢你对 RagHubMCP 的兴趣！欢迎贡献代码、报告问题或提出建议。

## 开发环境设置

### 前置要求

- Python 3.11+
- Node.js 18+
- Git

### 本地开发

```bash
# 1. 克隆仓库
git clone https://github.com/your-repo/RagHubMCP.git
cd RagHubMCP

# 2. 后端设置
cd backend
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
pip install -e ".[dev]"

# 3. 前端设置
cd ../frontend
npm install

# 4. 启动开发服务器
# 后端
cd backend
python -m src.main

# 前端 (新终端)
cd frontend
npm run dev
```

## 代码规范

### Python

- 遵循 [PEP 8](https://www.pep8.org/)
- 使用 `ruff` 进行代码检查和格式化
- 运行 `ruff check .` 和 `ruff format .` 确保代码符合规范

### 前端

- 使用 TypeScript
- 遵循 Vue 3 组合式 API 风格
- 运行 `npm run lint` 检查代码

## 提交 PR

1. Fork 本仓库
2. 创建特性分支: `git checkout -b feature/your-feature`
3. 提交更改: `git commit -m 'Add some feature'`
4. 推送分支: `git push origin feature/your-feature`
5. 创建 Pull Request

## 测试

```bash
# 后端测试
cd backend
pytest tests/ -v

# 前端测试
cd frontend
npm run test
```

## 问题反馈

请通过 GitHub Issues 报告问题，包含：
- 清晰的描述
- 复现步骤
- 期望行为 vs 实际行为
- 环境信息

## 许可证

通过贡献代码，你同意将你的贡献 MIT 许可证下发布。