# RagHubMCP 执行准则

**版本**: v2.0  
**生效日期**: 2026-03-20

## 一 核心原则

1. **测试优先**: 每个任务开始前先编写测试用例，测试通过方可验收
2. **最佳实践**: 所有代码参考 context7 文档，实现最佳实践标准
3. **记录追踪**: 每个任务完成必须更新 TODO.md 和 CHANGELOG.md
4. **善加利用**: 现有的 MCP 功能，包括 context7 的代码参考，chroma 的库检索和增加索引

---

## 二 V2 架构新增开发原则

### ✅ 必须遵守

1. [RULE-1] Pipeline 是唯一执行入口
  - 所有 RAG 流程必须通过 pipeline.run() 调用
  - MCP/REST 只调用 Pipeline，不直接调用底层模块

2. [RULE-2] 所有模块必须接口化
  - 每个模块必须定义抽象基类（ABC）
  - 具体实现通过工厂创建

3. [RULE-3] 禁止在模块中直接依赖具体实现
  - ❌ from chroma_service import ...
  - ✅ vector_db.search(...)  # 通过接口

4. [RULE-4] 所有能力必须可配置
  - 模型、数据库、策略全部配置驱动
  - 配置变更无需改代码

5. [RULE-5] 所有策略必须可评估
  - Profile 切换 → 结果对比
  - Rerank 前后 → 命中率对比

### ❌ 禁止事项

1. [FORBID-1] 重写全部代码 → 渐进式重构，每步可验证
2. [FORBID-2] 引入复杂 DAG → Pipeline 保持线性流程
3. [FORBID-3] 增加过多配置项 → 用户只需选择 Profile
4. [FORBID-4] 跳过验证 → V2 命中率必须 ≥ V1 + 20%
5. [FORBID-5] 直接依赖具体 LLM 实现 → 必须通过 Provider 接口


## 三 Git 原则

- 1. 没有得到允许不得读取备份
- 2. 没有的到允许不得创建分支
- 3. 没有得到允许不得切换分支

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
feat(v2): implement DefaultPipeline

- Add RAGPipeline abstract base class
- Integrate HybridSearchService as default retriever

Closes #V2.1
```

### 分支策略

- `main`: 主分支，稳定版本
- `develop`: 开发分支
- `feature/*`: 功能分支
- `fix/*`: 修复分支

---

## 四 任务执行流程

### 开始任务前

1. 确认当前时间和任务编号
2. 从 TODO.md 获取测试用例
3. 创建测试文件（测试优先）

### 任务进行中

1. 参考文档确保最佳实践
2. 编写代码实现
3. 运行测试验证

### 任务完成后

1. 确保所有测试通过
2. 更新 TODO.md（标记完成）
3. 更新 CHANGELOG.md（时间 + 简要概括）
4. Git 提交变更

---

## 五 时间记录规范

- **格式**: `YYYY-MM-DD HH:mm`
- **示例**: `2026-03-19 09:08`
- **来源**: 必须查询系统时间，禁止手动输入

**查询命令**:
```bash
# Windows
powershell -Command "Get-Date -Format 'yyyy-MM-dd HH:mm'"

# Linux/Mac
date '+%Y-%m-%d %H:%M'
```

---

## 六 CHANGELOG 规范
- 1. 所有项目变动，以概括形式记录于根目录下CHANGLOG.md
- 2. 必须有时间戳（符合第五条约定）
- 3. 新纪录必须写在最上方
- 4. 规范格式
```markdown
## [版本号] - YYYY-MM-DD
### 任务编号: 任务名称（假设来源于TODO）
- **时间**: YYYY-MM-DD HH:mm
- **内容**: 一句话简要概括
```

---

## 七 测试验收标准

### 1 验收流程

1. 逐项执行测试用例
2. 记录测试结果
3. 所有用例通过方可进入下一任务
4. 任一失败则修复后重新测试

### 2 V2 最终验收

- 1. MCP 调用只需一个 query
- 2. 结果明显优于 V1（命中率 +20%）
- 3. 可切换模型/数据库
- 4. 代码结构清晰（Pipeline 中心）

---

## 八 代码规范

### 1 Python

- 遵循 PEP 8
- 使用 Type Hints
- 文档字符串使用 Google 风格
- 最大行宽 100 字符

### 2 TypeScript/Vue

- 遵循 Vue 3 Composition API 风格
- 使用 TypeScript 严格模式
- 组件命名使用 PascalCase

---

## 九 Shell 命令规范

### 重定向注意事项

**问题**: Git Bash 环境下，Windows 的 `nul` 设备名会被当作普通文件名处理。

### 正确写法

```bash
# ❌ 错误 (Git Bash 会创建 nul 文件)
mkdir -p some/path 2>nul

# ✅ 正确: 使用 /dev/null (跨平台通用)
mkdir -p some/path 2>/dev/null

# ✅ 正确: 不使用重定向
mkdir -p some/path || true
```

### 规则

1. **统一使用 `/dev/null`**: 所有 shell 命令中需要丢弃输出时，使用 `/dev/null`
2. **避免 `nul` 关键字**: 不要在 bash 命令中使用 `nul` 作为重定向目标
3. **跨平台兼容**: 优先使用 `|| true` 或条件判断代替重定向

---

##  十 V2 MCP 接口收敛

### ✅ 保留

| 工具 | 用途 |
|------|------|
| `query` | 统一检索入口 |
| `ingest` | 统一索引入口 |

### ❌ 删除（deprecated）

| 工具 | 替代 |
|------|------|
| `search` | `query` |
| `rerank` | 内置于 Pipeline |
| `embed` | 内部调用 |

---

## 十一 参考资源

| 资源 | 用途 |
|------|------|
| MCP 协议规范 | 协议实现参考 |
| chroma-mcp 源码 | MCP 实现参考 |
| FlashRank 文档 | Rerank 集成 |
| Context7 | 最佳实践参考 |

---

*最后更新: 2026-03-20*