#!/usr/bin/env python3
"""
RagHubMCP 一键安装脚本

集成所有独立脚本的安装入口，支持：
- 环境检测
- 组件安装
- MCP 配置生成
- 安装报告

用法:
  python install.py                    # 交互式安装
  python install.py --mode docker      # Docker 模式
  python install.py --mode native      # 原生模式
  python install.py --dry-run          # 预览安装步骤
  python install.py --skip-mcp         # 跳过 MCP 配置
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional

# 添加 lib 目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "lib"))

# 导入配置模块
import importlib.util
_config_path = Path(__file__).parent.parent / "lib" / "config.py"
_spec = importlib.util.spec_from_file_location("config", _config_path)
if _spec is None or _spec.loader is None:
    raise ImportError("Cannot load config module")
config_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(config_module)


def run_script(script_path: str, args: list = None, capture: bool = False) -> int:
    """运行脚本。
    
    Args:
        script_path: 脚本路径
        args: 参数列表
        capture: 是否捕获输出
        
    Returns:
        int: 退出码
    """
    cmd = [sys.executable, script_path]
    if args:
        cmd.extend(args)
    
    if capture:
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.returncode
    else:
        return subprocess.run(cmd).returncode


def step_environment_check(dry_run: bool = False) -> dict:
    """步骤1: 环境检测。
    
    Args:
        dry_run: 是否为预览模式
        
    Returns:
        dict: 环境报告
    """
    print("\n" + "=" * 60)
    print(" 步骤 1: 环境检测")
    print("=" * 60)
    
    script_path = Path(__file__).parent.parent / "check" / "check-env.py"
    
    if dry_run:
        print("  [预览] 将运行环境检查脚本")
        return {}
    
    # 运行环境检查
    result = subprocess.run(
        [sys.executable, str(script_path), "--json"],
        capture_output=True,
        text=True,
    )
    
    if result.returncode == 0:
        report = json.loads(result.stdout)
        
        # 显示摘要
        print(f"\n  Python: {'✓' if report.get('python', {}).get('sufficient') else '✗'}")
        print(f"  Node.js: {'✓' if report.get('node', {}).get('sufficient') else '✗'}")
        print(f"  Docker: {'✓' if report.get('docker', {}).get('installed') else '✗'}")
        print(f"  Ollama: {'✓' if report.get('ollama', {}).get('installed') else '✗'}")
        
        return report
    else:
        print("  ✗ 环境检测失败")
        return {}


def step_init_config(dry_run: bool = False, install_dir: str = None) -> bool:
    """步骤2: 初始化配置。
    
    Args:
        dry_run: 是否为预览模式
        install_dir: 安装目录
        
    Returns:
        bool: 是否成功
    """
    print("\n" + "=" * 60)
    print(" 步骤 2: 初始化配置")
    print("=" * 60)
    
    script_path = Path(__file__).parent.parent / "config" / "init-config.py"
    
    args = ["--dry-run"] if dry_run else []
    if install_dir:
        args.extend(["--install-dir", install_dir])
    
    if dry_run:
        print("  [预览] 将初始化配置文件")
        return True
    
    return run_script(str(script_path), args) == 0


def step_install_components(dry_run: bool = False, components: list = None) -> bool:
    """步骤3: 安装组件。
    
    Args:
        dry_run: 是否为预览模式
        components: 要安装的组件列表
        
    Returns:
        bool: 是否成功
    """
    print("\n" + "=" * 60)
    print(" 步骤 3: 安装组件")
    print("=" * 60)
    
    if dry_run:
        print("  [预览] 将安装选定的组件")
        return True
    
    scripts_dir = Path(__file__).parent.parent
    
    success = True
    
    # Chroma 是必需的
    print("\n  安装 Chroma...")
    chroma_script = scripts_dir / "setup" / "setup-chroma.py"
    if run_script(str(chroma_script), ["--check"]) != 0:
        if run_script(str(chroma_script)) != 0:
            success = False
    
    # Ollama 可选
    if components and "ollama" in components:
        print("\n  安装 Ollama...")
        ollama_script = scripts_dir / "setup" / "setup-ollama.py"
        run_script(str(ollama_script), ["--check"])
    
    return success


def step_mcp_config(dry_run: bool = False, ide: str = None) -> bool:
    """步骤4: MCP 配置。
    
    Args:
        dry_run: 是否为预览模式
        ide: IDE 名称
        
    Returns:
        bool: 是否成功
    """
    print("\n" + "=" * 60)
    print(" 步骤 4: MCP 配置")
    print("=" * 60)
    
    if dry_run:
        print("  [预览] 将生成 MCP 配置")
        return True
    
    script_path = Path(__file__).parent.parent / "config" / "generate-mcp-config.py"
    
    args = ["--print"]
    if ide:
        args.extend(["--ide", ide])
    
    return run_script(str(script_path), args) == 0


def print_installation_report(report: dict):
    """打印安装报告。
    
    Args:
        report: 安装报告
    """
    print("\n" + "=" * 60)
    print(" 安装报告")
    print("=" * 60)
    
    print(f"\n  配置文件: {config_module.get_config_path()}")
    
    if report.get("environment"):
        env = report["environment"]
        print(f"\n  推荐部署方式: {env.get('recommendation', 'Unknown')}")
    
    print("\n  后续步骤:")
    print("    1. 启动后端: cd backend && python -m src.main")
    print("    2. 启动前端: cd frontend && npm run dev")
    print("    3. 访问控制台: http://localhost:3315")
    print("    4. API 文档: http://localhost:8818/docs")
    
    print("\n" + "=" * 60)


def parse_args():
    """解析命令行参数。"""
    parser = argparse.ArgumentParser(
        description="RagHubMCP 一键安装工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    parser.add_argument(
        "--mode",
        type=str,
        choices=["docker", "native", "manual"],
        default="native",
        help="部署模式",
    )
    
    parser.add_argument(
        "--install-dir",
        type=str,
        help="安装目录",
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="预览安装步骤",
    )
    
    parser.add_argument(
        "--skip-mcp",
        action="store_true",
        help="跳过 MCP 配置",
    )
    
    parser.add_argument(
        "--ide",
        type=str,
        help="指定 IDE 生成 MCP 配置",
    )
    
    parser.add_argument(
        "--components",
        type=str,
        nargs="+",
        choices=["ollama", "qdrant"],
        help="要安装的组件",
    )
    
    return parser.parse_args()


def main():
    """主入口。"""
    args = parse_args()
    
    print("\n" + "=" * 60)
    print(" RagHubMCP 安装向导")
    print("=" * 60)
    
    if args.dry_run:
        print("\n[预览模式] 不执行实际操作")
    
    report = {}
    
    # 步骤1: 环境检测
    report["environment"] = step_environment_check(args.dry_run)
    
    # 步骤2: 初始化配置
    step_init_config(args.dry_run, args.install_dir)
    
    # 步骤3: 安装组件
    if args.mode == "native":
        step_install_components(args.dry_run, args.components)
    elif args.mode == "docker":
        print("\n  Docker 模式: 使用 docker-compose up -d 启动")
    
    # 步骤4: MCP 配置
    if not args.skip_mcp:
        step_mcp_config(args.dry_run, args.ide)
    
    # 打印报告
    if not args.dry_run:
        print_installation_report(report)


if __name__ == "__main__":
    main()