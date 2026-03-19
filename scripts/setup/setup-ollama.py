#!/usr/bin/env python3
"""
RagHubMCP Ollama 安装脚本

自动检测并安装 Ollama，支持：
- 检测操作系统
- 自动下载安装（调用官方脚本）
- 启动服务
- 验证服务运行

用法:
  python setup-ollama.py           # 安装 Ollama
  python setup-ollama.py --check   # 仅检测
  python setup-ollama.py --start   # 启动服务
  python setup-ollama.py --pull <model>  # 下载模型
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional

# 添加 lib 目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "lib"))

try:
    import lib.config as config_module
except ImportError:
    config_module = None


def get_ollama_default_port() -> int:
    """获取 Ollama 默认端口。"""
    if config_module:
        try:
            cfg = config_module.load_config()
            return cfg.ports.ollama
        except Exception:
            pass
    return 11434


def check_ollama_installed() -> dict:
    """检查 Ollama 是否已安装。
    
    Returns:
        dict: 包含 installed, version, path
    """
    result = {
        "installed": False,
        "version": None,
        "path": None,
    }
    
    ollama_path = shutil.which("ollama")
    if ollama_path:
        result["installed"] = True
        result["path"] = ollama_path
        
        try:
            proc = subprocess.run(
                ["ollama", "--version"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if proc.returncode == 0:
                result["version"] = proc.stdout.strip()
        except Exception:
            pass
    
    return result


def check_ollama_running(port: int = 11434) -> dict:
    """检查 Ollama 服务是否运行。
    
    Args:
        port: Ollama 服务端口
        
    Returns:
        dict: 包含 running, url, models
    """
    result = {
        "running": False,
        "url": f"http://localhost:{port}",
        "models": [],
    }
    
    try:
        import urllib.request
        import urllib.error
        
        url = f"http://localhost:{port}/api/version"
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=5) as response:
            if response.status == 200:
                result["running"] = True
                
                # 获取模型列表
                try:
                    models_url = f"http://localhost:{port}/api/tags"
                    req = urllib.request.Request(models_url, method="GET")
                    with urllib.request.urlopen(req, timeout=5) as models_resp:
                        if models_resp.status == 200:
                            data = json.loads(models_resp.read().decode())
                            result["models"] = [
                                m.get("name", m.get("model", "unknown"))
                                for m in data.get("models", [])
                            ]
                except Exception:
                    pass
    except (urllib.error.URLError, Exception):
        pass
    
    return result


def install_ollama() -> bool:
    """安装 Ollama。
    
    Returns:
        bool: 安装是否成功
    """
    system = platform.system()
    
    if system == "Darwin":  # macOS
        print("检测到 macOS，使用 Homebrew 安装...")
        if shutil.which("brew"):
            try:
                subprocess.run(["brew", "install", "ollama"], check=True)
                return True
            except subprocess.CalledProcessError:
                print("Homebrew 安装失败，请手动安装")
                return False
        else:
            print("未找到 Homebrew，请手动安装 Ollama")
            print("下载地址: https://ollama.ai/download")
            return False
    
    elif system == "Linux":
        print("检测到 Linux，使用官方脚本安装...")
        try:
            # 使用官方安装脚本
            proc = subprocess.run(
                ["curl", "-fsSL", "https://ollama.ai/install.sh"],
                capture_output=True,
                text=True,
                timeout=60,
            )
            if proc.returncode == 0:
                # 执行安装脚本
                install_proc = subprocess.run(
                    ["sh", "-c", proc.stdout],
                    capture_output=True,
                    text=True,
                    timeout=300,
                )
                if install_proc.returncode == 0:
                    print("Ollama 安装成功")
                    return True
                else:
                    print(f"安装失败: {install_proc.stderr}")
                    return False
            else:
                print("下载安装脚本失败")
                return False
        except Exception as e:
            print(f"安装过程出错: {e}")
            return False
    
    elif system == "Windows":
        print("检测到 Windows")
        print("Windows 安装需要手动下载安装程序")
        print("下载地址: https://ollama.ai/download")
        print("\n或者使用 WSL2 在 Linux 环境中安装")
        return False
    
    else:
        print(f"不支持的操作系统: {system}")
        return False


def start_ollama_service(port: int = 11434) -> bool:
    """启动 Ollama 服务。
    
    Args:
        port: 服务端口
        
    Returns:
        bool: 启动是否成功
    """
    # 检查是否已经在运行
    running = check_ollama_running(port)
    if running["running"]:
        print(f"Ollama 服务已在运行 (端口 {port})")
        return True
    
    print(f"正在启动 Ollama 服务 (端口 {port})...")
    
    # 设置环境变量
    env = os.environ.copy()
    env["OLLAMA_HOST"] = f"0.0.0.0:{port}"
    
    try:
        # 后台启动 ollama serve
        if platform.system() == "Windows":
            subprocess.Popen(
                ["ollama", "serve"],
                env=env,
                creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        else:
            subprocess.Popen(
                ["ollama", "serve"],
                env=env,
                start_new_session=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        
        # 等待服务启动
        for _ in range(10):
            time.sleep(1)
            if check_ollama_running(port)["running"]:
                print(f"Ollama 服务启动成功 (端口 {port})")
                return True
        
        print("服务启动超时")
        return False
    
    except Exception as e:
        print(f"启动服务失败: {e}")
        return False


def pull_model(model: str) -> bool:
    """下载 Ollama 模型。
    
    Args:
        model: 模型名称
        
    Returns:
        bool: 下载是否成功
    """
    print(f"正在下载模型: {model}")
    
    try:
        proc = subprocess.run(
            ["ollama", "pull", model],
            capture_output=True,
            text=True,
            timeout=600,  # 10 分钟超时
        )
        if proc.returncode == 0:
            print(f"模型 {model} 下载成功")
            return True
        else:
            print(f"下载失败: {proc.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print("下载超时")
        return False
    except Exception as e:
        print(f"下载出错: {e}")
        return False


def print_status():
    """打印 Ollama 状态。"""
    print("\n" + "=" * 50)
    print(" Ollama 状态检查")
    print("=" * 50)
    
    # 安装状态
    installed = check_ollama_installed()
    print(f"\n[安装状态]")
    if installed["installed"]:
        print(f"  ✓ 已安装")
        print(f"    版本: {installed['version'] or 'Unknown'}")
        print(f"    路径: {installed['path']}")
    else:
        print("  ✗ 未安装")
        return
    
    # 运行状态
    port = get_ollama_default_port()
    running = check_ollama_running(port)
    print(f"\n[运行状态]")
    if running["running"]:
        print(f"  ✓ 运行中 (端口 {port})")
        if running["models"]:
            print(f"  已安装模型:")
            for model in running["models"]:
                print(f"    - {model}")
        else:
            print("  暂无已安装模型")
    else:
        print("  ✗ 未运行")


def parse_args():
    """解析命令行参数。"""
    parser = argparse.ArgumentParser(
        description="RagHubMCP Ollama 安装工具",
    )
    
    parser.add_argument(
        "--check",
        action="store_true",
        help="仅检测，不安装",
    )
    
    parser.add_argument(
        "--start",
        action="store_true",
        help="启动 Ollama 服务",
    )
    
    parser.add_argument(
        "--pull",
        type=str,
        metavar="MODEL",
        help="下载指定模型",
    )
    
    parser.add_argument(
        "--port",
        type=int,
        default=None,
        help="指定服务端口",
    )
    
    return parser.parse_args()


def main():
    """主入口。"""
    args = parse_args()
    port = args.port or get_ollama_default_port()
    
    if args.check:
        print_status()
        return
    
    if args.start:
        start_ollama_service(port)
        print_status()
        return
    
    if args.pull:
        pull_model(args.pull)
        return
    
    # 默认：检测并安装
    print_status()
    
    installed = check_ollama_installed()
    if not installed["installed"]:
        print("\n" + "-" * 50)
        choice = input("是否安装 Ollama? [y/N]: ").strip().lower()
        if choice == "y":
            if install_ollama():
                start_ollama_service(port)
                print_status()
    else:
        running = check_ollama_running(port)
        if not running["running"]:
            print("\n" + "-" * 50)
            choice = input("是否启动 Ollama 服务? [y/N]: ").strip().lower()
            if choice == "y":
                start_ollama_service(port)
                print_status()


if __name__ == "__main__":
    main()