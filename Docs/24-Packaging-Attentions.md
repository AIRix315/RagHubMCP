# RagHubMCP 打包注意事项文档

> 版本: 2.6.2  
> 创建日期: 2026-03-23  
> 最后更新: 2026-03-23

---

## 目录

1. [概述](#概述)
2. [打包架构](#打包架构)
3. [环境要求](#环境要求)
4. [完整打包流程](#完整打包流程)
5. [多平台打包](#多平台打包)
6. [版本号管理](#版本号管理)
7. [Python 虚拟环境注意事项](#python-虚拟环境注意事项)
8. [PyInstaller 打包（可选）](#pyinstaller-打包可选)
9. [测试清单](#测试清单)
10. [常见问题与解决方案](#常见问题与解决方案)
11. [发布检查清单](#发布检查清单)

---

## 概述

RagHubMCP 采用 **Go Wrapper + Python Backend** 的混合打包架构：

```
RHM.exe (Go 包装器)
├── Go HTTP Proxy (端口 3315)
│   ├── /api/*    → REST API (端口 8818)
│   ├── /mcp/*    → MCP HTTP (端口 8819)
│   ├── /docs/*   → REST API 文档
│   ├── /ws/*     → WebSocket 代理
│   └── /*        → 前端静态文件
├── Python REST API (端口 8818)
├── Python MCP HTTP (端口 8819)
└── System Tray (系统托盘)
    ├── Open Browser
    ├── About
    └── Quit → 清理所有进程后退出
```

### 打包模式

| 模式 | 说明 | 文件大小 | Python 依赖 |
|------|------|---------|------------|
| **Go Wrapper Only** | Go 包装器 + 系统 Python | ~10MB | 需要安装 |
| **Full Bundle** | Go + PyInstaller 嵌入 Python | ~150-300MB | 不需要 |

当前默认使用 **Go Wrapper Only** 模式。

---

## 打包架构

### 目录结构

```
RagHubMCP/
├── version.txt              # 版本号文件
├── frontend/                # Vue 前端
│   ├── src/
│   ├── dist/               # 构建产物
│   └── package.json
├── backend/                 # Python 后端
│   ├── src/
│   ├── config.yaml
│   └── pyproject.toml
├── pack/
│   ├── build.bat           # Windows 打包脚本
│   ├── build.sh            # Linux/macOS 打包脚本
│   ├── go/                 # Go 包装器源码
│   │   ├── main.go
│   │   ├── process.go
│   │   ├── tray.go
│   │   ├── proxy.go
│   │   ├── embed.go
│   │   ├── icons/          # 托盘图标
│   │   └── go.mod
│   └── python/             # PyInstaller 配置（可选）
│       └── RHM.spec
└── dist/
    └── RHM.exe             # 最终产物
```

### Go Wrapper 职责

| 文件 | 功能 |
|------|------|
| `main.go` | 入口点、参数解析、服务编排 |
| `process.go` | 启动/停止 Python 子进程、隐藏控制台窗口 |
| `tray.go` | 系统托盘图标和菜单、退出时清理进程 |
| `proxy.go` | HTTP 反向代理、静态文件服务 |
| `embed.go` | 嵌入前端和后端资源 |
| `browser.go` | 跨平台打开浏览器 |
| `platform.go` | 平台兼容性（路径、浏览器等） |

---

## 环境要求

### Windows 打包

| 工具 | 版本要求 | 用途 |
|------|---------|------|
| Go | 1.21+ | 编译 Go wrapper |
| Node.js | 18+ | 构建前端 |
| Python | 3.11+ | 运行后端（可选 PyInstaller） |
| PyInstaller | 6.x | 嵌入 Python（可选） |

### Linux/macOS 打包

| 工具 | 版本要求 |
|------|---------|
| Go | 1.21+ |
| Node.js | 18+ |
| Python3 | 3.11+ |

### 验证环境

```bash
# Windows
go version
node --version
python --version

# Linux/macOS
go version
node --version
python3 --version
```

---

## 完整打包流程

### 步骤 1: 前端构建

```bash
cd frontend

# 安装依赖（首次）
npm install

# 构建生产版本
npm run build
```

**产物**: `frontend/dist/`

**重要检查项**:
- [ ] `dist/index.html` 包含主题初始化脚本
- [ ] `dist/index.html` 默认语言为 `en-US`
- [ ] 无 TypeScript 编译错误
- [ ] 无 ESLint 警告

**主题初始化脚本确认**:
```html
<script>
  (function() {
    const savedTheme = localStorage.getItem('theme');
    const savedLocale = localStorage.getItem('locale');
    if (savedTheme === 'dark' || (!savedTheme && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
    const locale = savedLocale || 'en-US';
    document.documentElement.setAttribute('lang', locale);
  })();
</script>
```

### 步骤 2: 后端准备

```bash
cd backend

# 创建虚拟环境（推荐）
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# 安装依赖
pip install -e ".[dev]"
```

**重要**: 打包时应使用虚拟环境中的 Python！

### 步骤 3: 准备嵌入资源

```bash
cd pack/go

# 创建目录结构
mkdir -p frontend/dist
mkdir -p backend/src
mkdir -p data

# 复制前端
cp -r ../../frontend/dist/* frontend/dist/

# 复制后端
cp -r ../../backend/src/* backend/src/
cp ../../backend/config.yaml backend/
cp ../../backend/pyproject.toml backend/

# 准备数据目录
mkdir -p data/flashrank_cache
mkdir -p data/chroma
```

### 步骤 4: 编译 Go Wrapper

#### Windows（带版本号）

```batch
cd pack/go

# 读取版本号
set VERSION=2.6.2

# 设置链接器参数
set LDFLAGS=-s -w -H windowsgui -X main.version=%VERSION% -X "main.buildTime=2026-03-23"

# 编译
go build -ldflags="%LDFLAGS%" -o ../../dist/RHM-%VERSION%.exe .
```

**参数说明**:
- `-s -w`: 去除调试信息，减小体积
- `-H windowsgui`: GUI 模式，隐藏控制台窗口
- `-X main.version=%VERSION%`: 注入版本号
- `-X main.buildTime`: 注入构建时间

#### Linux/macOS

```bash
cd pack/go

VERSION=$(cat ../../version.txt)
BUILD_TIME=$(date '+%Y-%m-%d')
LDFLAGS="-s -w -X main.version=$VERSION -X main.buildTime=$BUILD_TIME"

# Linux
go build -ldflags="$LDFLAGS" -o ../../dist/RHM-$VERSION-linux .

# macOS
GOOS=darwin GOARCH=amd64 go build -ldflags="$LDFLAGS" -o ../../dist/RHM-$VERSION-macos-amd64 .
GOOS=darwin GOARCH=arm64 go build -ldflags="$LDFLAGS" -o ../../dist/RHM-$VERSION-macos-arm64 .
```

### 步骤 5: 验证构建产物

```bash
# 检查版本
./dist/RHM-2.6.2.exe --version
# 输出: RagHubMCP Distributor v2.6.2 (built 2026-03-23)

# 检查平台
file dist/RHM-2.6.2.exe
# 输出: PE32+ executable for MS Windows (GUI), x86-64

# 检查大小
ls -lh dist/RHM-2.6.2.exe
# 输出: ~10MB (Go wrapper only)
```

---

## 多平台打包

### Windows (x64)

```batch
cd pack
build.bat
```

产物: `dist/RHM-{version}.exe`

### Linux (x64)

```bash
cd pack
chmod +x build.sh
./build.sh
```

产物: `dist/RHM-{version}-linux`

### macOS (Intel & Apple Silicon)

```bash
# Intel Mac
GOOS=darwin GOARCH=amd64 go build -ldflags="$LDFLAGS" -o dist/RHM-{version}-macos-amd64 .

# Apple Silicon
GOOS=darwin GOARCH=arm64 go build -ldflags="$LDFLAGS" -o dist/RHM-{version}-macos-arm64 .
```

### 交叉编译矩阵

| 平台 | GOOS | GOARCH | 输出文件 |
|------|------|--------|----------|
| Windows x64 | windows | amd64 | RHM-{version}.exe |
| Linux x64 | linux | amd64 | RHM-{version}-linux |
| macOS Intel | darwin | amd64 | RHM-{version}-macos-amd64 |
| macOS ARM | darwin | arm64 | RHM-{version}-macos-arm64 |

### 平台特定注意事项

#### Windows
- 必须使用 `-H windowsgui` 隐藏控制台窗口
- Python 子进程需要 `SysProcAttr{HideWindow: true}` 隐藏窗口
- 托盘图标使用 `.ico` 格式

#### macOS
- 托盘图标使用 `.png` 格式（64x64 推荐 Retina）
- 需要签名和公证才能分发
- 后缀为 `.app` 的应用包

#### Linux
- 托盘图标使用 `.png` 格式（32x32）
- 依赖 `libayatana-appindicator3` 或 `libappindicator3` 显示系统托盘
- AppImage 格式便于分发

---

## 版本号管理

### 版本文件

`version.txt` 文件存储版本号：

```
2.6.2
```

### 版本号格式

```
MAJOR.MINOR.PATCH

MAJOR: 重大架构变更
MINOR: 新功能、功能增强
PATCH: Bug 修复、小改进
```

### 构建时注入版本号

**build.bat (Windows)**:
```batch
for /f "tokens=*" %%i in (..\version.txt) do set VERSION=%%i
set BUILD_TIME=%datetime:~0,4%-%datetime:~4,2%-%datetime:~6,2%
go build -ldflags="-X main.version=%VERSION% -X main.buildTime=%BUILD_TIME%"
```

**build.sh (Linux/macOS)**:
```bash
VERSION=$(cat ../version.txt)
BUILD_TIME=$(date '+%Y-%m-%d')
go build -ldflags="-X main.version=$VERSION -X main.buildTime=$BUILD_TIME"
```

### 输出文件命名规范

```
RHM-{VERSION}-{PLATFORM}.{EXTENSION}

示例:
- RHM-2.6.2.exe        # Windows
- RHM-2.6.2-linux      # Linux
- RHM-2.6.2-macos.dmg  # macOS
```

---

## Python 虚拟环境注意事项

### 重要规则

1. **打包时必须使用虚拟环境中的 Python**
2. **PyInstaller 必须在虚拟环境中运行**
3. **依赖版本必须锁定**

### 创建虚拟环境

```bash
cd backend

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# 安装依赖
pip install -e ".[dev]"
pip install pyinstaller
```

### PyInstaller 使用虚拟环境

```bash
# 确保虚拟环境已激活
which python  # Linux/macOS
where python  # Windows

# 应该显示 venv 目录下的 Python

# 运行 PyInstaller
python -m PyInstaller RHM.spec --clean
```

### 依赖锁定

使用 `requirements.txt` 或 `pyproject.toml` 锁定版本：

```toml
# pyproject.toml
[project]
dependencies = [
    "fastapi>=0.109.0,<0.110.0",
    "uvicorn>=0.27.0,<0.28.0",
    # ...
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pyinstaller>=6.0.0",
]
```

---

## PyInstaller 打包（可选）

### 为什么是可选的？

当前架构：**Go Wrapper + 系统 Python**

- Go wrapper 作为进程管理器启动 Python
- Python 后端代码以源码形式嵌入 Go 二进制
- 运行时需要系统安装 Python

如果需要**完全独立分发**，可以启用 PyInstaller 打包。

### 启用 PyInstaller 打包

#### 1. 修改 build.bat

取消注释 Step 5:

```batch
echo ================================================
echo   Step 5: Building Python Package
echo ================================================
echo.

cd python
%PYTHON_CMD% -m PyInstaller RHM.spec --clean
cd ..
```

#### 2. 更新 RHM.spec

当前配置会生成 `RHM-python.exe`，需要整合到 Go wrapper：

```python
# pack/python/RHM.spec

# 输出文件名
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="RHM-python",  # Python 后端可执行文件
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,  # 保持控制台以便调试
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
```

#### 3. 修改 Go wrapper 调用 PyInstaller 产物

```go
// process.go - getPythonExecutable()
func getPythonExecutable() string {
    // 优先使用嵌入的 Python 可执行文件
    embeddedPython := getEmbeddedPythonPath()
    if _, err := os.Stat(embeddedPython); err == nil {
        return embeddedPython
    }
    
    // 回退到系统 Python
    // ...
}
```

### PyInstaller 打包检查项

- [ ] 虚拟环境已激活
- [ ] 所有依赖已安装
- [ ] `hiddenimports` 包含所有动态导入的模块
- [ ] `datas` 包含非 Python 文件（config.yaml 等）
- [ ] 测试独立运行（无源码目录）

### 预期文件大小

| 模式 | 大小 |
|------|------|
| Go Wrapper Only | ~10MB |
| Go + PyInstaller | ~150-300MB |
| 完整离线包（含模型）| ~500MB+ |

---

## 测试清单

### 构建前测试

```bash
# 前端测试
cd frontend
npm run type-check
npm run lint
npm run test

# 后端测试
cd backend
pytest tests/ -v

# Go 测试
cd pack/go
go test ./... -v
```

### 构建后测试

#### 基本功能测试

```bash
# 1. 版本检查
./RHM-2.6.2.exe --version

# 2. 帮助信息
./RHM-2.6.2.exe --help

# 3. 启动服务（无浏览器、无托盘）
./RHM-2.6.2.exe --no-browser --no-tray --debug

# 4. 检查端口
netstat -ano | grep -E ":(3315|8818|8819)"
```

#### 前端测试

```bash
# 检查首页
curl http://localhost:3315/

# 验证默认语言
curl http://localhost:3315/ | grep 'lang="en-US"'

# 验证主题脚本
curl http://localhost:3315/ | grep 'savedTheme'
```

#### API 测试

```bash
# REST API 健康检查
curl http://localhost:8818/health
# 预期: {"status":"healthy","service":"RagHubMCP"}

# Provider API
curl http://localhost:3315/api/providers
# 预期: JSON 响应，包含 embedding/rerank/llm/vectorstore
```

#### 进程测试

```powershell
# Windows PowerShell
Get-Process RHM*,python* | Select-Object Id, ProcessName, MainWindowTitle

# 验证:
# - MainWindowTitle 为空（隐藏控制台）
# - 进程 ID 正确显示
```

#### 托盘测试

1. 启动 RHM.exe（不带 --no-tray）
2. 检查系统托盘区域是否显示图标
3. 右键托盘图标 → 检查菜单项
4. 点击 "Open Browser" → 验证浏览器打开
5. 点击 "Quit" → 验证所有进程退出

```bash
# 退出后检查
netstat -ano | grep -E ":(3315|8818|8819)"
# 应该没有 LISTENING 状态
```

### 测试报告模板

```markdown
## 打包测试报告

**版本**: 2.6.2
**日期**: 2026-03-23
**平台**: Windows 10/11 x64

### 构建检查

| 项目 | 状态 | 备注 |
|------|------|------|
| 前端构建 | ✅ PASS | 无 TypeScript 错误 |
| Go 测试 | ✅ PASS | 所有测试通过 |
| 文件大小 | ✅ PASS | 9.6MB |
| PE 格式 | ✅ PASS | PE32+ GUI executable |

### 功能测试

| 功能 | 状态 | 备注 |
|------|------|------|
| 版本显示 | ✅ PASS | v2.6.2 |
| 服务启动 | ✅ PASS | 3315/8818/8819 |
| 前端访问 | ✅ PASS | 默认 en-US |
| REST API | ✅ PASS | /health 返回 healthy |
| 托盘图标 | ✅ PASS | 显示正常 |
| 进程隐藏 | ✅ PASS | 无控制台窗口 |
| 退出清理 | ✅ PASS | 所有进程退出 |

### 问题记录

无
```

---

## 常见问题与解决方案

### 1. 控制台窗口显示

**问题**: 运行时出现黑色控制台窗口

**原因**: Python 子进程默认创建控制台窗口

**解决**:

```go
// process.go - 添加 HideWindow
if runtime.GOOS == "windows" {
    cmd.SysProcAttr = &syscall.SysProcAttr{
        HideWindow: true,
    }
}
```

**构建参数**:
```bash
# Go 主程序也要隐藏
go build -ldflags="-H windowsgui"
```

### 2. 托盘图标不显示

**问题**: 系统托盘区域没有图标

**原因**:
1. 图标文件未正确嵌入
2. systray 库需要主线程运行

**解决**:

```go
// 确保图标嵌入
//go:embed icons/*.png icons/*.ico icon.png
var iconFS embed.FS

// 检查托盘启动日志
logrus.Info("System tray started")
```

### 3. 版本号未注入

**问题**: `--version` 显示 `dev` 或 `unknown`

**原因**: ldflags 参数格式错误

**正确格式**:
```bash
# Windows
go build -ldflags="-X main.version=2.6.2 -X main.buildTime=2026-03-23"

# Linux/macOS (带空格需要引号)
go build -ldflags="-X main.version=2.6.2 -X 'main.buildTime=2026-03-23'"
```

### 4. Python 进程未退出

**问题**: 关闭程序后 Python 进程仍在运行

**原因**: 托盘退出未调用清理函数

**解决**:

```go
// tray.go
func onExit() {
    logrus.Info("System tray exiting...")
    stopPythonProcesses()       // 停止 Python 进程
    cleanupTempResources()       // 清理临时文件
    logrus.Info("All services stopped, goodbye!")
}
```

### 5. 前端主题不生效

**问题**: 页面加载时主题闪烁或不正确

**原因**: 主题 class 未在 CSS 加载前设置

**解决**: 在 `index.html` 的 `<head>` 中添加初始化脚本：

```html
<head>
  <script>
    // 必须在 CSS 加载前执行
      const savedTheme = localStorage.getItem('theme');
      if (savedTheme === 'dark' || (!savedTheme && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
        document.documentElement.classList.add('dark');
      }
    })();
  </script>
  <!-- 然后加载 CSS -->
  <link rel="stylesheet" href="/assets/index.css">
</head>
```

### 6. 默认语言错误

**问题**: 页面默认显示中文

**解决**:

```typescript
// i18n/index.ts
const savedLocale = localStorage.getItem('locale') || 'en-US';  // 默认 en-US
```

```html
<!-- index.html -->
<html lang="en-US">  <!-- 默认 en-US -->
```

### 7. PyInstaller 打包失败

**问题**: `ModuleNotFoundError` 或 `ImportError`

**原因**: 隐藏导入未包含在 spec 文件

**解决**: 更新 `hiddenimports` 列表：

```python
# RHM.spec
hiddenimports = [
    "raghub_mcp.main",
    "raghub_mcp.api.router",
    # ... 添加所有模块
]
```

### 8. Linux 托盘不显示

**问题**: Linux 上系统托盘不工作

**原因**: 缺少 AppIndicator 依赖

**解决**:

```bash
# Ubuntu/Debian
sudo apt install libayatana-appindicator3-dev

# Fedora
sudo dnf install libappindicator-gtk3
```

---

## 发布检查清单

### 发布前检查

- [ ] 版本号已更新 (`version.txt`)
- [ ] CHANGELOG.md 已更新
- [ ] 所有测试通过
- [ ] 前端构建无错误
- [ ] Go 测试通过
- [ ] 主题初始化脚本存在
- [ ] 默认语言为 en-US

### 构建检查

- [ ] Windows x64 构建成功
- [ ] Linux x64 构建成功（可选）
- [ ] macOS 构建成功（可选）
- [ ] 文件大小合理
- [ ] 版本号正确注入

### 功能测试

- [ ] `--version` 显示正确版本
- [ ] `--help` 输出正确
- [ ] 启动服务正常
- [ ] 端口监听正常
- [ ] 前端页面可访问
- [ ] API 端点正常响应
- [ ] 托盘图标显示
- [ ] 托盘菜单功能正常
- [ ] 退出时全部进程终止
- [ ] 无控制台窗口显示

### 集成测试

- [ ] 浏览器自动打开（默认）
- [ ] `--no-browser` 禁止浏览器打开
- [ ] `--no-tray` 禁止托盘显示
- [ ] `--debug` 输出详细日志
- [ ] 多端口配置正常

### 文档检查

- [ ] README.md 已更新
- [ ] CHANGELOG.md 记录变更
- [ ] 本文档（24-Packaging-Attentions.md）已更新

---

## 附录

### A. 完整构建命令参考

#### Windows

```batch
cd RagHubMCP

:: 前端
cd frontend
call npm install
call npm run build
cd ..

:: 后端（可选 PyInstaller）
cd backend
python -m venv venv
call venv\Scripts\activate
pip install -e ".[dev]"
cd ..

:: Go wrapper
cd pack\go
go mod tidy
go build -ldflags="-s -w -H windowsgui -X main.version=2.6.2 -X main.buildTime=2026-03-23" -o ..\..\dist\RHM-2.6.2.exe .
```

#### Linux/macOS

```bash
cd RagHubMCP

# 前端
cd frontend && npm install && npm run build && cd ..

# Go wrapper
cd pack/go
go mod tidy
VERSION=2.6.2
BUILD_TIME=$(date '+%Y-%m-%d')
go build -ldflags="-s -w -X main.version=$VERSION -X main.buildTime=$BUILD_TIME" -o ../../dist/RHM-$VERSION-linux .
```

### B. 版本号历史

| 版本 | 日期 | 主要变更 |
|------|------|---------|
| 2.6.2 | 2026-03-23 | 修复托盘退出清理、隐藏 Python 控制台、默认英文 |
| 2.6.0 | 2026-03-22 | 新 UI 设计 |
| ... | ... | ... |

### C. 相关文档

- [Packaging Plan](./Ref/PACKAGING_PLAN.md)
- [Go Packaging README](../pack/go/README.md)
- [UI Plan](./23-UI-Plan.md)

---

**文档维护**: 如有新的打包问题或解决方案，请更新本文档。