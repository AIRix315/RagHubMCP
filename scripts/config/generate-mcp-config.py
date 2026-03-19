#!/usr/bin/env python3
"""
RagHubMCP MCP 配置生成器

生成各 IDE 的 MCP 配置文件：
- Claude Desktop
- Cursor
- Windsurf
- VS Code
- OpenCode
- CherryStudio

支持两种模式：
- Docker 模式：通过 Docker 容器连接
- 原生模式：直接运行 Python 脚本

用法:
  python generate-mcp-config.py               # 交互式选择 IDE
  python generate-mcp-config.py --ide claude  # 指定 IDE
  python generate-mcp-config.py --print       # 打印到终端
  python generate-mcp-config.py --write       # 写入配置文件
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import sys
from pathlib import Path
from typing import Any, Optional

# 添加 lib 目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "lib"))

try:
    import lib.config as config_module
except ImportError:
    config_module = None


# MCP 配置模板
MCP_TEMPLATES = {
    "claude_desktop": {
        "name": "Claude Desktop",
        "config_path": {
            "Darwin": "~/Library/Application Support/Claude/claude_desktop_config.json",
            "Windows": "~/AppData/Roaming/Claude/claude_desktop_config.json",
            "Linux": "~/.config/Claude/claude_desktop_config.json",
        },
    },
    "cursor": {
        "name": "Cursor",
        "config_path": {
            "Darwin": "~/.cursor/mcp.json",
            "Windows": "~/.cursor/mcp.json",
            "Linux": "~/.cursor/mcp.json",
        },
    },
    "windsurf": {
        "name": "Windsurf",
        "config_path": {
            "Darwin": "~/.codeium/windsurf/mcp_config.json",
            "Windows": "~/.codeium/windsurf/mcp_config.json",
            "Linux": "~/.codeium/windsurf/mcp_config.json",
        },
    },
    "vscode": {
        "name": "VS Code + Copilot",
        "config_path": {
            "Darwin": ".vscode/settings.json",
            "Windows": ".vscode/settings.json",
            "Linux": ".vscode/settings.json",
        },
    },
    "opencode": {
        "name": "OpenCode",
        "config_path": None,  # 内置配置
    },
    "cherystudio": {
        "name": "CherryStudio",
        "config_path": {
            "Darwin": "~/.cherry-studio/mcp.json",
            "Windows": "~/.cherry-studio/mcp.json",
            "Linux": "~/.cherry-studio/mcp.json",
        },
    },
}


def get_project_root() -> Path:
    """获取项目根目录。"""
    # 尝试从配置文件获取
    if config_module:
        try:
            cfg = config_module.load_config()
            return Path(cfg.paths.install_dir).expanduser()
        except Exception:
            pass
    
    # 使用当前脚本的父目录的父目录
    return Path(__file__).parent.parent.parent.resolve()


def get_backend_path() -> Path:
    """获取后端路径。"""
    return get_project_root() / "backend"


def get_config_yaml_path() -> Path:
    """获取配置文件路径。"""
    return get_backend_path() / "config.yaml"


def generate_native_config() -> dict[str, Any]:
    """生成原生模式 MCP 配置。
    
    Returns:
        dict: MCP 配置字典
    """
    backend_path = get_backend_path()
    config_path = get_config_yaml_path()
    python_path = sys.executable
    
    return {
        "raghub": {
            "command": python_path,
            "args": [
                "-m",
                "src.mcp_server.server",
                "--config",
                str(config_path),
            ],
            "env": {
                "PYTHONPATH": str(backend_path),
            },
        }
    }


def generate_docker_config() -> dict[str, Any]:
    """生成 Docker 模式 MCP 配置。
    
    Returns:
        dict: MCP 配置字典
    """
    return {
        "raghub": {
            "command": "docker",
            "args": [
                "exec",
                "-i",
                "raghub-backend",
                "python",
                "-m",
                "src.mcp_server.server",
            ],
        }
    }


def get_config_path_for_ide(ide: str) -> Optional[Path]:
    """获取指定 IDE 的配置文件路径。
    
    Args:
        ide: IDE 标识符
        
    Returns:
        Path: 配置文件路径，如果不需要文件则返回 None
    """
    if ide not in MCP_TEMPLATES:
        return None
    
    template = MCP_TEMPLATES[ide]
    config_paths = template.get("config_path")
    
    if config_paths is None:
        return None
    
    system = platform.system()
    path_str = config_paths.get(system) or config_paths.get("Linux")
    
    if path_str:
        return Path(path_str).expanduser()
    
    return None


def format_output(ide: str, config: dict[str, Any]) -> str:
    """格式化输出配置。
    
    Args:
        ide: IDE 标识符
        config: 配置字典
        
    Returns:
        str: 格式化后的配置
    """
    if ide == "vscode":
        # VS Code 使用不同的格式
        return json.dumps({
            "mcp": {
                "servers": config
            }
        }, indent=2, ensure_ascii=False)
    
    return json.dumps({
        "mcpServers": config
    }, indent=2, ensure_ascii=False)


def print_config(ide: str, docker_mode: bool = False):
    """打印配置到终端。
    
    Args:
        ide: IDE 标识符
        docker_mode: 是否使用 Docker 模式
    """
    config = generate_docker_config() if docker_mode else generate_native_config()
    output = format_output(ide, config)
    
    print(f"\n{'=' * 60}")
    print(f" {MCP_TEMPLATES.get(ide, {}).get('name', ide)} MCP 配置")
    print(f" 模式: {'Docker' if docker_mode else '原生'}")
    print(f"{'=' * 60}\n")
    print(output)
    print(f"\n{'=' * 60}")
    
    # 显示配置文件路径
    config_path = get_config_path_for_ide(ide)
    if config_path:
        print(f" 配置文件路径: {config_path}")
    else:
        print(" 此 IDE 使用内置配置，无需手动配置文件")
    print(f"{'=' * 60}\n")


def write_config(ide: str, docker_mode: bool = False) -> bool:
    """写入配置文件。
    
    Args:
        ide: IDE 标识符
        docker_mode: 是否使用 Docker 模式
        
    Returns:
        bool: 是否成功
    """
    config_path = get_config_path_for_ide(ide)
    
    if config_path is None:
        print(f"{MCP_TEMPLATES.get(ide, {}).get('name', ide)} 使用内置配置，无需手动配置文件")
        return True
    
    config = generate_docker_config() if docker_mode else generate_native_config()
    
    # 读取现有配置（如果存在）
    existing = {}
    if config_path.exists():
        try:
            with open(config_path, encoding="utf-8") as f:
                existing = json.load(f)
        except Exception:
            pass
    
    # 合并配置
    if ide == "vscode":
        if "mcp" not in existing:
            existing["mcp"] = {}
        if "servers" not in existing["mcp"]:
            existing["mcp"]["servers"] = {}
        existing["mcp"]["servers"].update(config)
    else:
        if "mcpServers" not in existing:
            existing["mcpServers"] = {}
        existing["mcpServers"].update(config)
    
    # 创建目录
    config_path.parent.mkdir(parents=True, exist_ok=True)
    
    # 写入配置
    try:
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(existing, f, indent=2, ensure_ascii=False)
        
        print(f"✓ 配置已写入: {config_path}")
        return True
    except Exception as e:
        print(f"✗ 写入失败: {e}")
        return False


def list_ides():
    """列出所有支持的 IDE。"""
    print("\n支持的 IDE:")
    print("-" * 40)
    for ide, info in MCP_TEMPLATES.items():
        config_path = get_config_path_for_ide(ide)
        path_str = str(config_path) if config_path else "内置配置"
        print(f"  {info['name']:20} ({ide})")
        print(f"    路径: {path_str}")
    print()


def parse_args():
    """解析命令行参数。"""
    parser = argparse.ArgumentParser(
        description="RagHubMCP MCP 配置生成器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    parser.add_argument(
        "--ide",
        type=str,
        choices=list(MCP_TEMPLATES.keys()),
        help="指定 IDE",
    )
    
    parser.add_argument(
        "--print",
        action="store_true",
        help="打印配置到终端",
    )
    
    parser.add_argument(
        "--write",
        action="store_true",
        help="写入配置文件",
    )
    
    parser.add_argument(
        "--docker",
        action="store_true",
        help="生成 Docker 模式配置",
    )
    
    parser.add_argument(
        "--list",
        action="store_true",
        help="列出所有支持的 IDE",
    )
    
    return parser.parse_args()


def main():
    """主入口。"""
    args = parse_args()
    
    if args.list:
        list_ides()
        return
    
    # 选择 IDE
    ide = args.ide
    if not ide:
        print("\n请选择 IDE:")
        for i, (key, info) in enumerate(MCP_TEMPLATES.items(), 1):
            print(f"  [{i}] {info['name']} ({key})")
        
        try:
            choice = input("\n请选择 [1-6]: ").strip()
            ide = list(MCP_TEMPLATES.keys())[int(choice) - 1]
        except (ValueError, IndexError, KeyboardInterrupt):
            print("\n已取消")
            return
    
    # 默认打印配置
    if not args.write:
        print_config(ide, args.docker)
    else:
        write_config(ide, args.docker)


if __name__ == "__main__":
    main()