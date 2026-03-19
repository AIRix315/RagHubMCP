# RagHubMCP 执行准则

**版本**: v1.0  
**生效日期**: 2026-03-19

---

## 核心原则

1. **测试优先**: 每个任务开始前先编写测试用例，测试通过方可验收
2. **最佳实践**: 所有代码参考 context7 文档，实现最佳实践标准
3. **记录追踪**: 每个任务完成必须更新 TODO.md 和 CHANGELOG.md
4. **善加利用**：现有的MCP功能，包括context7的代码参考，chroma的库检索和增加索引，必要时用MCP_everything查看已经被拉取到本地的GitHub仓库代码等

---

## Git 工作流

### 提交规范

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Type 类型**:
- `feat`: 新功能
- `fix`: Bug 修复
- `docs`: 文档更新
- `style`: 代码格式
- `refactor`: 重构
- `test`: 测试相关
- `chore`: 构建/工具

**示例**:
```
feat(mcp): implement chroma_query_with_rerank tool

- Add vector search + rerank combination
- Support n_results/rerank_top_k parameters
- Add metadata filtering

Closes #1
```

### 分支策略

- `main`: 主分支，稳定版本
- `develop`: 开发分支
- `feature/*`: 功能分支
- `fix/*`: 修复分支

---

## 任务执行流程

### 开始任务前

1. 确认当前时间和任务编号
2. 从 TODO.md 获取测试用例
3. 创建测试文件（测试优先）

### 任务进行中

1. 编写代码实现
2. 运行测试验证
3. 参考文档确保最佳实践

### 任务完成后

1. 确保所有测试通过
2. 更新 TODO.md（标记完成）
3. 更新 CHANGELOG.md（时间 + 简要概括）
4. Git 提交变更

---

## 时间记录规范

### 格式要求

- **格式**: `YYYY-MM-DD HH:mm`
- **示例**: `2026-03-19 09:08`
- **来源**: 必须查询系统时间，禁止手动输入

### 查询命令

```bash
# Windows
powershell -Command "Get-Date -Format 'yyyy-MM-dd HH:mm'"

# Linux/Mac
date '+%Y-%m-%d %H:%M'
```

---

## CHANGELOG 记录格式

```markdown
## [版本号] - YYYY-MM-DD

### 任务编号: 任务名称
- **时间**: YYYY-MM-DD HH:mm
- **状态**: 完成/进行中
- **内容**: 一句话简要概括
- **测试**: TC-x.x.x 通过

### 示例

## [0.1.0] - 2026-03-19

### 1.1: 项目初始化
- **时间**: 2026-03-19 09:08
- **状态**: 完成
- **内容**: 创建项目结构、Git仓库、配置文件
- **测试**: TC-1.1.1 ~ TC-1.1.4 通过
```

---

## 测试验收标准

### Phase 1 测试用例

| 编号 | 测试内容 | 通过标准 |
|------|---------|---------|
| TC-1.1.1 | 虚拟环境激活成功 | `venv\Scripts\activate` 无报错 |
| TC-1.1.2 | pip install 无报错 | 所有依赖安装成功 |
| TC-1.1.3 | 核心模块导入成功 | `import fastapi; import chromadb; import flashrank` 成功 |
| TC-1.1.4 | 配置文件加载成功 | config.yaml 正确解析 |

### 验收流程

1. 逐项执行测试用例
2. 记录测试结果
3. 所有用例通过方可进入下一任务
4. 任一失败则修复后重新测试

---

## 代码规范

### Python

- 遵循 PEP 8
- 使用 Type Hints
- 文档字符串使用 Google 风格
- 最大行宽 100 字符

### TypeScript/Vue

- 遵循 Vue 3 Composition API 风格
- 使用 TypeScript 严格模式
- 组件命名使用 PascalCase

---

## Shell 命令规范

### 重定向注意事项

**问题**: Git Bash 环境下，Windows 的 `nul` 设备名会被当作普通文件名处理，导致创建实际的 `nul` 文件。

| 环境 | `2>nul` 行为 | 结果 |
|------|-------------|------|
| Windows CMD | 重定向到空设备 | ✅ 正确 |
| Windows PowerShell | 重定向到空设备 | ✅ 正确 |
| **Git Bash** | 创建名为 `nul` 的实际文件 | ❌ 创建了文件 |

### 正确写法

```bash
# ❌ 错误 (Git Bash 会创建 nul 文件)
mkdir -p some/path 2>nul
command 2>nul

# ✅ 正确方式 1: 使用 /dev/null (Git Bash/WSL/Linux/Mac 通用)
mkdir -p some/path 2>/dev/null
command 2>/dev/null

# ✅ 正确方式 2: 不使用重定向，用 || true 或 || echo
mkdir -p some/path || true
command || echo "ignored error"

# ✅ 正确方式 3: 在 Windows PowerShell 中使用
mkdir some/path 2>$null
command 2>$null
```

### 规则

1. **统一使用 `/dev/null`**: 所有 shell 命令中需要丢弃输出时，使用 `/dev/null`
2. **避免 `nul` 关键字**: 不要在 bash 命令中使用 `nul` 作为重定向目标
3. **跨平台兼容**: 优先使用 `|| true` 或条件判断代替重定向

---

## 参考资源

| 资源 | 用途 |
|------|------|
| MCP 协议规范 | 协议实现参考 |
| chroma-mcp 源码 | MCP 实现参考 |
| FlashRank 文档 | Rerank 集成 |
| Context7 | 最佳实践参考 |

---

*最后更新: 2026-03-20 00:10*