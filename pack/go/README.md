# RagHubMCP Go Packaging Readme

This directory contains the Go + Python hybrid packaging solution for RagHubMCP.

## Architecture

```
RHM.exe (Go wrapper)
├── Python REST API (port 8818)
├── Python MCP HTTP (port 8819)
├── Go HTTP Proxy (port 3315)
│   ├── /api/* → REST API
│   ├── /mcp/* → MCP HTTP
│   ├── /docs/* → REST API
│   ├── /ws/* → WebSocket proxy
│   └── /* → Frontend static files
└── System Tray
    ├── Open Browser
    ├── About
    └── Quit
```

## Files

| File | Purpose |
|------|---------|
| `main.go` | Main entry point, argument parsing, service orchestration |
| `platform.go` | Cross-platform compatibility (Windows/macOS/Linux) |
| `process.go` | Python process management (start/stop/monitor) |
| `proxy.go` | HTTP reverse proxy to Python services |
| `tray.go` | System tray icon and menu |
| `cli.go` | CLI command handling (index/search/serve) |
| `embed.go` | Resource embedding (frontend + backend) |
| `browser.go` | Cross-platform browser opening |
| `go.mod` | Go module definition |

## Build Requirements

### Go
- Go 1.21 or higher
- Dependencies:
  - `github.com/getlantern/systray` (system tray)
  - `github.com/sirupsen/logrus` (logging)

### Python
- Python 3.11 or higher
- PyInstaller 6.x
- Project dependencies (see `backend/pyproject.toml`)

### Node.js (for frontend)
- Node.js 18 or higher
- npm

## Build Instructions

### Windows

```cmd
cd pack
build.bat
```

Output: `dist/RHM.exe`

### Linux/macOS

```bash
cd pack
chmod +x build.sh
./build.sh
```

Output: `dist/RHM-linux` or `dist/RHM-macos`

## Usage

### Start Web Service (Default)

```bash
# Windows
RHM.exe

# Linux/macOS
./RHM-linux
```

### CLI Commands

```bash
# Show help
RHM.exe --help

# Show version
RHM.exe --version

# Start services with options
RHM.exe --port 3315 --rest-port 8818 --mcp-port 8819

# Headless mode (no browser, no tray)
RHM.exe --no-browser --no-tray

# Debug mode
RHM.exe --debug

# Index a directory
RHM.exe index /path/to/code

# Search
RHM.exe search "query"
```

## Development Mode

For development, you can run the Python services directly:

```bash
# REST API
cd backend
python -m src.main --port 8818

# MCP HTTP
python -m src.mcp_server.server --transport http --port 8819

# Frontend
cd frontend
npm run dev
```

## Distribution

The Go wrapper can be distributed as a single executable. Python dependencies
are either:
1. Embedded (larger file, standalone)
2. System Python (smaller file, requires Python installation)

Choose based on your distribution needs.