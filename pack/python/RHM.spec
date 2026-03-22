# RagHubMCP Python Packaging Configuration
# For PyInstaller - bundles Python backend into standalone executable

import sys
from pathlib import Path
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# Project root (relative to this spec file)
PROJECT_ROOT = Path(SPEC).parent.parent
BACKEND_DIR = PROJECT_ROOT / "backend"
FRONTEND_DIR = PROJECT_ROOT / "frontend"

# Data files to include
datas = []

# Backend source code
datas.append((str(BACKEND_DIR / "src"), "backend/src"))
datas.append((str(BACKEND_DIR / "config.yaml"), "backend"))

# Frontend is handled by Go wrapper, but we include it for completeness
if (FRONTEND_DIR / "dist").exists():
    datas.append((str(FRONTEND_DIR / "dist"), "frontend/dist"))

# Hidden imports (modules not detected automatically)
hiddenimports = [
    # FastAPI and dependencies
    "fastapi",
    "fastapi.middleware",
    "fastapi.middleware.cors",
    "uvicorn",
    "uvicorn.logging",
    "uvicorn.loops",
    "uvicorn.loops.auto",
    "uvicorn.protocols",
    "uvicorn.protocols.http",
    "uvicorn.protocols.http.auto",
    "uvicorn.protocols.websockets",
    "uvicorn.protocols.websockets.auto",
    "uvicorn.lifespan",
    "uvicorn.lifespan.on",
    
    # MCP
    "modelcontextprotocol",
    "mcp",
    "mcp.server",
    "mcp.server.fastmcp",
    
    # Vector databases
    "chromadb",
    "chromadb.api",
    "chromadb.config",
    "qdrant_client",
    "qdrant_client.http",
    
    # Embedding
    "ollama",
    "openai",
    "httpx",
    
    # Rerank
    "flashrank",
    
    # Tree-sitter for code parsing
    "tree_sitter",
    
    # BM25
    "bm25s",
    
    # YAML config
    "yaml",
    "pyyaml",
    
    # Async support
    "asyncio",
    "anyio",
    
    # Pydantic
    "pydantic",
    "pydantic_settings",
    
    # Watcher
    "watchdog",
    "watchdog.observers",
    "watchdog.events",
    
    # Network
    "networkx",
]

# Exclude modules (reduce size)
excludes = [
    # GUI frameworks (not needed)
    "PyQt5",
    "PyQt6",
    "PySide2",
    "PySide6",
    "tkinter",
    "matplotlib",
    
    # Testing (not needed in production)
    "pytest",
    "unittest",
    
    # Unused scientific libraries
    "scipy",
    "pandas",
    "numpy",
]

# Analysis configuration
a = Analysis(
    [str(BACKEND_DIR / "src" / "main.py")],
    pathex=[str(PROJECT_ROOT)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    noarchive=False,
)

# PYZ archive
pyz = PYZ(a.pure)

# EXE configuration
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="RHM-python",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,  # Compress with UPX if available
    console=True,  # Keep console for debugging
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

# Note: This creates RHM-python.exe which is then called by the Go wrapper
# The Go wrapper (RHM.exe) handles:
# - Process management
# - System tray
# - HTTP reverse proxy
# - Browser opening
# - Service orchestration