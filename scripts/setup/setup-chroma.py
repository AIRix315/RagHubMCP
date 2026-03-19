#!/usr/bin/env python3
"""
RagHubMCP Chroma 安装脚本

支持：
- pip 安装 chromadb
- 创建数据目录
- 验证可用性

用法:
  python setup-chroma.py           # 安装 Chroma
  python setup-chroma.py --check   # 仅检测
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Optional

# 添加 lib 目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "lib"))

try:
    import lib.config as config_module
except ImportError:
    config_module = None


def get_chroma_config() -> dict:
    """获取 Chroma 配置。"""
    defaults = {
        "persist_dir": str(Path.home() / "RagHubMCP" / "data" / "chroma"),
    }
    
    if config_module:
        try:
            cfg = config_module.load_config()
            return {
                "persist_dir": cfg.database.persist_dir,
            }
        except Exception:
            pass
    
    return defaults


def check_chromadb_installed() -> dict:
    """检查 chromadb 是否已安装。
    
    Returns:
        dict: 包含 installed, version
    """
    result = {
        "installed": False,
        "version": None,
    }
    
    try:
        import chromadb
        result["installed"] = True
        result["version"] = getattr(chromadb, "__version__", "unknown")
    except ImportError:
        pass
    
    return result


def install_chromadb() -> bool:
    """安装 chromadb。
    
    Returns:
        bool: 安装是否成功
    """
    print("正在安装 chromadb...")
    
    try:
        proc = subprocess.run(
            [sys.executable, "-m", "pip", "install", "chromadb"],
            capture_output=True,
            text=True,
            timeout=300,
        )
        
        if proc.returncode == 0:
            print("chromadb 安装成功")
            return True
        else:
            print(f"安装失败: {proc.stderr}")
            return False
    
    except Exception as e:
        print(f"安装出错: {e}")
        return False


def verify_chromadb(persist_dir: str) -> dict:
    """验证 chromadb 可用性。
    
    Args:
        persist_dir: 持久化目录
        
    Returns:
        dict: 包含 working, message
    """
    result = {
        "working": False,
        "message": None,
    }
    
    try:
        import chromadb
        from chromadb.config import Settings
        
        # 创建持久化目录
        Path(persist_dir).mkdir(parents=True, exist_ok=True)
        
        # 尝试创建客户端
        client = chromadb.PersistentClient(
            path=persist_dir,
            settings=Settings(anonymized_telemetry=False),
        )
        
        # 尝试创建和删除 collection
        test_collection = client.get_or_create_collection("test_setup")
        client.delete_collection("test_setup")
        
        result["working"] = True
        result["message"] = "ChromaDB 工作正常"
    
    except ImportError:
        result["message"] = "chromadb 未安装"
    except Exception as e:
        result["message"] = str(e)
    
    return result


def print_status():
    """打印 Chroma 状态。"""
    print("\n" + "=" * 50)
    print(" ChromaDB 状态检查")
    print("=" * 50)
    
    config = get_chroma_config()
    persist_dir = config["persist_dir"]
    
    print(f"\n[配置]")
    print(f"  数据目录: {persist_dir}")
    
    # 安装状态
    installed = check_chromadb_installed()
    print(f"\n[安装状态]")
    if installed["installed"]:
        print(f"  ✓ 已安装")
        print(f"    版本: {installed['version']}")
    else:
        print("  ✗ 未安装")
        return
    
    # 目录状态
    print(f"\n[数据目录]")
    persist_path = Path(persist_dir)
    if persist_path.exists():
        print(f"  ✓ 已存在: {persist_path}")
    else:
        print(f"  ✗ 不存在: {persist_path}")
    
    # 功能验证
    verification = verify_chromadb(persist_dir)
    print(f"\n[功能验证]")
    if verification["working"]:
        print(f"  ✓ {verification['message']}")
    else:
        print(f"  ✗ {verification['message']}")


def parse_args():
    """解析命令行参数。"""
    parser = argparse.ArgumentParser(
        description="RagHubMCP ChromaDB 安装工具",
    )
    
    parser.add_argument(
        "--check",
        action="store_true",
        help="仅检测，不安装",
    )
    
    parser.add_argument(
        "--persist-dir",
        type=str,
        default=None,
        help="指定数据持久化目录",
    )
    
    return parser.parse_args()


def main():
    """主入口。"""
    args = parse_args()
    config = get_chroma_config()
    persist_dir = args.persist_dir or config["persist_dir"]
    
    if args.check:
        print_status()
        return
    
    # 默认：检测并安装
    print_status()
    
    installed = check_chromadb_installed()
    if not installed["installed"]:
        print("\n" + "-" * 50)
        choice = input("是否安装 chromadb? [y/N]: ").strip().lower()
        if choice == "y":
            if install_chromadb():
                print_status()
    else:
        # 创建目录
        Path(persist_dir).mkdir(parents=True, exist_ok=True)
        print(f"\n数据目录已创建: {persist_dir}")
        
        # 验证
        verification = verify_chromadb(persist_dir)
        if not verification["working"]:
            print(f"\n警告: {verification['message']}")


if __name__ == "__main__":
    main()