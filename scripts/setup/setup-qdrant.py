#!/usr/bin/env python3
"""
RagHubMCP Qdrant 安装脚本

支持多种安装方式：
- Docker 方式（推荐）
- 本地二进制安装
- 验证服务运行

用法:
  python setup-qdrant.py           # 安装 Qdrant
  python setup-qdrant.py --check   # 仅检测
  python setup-qdrant.py --start   # 启动服务
  python setup-qdrant.py --stop    # 停止服务
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

# Qdrant Docker 镜像
QDRANT_IMAGE = "qdrant/qdrant:latest"
QDRANT_CONTAINER_NAME = "raghub-qdrant"


def get_qdrant_config() -> dict:
    """获取 Qdrant 配置。"""
    defaults = {
        "port": 6333,
        "persist_dir": str(Path.home() / "RagHubMCP" / "data" / "qdrant"),
    }
    
    if config_module:
        try:
            cfg = config_module.load_config()
            return {
                "port": cfg.ports.qdrant,
                "persist_dir": cfg.database.persist_dir.replace("/chroma", "/qdrant"),
            }
        except Exception:
            pass
    
    return defaults


def check_docker_available() -> bool:
    """检查 Docker 是否可用。"""
    try:
        result = subprocess.run(
            ["docker", "info"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return result.returncode == 0
    except Exception:
        return False


def check_qdrant_docker() -> dict:
    """检查 Qdrant Docker 容器状态。
    
    Returns:
        dict: 包含 installed, running, container_id, port
    """
    result = {
        "installed": False,
        "running": False,
        "container_id": None,
        "port": None,
    }
    
    try:
        # 检查容器是否存在
        proc = subprocess.run(
            ["docker", "ps", "-a", "--filter", f"name={QDRANT_CONTAINER_NAME}",
             "--format", "{{.ID}}\t{{.Status}}\t{{.Ports}}"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        
        if proc.returncode == 0 and proc.stdout.strip():
            lines = proc.stdout.strip().split("\n")
            if lines:
                parts = lines[0].split("\t")
                result["installed"] = True
                result["container_id"] = parts[0]
                
                # 检查是否运行
                status = parts[1] if len(parts) > 1 else ""
                result["running"] = "Up" in status
                
                # 提取端口
                if len(parts) > 2:
                    ports = parts[2]
                    if "6333" in ports:
                        result["port"] = 6333
    
    except Exception:
        pass
    
    return result


def check_qdrant_service(port: int = 6333) -> dict:
    """检查 Qdrant 服务是否运行。
    
    Args:
        port: Qdrant 服务端口
        
    Returns:
        dict: 包含 running, url, collections
    """
    result = {
        "running": False,
        "url": f"http://localhost:{port}",
        "collections": [],
    }
    
    try:
        import urllib.request
        import urllib.error
        
        url = f"http://localhost:{port}/collections"
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=5) as response:
            if response.status == 200:
                result["running"] = True
                data = json.loads(response.read().decode())
                result["collections"] = [
                    c.get("name", "unknown")
                    for c in data.get("result", {}).get("collections", [])
                ]
    except (urllib.error.URLError, Exception):
        pass
    
    return result


def install_qdrant_docker(port: int, persist_dir: str) -> bool:
    """使用 Docker 安装 Qdrant。
    
    Args:
        port: 服务端口
        persist_dir: 数据持久化目录
        
    Returns:
        bool: 安装是否成功
    """
    if not check_docker_available():
        print("Docker 不可用，无法使用 Docker 方式安装")
        return False
    
    # 创建数据目录
    Path(persist_dir).mkdir(parents=True, exist_ok=True)
    
    print(f"正在拉取 Qdrant 镜像: {QDRANT_IMAGE}")
    
    try:
        # 拉取镜像
        proc = subprocess.run(
            ["docker", "pull", QDRANT_IMAGE],
            capture_output=True,
            text=True,
            timeout=300,
        )
        if proc.returncode != 0:
            print(f"拉取镜像失败: {proc.stderr}")
            return False
        
        print("镜像拉取成功")
        return True
    
    except Exception as e:
        print(f"安装失败: {e}")
        return False


def start_qdrant_docker(port: int, persist_dir: str) -> bool:
    """启动 Qdrant Docker 容器。
    
    Args:
        port: 服务端口
        persist_dir: 数据持久化目录
        
    Returns:
        bool: 启动是否成功
    """
    # 检查是否已在运行
    status = check_qdrant_docker()
    if status["running"]:
        print(f"Qdrant 容器已在运行 (ID: {status['container_id']})")
        return True
    
    # 如果容器存在但未运行，启动它
    if status["installed"]:
        print("正在启动现有容器...")
        try:
            subprocess.run(
                ["docker", "start", QDRANT_CONTAINER_NAME],
                capture_output=True,
                text=True,
                timeout=30,
            )
            return True
        except Exception as e:
            print(f"启动失败: {e}")
            return False
    
    # 创建数据目录
    Path(persist_dir).mkdir(parents=True, exist_ok=True)
    
    print(f"正在创建并启动 Qdrant 容器...")
    
    try:
        proc = subprocess.run(
            [
                "docker", "run", "-d",
                "--name", QDRANT_CONTAINER_NAME,
                "-p", f"{port}:6333",
                "-p", f"{port+1}:6334",  # gRPC 端口
                "-v", f"{persist_dir}:/qdrant/storage",
                QDRANT_IMAGE,
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )
        
        if proc.returncode == 0:
            print(f"Qdrant 容器启动成功 (端口 {port})")
            return True
        else:
            print(f"启动失败: {proc.stderr}")
            return False
    
    except Exception as e:
        print(f"启动失败: {e}")
        return False


def stop_qdrant_docker() -> bool:
    """停止 Qdrant Docker 容器。
    
    Returns:
        bool: 停止是否成功
    """
    status = check_qdrant_docker()
    if not status["installed"]:
        print("Qdrant 容器不存在")
        return True
    
    print("正在停止 Qdrant 容器...")
    
    try:
        subprocess.run(
            ["docker", "stop", QDRANT_CONTAINER_NAME],
            capture_output=True,
            text=True,
            timeout=30,
        )
        print("Qdrant 容器已停止")
        return True
    except Exception as e:
        print(f"停止失败: {e}")
        return False


def remove_qdrant_docker() -> bool:
    """删除 Qdrant Docker 容器。
    
    Returns:
        bool: 删除是否成功
    """
    stop_qdrant_docker()
    
    print("正在删除 Qdrant 容器...")
    
    try:
        subprocess.run(
            ["docker", "rm", QDRANT_CONTAINER_NAME],
            capture_output=True,
            text=True,
            timeout=30,
        )
        print("Qdrant 容器已删除")
        return True
    except Exception as e:
        print(f"删除失败: {e}")
        return False


def print_status():
    """打印 Qdrant 状态。"""
    print("\n" + "=" * 50)
    print(" Qdrant 状态检查")
    print("=" * 50)
    
    config = get_qdrant_config()
    port = config["port"]
    persist_dir = config["persist_dir"]
    
    print(f"\n[配置]")
    print(f"  端口: {port}")
    print(f"  数据目录: {persist_dir}")
    
    # Docker 状态
    docker_status = check_qdrant_docker()
    print(f"\n[Docker 容器]")
    if docker_status["installed"]:
        print(f"  ✓ 容器存在")
        if docker_status["running"]:
            print(f"  ✓ 运行中 (ID: {docker_status['container_id'][:12]})")
        else:
            print(f"  ✗ 已停止")
    else:
        print("  ✗ 容器不存在")
    
    # 服务状态
    service_status = check_qdrant_service(port)
    print(f"\n[服务状态]")
    if service_status["running"]:
        print(f"  ✓ 运行中 (端口 {port})")
        print(f"  URL: {service_status['url']}")
        if service_status["collections"]:
            print(f"  Collections: {len(service_status['collections'])}")
    else:
        print(f"  ✗ 未运行")


def parse_args():
    """解析命令行参数。"""
    parser = argparse.ArgumentParser(
        description="RagHubMCP Qdrant 安装工具",
    )
    
    parser.add_argument(
        "--check",
        action="store_true",
        help="仅检测，不安装",
    )
    
    parser.add_argument(
        "--start",
        action="store_true",
        help="启动 Qdrant 服务",
    )
    
    parser.add_argument(
        "--stop",
        action="store_true",
        help="停止 Qdrant 服务",
    )
    
    parser.add_argument(
        "--remove",
        action="store_true",
        help="删除 Qdrant 容器",
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
    config = get_qdrant_config()
    port = args.port or config["port"]
    persist_dir = config["persist_dir"]
    
    if args.check:
        print_status()
        return
    
    if args.stop:
        stop_qdrant_docker()
        return
    
    if args.remove:
        remove_qdrant_docker()
        return
    
    if args.start:
        start_qdrant_docker(port, persist_dir)
        print_status()
        return
    
    # 默认：检测并安装
    print_status()
    
    docker_status = check_qdrant_docker()
    if not docker_status["installed"]:
        if check_docker_available():
            print("\n" + "-" * 50)
            choice = input("是否使用 Docker 安装 Qdrant? [y/N]: ").strip().lower()
            if choice == "y":
                if install_qdrant_docker(port, persist_dir):
                    start_qdrant_docker(port, persist_dir)
                    print_status()
        else:
            print("\nDocker 不可用。请手动安装 Qdrant 或先安装 Docker。")
    else:
        if not docker_status["running"]:
            print("\n" + "-" * 50)
            choice = input("是否启动 Qdrant 服务? [y/N]: ").strip().lower()
            if choice == "y":
                start_qdrant_docker(port, persist_dir)
                print_status()


if __name__ == "__main__":
    main()