#!/usr/bin/env python3
"""
RagHubMCP 环境检查脚本

检查系统环境并输出报告，包括：
- Python 版本检测 (>=3.11)
- Node.js 版本检测 (>=18)
- Git 环境检查
- Docker 环境检查
- Ollama 环境检查（服务状态 + 模型列表）
- 端口占用检测
- 硬件资源评估
- 智能推荐部署方式

用法:
  python check-env.py           # 输出文本报告
  python check-env.py --json    # 输出 JSON 格式
  python check-env.py --fix     # 输出修复建议
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import socket
import subprocess
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Optional

# 添加 lib 目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "lib"))

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False


# 最低版本要求
MIN_PYTHON_VERSION = (3, 11)
MIN_NODE_VERSION = (18, 0, 0)


def parse_version(version_str: str) -> tuple:
    """解析版本字符串为元组。"""
    parts = []
    for part in version_str.split("."):
        # 移除非数字后缀
        clean = ""
        for char in part:
            if char.isdigit():
                clean += char
            else:
                break
        if clean:
            parts.append(int(clean))
    return tuple(parts) if parts else (0,)


def check_python_version(min_version: tuple = MIN_PYTHON_VERSION) -> dict[str, Any]:
    """检查 Python 版本。
    
    Args:
        min_version: 最低版本要求
        
    Returns:
        dict: 包含 version, installed, sufficient, min_required
    """
    current = sys.version_info[:2]
    version_str = f"{current[0]}.{current[1]}.{sys.version_info[2]}"
    
    return {
        "installed": True,
        "version": version_str,
        "sufficient": current >= min_version,
        "min_required": f"{min_version[0]}.{min_version[1]}",
        "path": sys.executable,
    }


def check_node_version(min_version: tuple = MIN_NODE_VERSION) -> dict[str, Any]:
    """检查 Node.js 版本。
    
    Args:
        min_version: 最低版本要求
        
    Returns:
        dict: 包含 version, installed, sufficient
    """
    result = {
        "installed": False,
        "version": None,
        "sufficient": False,
        "min_required": f"{min_version[0]}.{min_version[1]}.{min_version[2]}",
        "path": None,
    }
    
    try:
        # 检查 node 是否存在
        node_path = shutil.which("node")
        if node_path:
            result["installed"] = True
            result["path"] = node_path
            
            # 获取版本
            proc = subprocess.run(
                ["node", "--version"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if proc.returncode == 0:
                version_str = proc.stdout.strip().lstrip("v")
                result["version"] = version_str
                result["sufficient"] = parse_version(version_str) >= min_version
    except (FileNotFoundError, subprocess.TimeoutExpired, Exception):
        pass
    
    return result


def check_git() -> dict[str, Any]:
    """检查 Git 环境。
    
    Returns:
        dict: 包含 installed, version, path
    """
    result = {
        "installed": False,
        "version": None,
        "path": None,
    }
    
    try:
        git_path = shutil.which("git")
        if git_path:
            result["installed"] = True
            result["path"] = git_path
            
            proc = subprocess.run(
                ["git", "--version"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if proc.returncode == 0:
                # 输出格式: git version 2.39.0
                version_str = proc.stdout.strip().split()[-1]
                result["version"] = version_str
    except (FileNotFoundError, subprocess.TimeoutExpired, Exception):
        pass
    
    return result


def check_docker() -> dict[str, Any]:
    """检查 Docker 环境。
    
    Returns:
        dict: 包含 installed, running, version
    """
    result = {
        "installed": False,
        "running": False,
        "version": None,
        "compose_version": None,
    }
    
    try:
        docker_path = shutil.which("docker")
        if docker_path:
            result["installed"] = True
            
            # 检查 Docker 版本
            proc = subprocess.run(
                ["docker", "--version"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if proc.returncode == 0:
                # 输出格式: Docker version 24.0.5, build ced0996
                version_str = proc.stdout.strip().split()[2].rstrip(",")
                result["version"] = version_str
            
            # 检查 Docker 是否运行
            proc = subprocess.run(
                ["docker", "info"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            result["running"] = proc.returncode == 0
            
            # 检查 Docker Compose
            compose_path = shutil.which("docker-compose") or shutil.which("docker")
            if compose_path:
                try:
                    proc = subprocess.run(
                        ["docker", "compose", "version"],
                        capture_output=True,
                        text=True,
                        timeout=10,
                    )
                    if proc.returncode == 0:
                        result["compose_version"] = proc.stdout.strip().split()[-1]
                except Exception:
                    pass
    except (FileNotFoundError, subprocess.TimeoutExpired, Exception):
        pass
    
    return result


def check_ollama(host: str = "localhost", port: int = 11434) -> dict[str, Any]:
    """检查 Ollama 环境。
    
    Args:
        host: Ollama 服务主机
        port: Ollama 服务端口
        
    Returns:
        dict: 包含 installed, running, models, version
    """
    result = {
        "installed": False,
        "running": False,
        "models": [],
        "version": None,
        "url": f"http://{host}:{port}",
    }
    
    # 检查 ollama 命令是否存在
    ollama_path = shutil.which("ollama")
    if ollama_path:
        result["installed"] = True
        
        # 获取版本
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
    
    # 检查服务是否运行
    try:
        import urllib.request
        import urllib.error
        
        url = f"http://{host}:{port}/api/version"
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=5) as response:
            if response.status == 200:
                result["running"] = True
                
                # 获取模型列表
                try:
                    models_url = f"http://{host}:{port}/api/tags"
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


def check_port_available(port: int, host: str = "127.0.0.1") -> dict[str, Any]:
    """检查端口是否可用。
    
    Args:
        port: 端口号
        host: 主机地址
        
    Returns:
        dict: 包含 port, available, host
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            result = s.connect_ex((host, port))
            available = result != 0  # 连接失败表示端口可用
            return {
                "port": port,
                "available": available,
                "host": host,
            }
    except Exception as e:
        return {
            "port": port,
            "available": False,
            "host": host,
            "error": str(e),
        }


def check_hardware_resources() -> dict[str, Any]:
    """检查硬件资源。
    
    Returns:
        dict: 包含 memory_gb, cpu_count, disk_gb (可选)
    """
    result = {
        "memory_gb": 0,
        "cpu_count": 0,
        "platform": platform.system(),
        "architecture": platform.machine(),
    }
    
    try:
        if HAS_PSUTIL:
            import psutil
            
            # 内存
            mem = psutil.virtual_memory()
            result["memory_gb"] = round(mem.total / (1024**3), 1)
            result["memory_available_gb"] = round(mem.available / (1024**3), 1)
            
            # CPU
            result["cpu_count"] = psutil.cpu_count(logical=True)
            result["cpu_physical_count"] = psutil.cpu_count(logical=False)
            
            # 磁盘
            disk = psutil.disk_usage("/")
            result["disk_gb"] = round(disk.total / (1024**3), 1)
            result["disk_available_gb"] = round(disk.free / (1024**3), 1)
            
            # GPU 检测 (通过 nvidia-smi)
            try:
                proc = subprocess.run(
                    ["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                if proc.returncode == 0:
                    result["gpu"] = []
                    for line in proc.stdout.strip().split("\n"):
                        if line.strip():
                            parts = [p.strip() for p in line.split(",")]
                            if len(parts) >= 2:
                                result["gpu"].append({
                                    "name": parts[0],
                                    "memory": parts[1],
                                })
            except Exception:
                pass
        else:
            # 没有 psutil 时使用基础方法
            result["memory_gb"] = 0
            result["cpu_count"] = os.cpu_count() or 1
    except Exception:
        pass
    
    return result


def get_environment_report(
    ports: Optional[list[int]] = None,
    ollama_port: int = 11434,
) -> dict[str, Any]:
    """生成完整的环境报告。
    
    Args:
        ports: 需要检查的端口列表
        ollama_port: Ollama 服务端口
        
    Returns:
        dict: 完整的环境报告
    """
    if ports is None:
        ports = [8818, 3315, 11434, 6333]
    
    report = {
        "system": {
            "os": platform.system(),
            "os_version": platform.version(),
            "architecture": platform.machine(),
        },
        "python": check_python_version(),
        "node": check_node_version(),
        "git": check_git(),
        "docker": check_docker(),
        "ollama": check_ollama(port=ollama_port),
        "hardware": check_hardware_resources(),
        "ports": {},
    }
    
    # 检查端口
    port_names = {
        8818: "backend",
        3315: "frontend",
        11434: "ollama",
        6333: "qdrant",
    }
    for port in ports:
        name = port_names.get(port, f"port_{port}")
        report["ports"][name] = check_port_available(port)
    
    return report


def recommend_deployment_mode(report: dict[str, Any]) -> str:
    """根据环境报告推荐部署方式。
    
    Args:
        report: 环境报告
        
    Returns:
        str: 推荐的部署方式 (docker/native/manual/partial)
    """
    docker = report.get("docker", {})
    python = report.get("python", {})
    node = report.get("node", {})
    
    # Docker 可用且运行中
    if docker.get("installed") and docker.get("running"):
        return "docker"
    
    # Python 和 Node 都满足要求
    if python.get("sufficient") and node.get("sufficient"):
        return "native"
    
    # 只有 Python 满足
    if python.get("sufficient"):
        return "backend-only"
    
    # 需要手动安装
    return "manual"


def print_report(report: dict[str, Any], show_fix: bool = False):
    """打印文本格式的环境报告。
    
    Args:
        report: 环境报告
        show_fix: 是否显示修复建议
    """
    print("\n" + "=" * 60)
    print(" RagHubMCP 环境检查报告")
    print("=" * 60)
    
    # 系统
    print(f"\n[系统信息]")
    sys_info = report.get("system", {})
    print(f"  操作系统: {sys_info.get('os', 'Unknown')} {sys_info.get('architecture', '')}")
    
    # Python
    print(f"\n[Python]")
    py = report.get("python", {})
    status = "✓" if py.get("sufficient") else "✗"
    print(f"  {status} 版本: {py.get('version', 'N/A')}")
    print(f"    最低要求: {py.get('min_required', '3.11')}")
    print(f"    路径: {py.get('path', 'N/A')}")
    if show_fix and not py.get("sufficient"):
        print(f"    [修复] 请升级 Python 到 {py.get('min_required')} 或更高版本")
    
    # Node.js
    print(f"\n[Node.js]")
    node = report.get("node", {})
    if node.get("installed"):
        status = "✓" if node.get("sufficient") else "✗"
        print(f"  {status} 版本: {node.get('version', 'N/A')}")
        print(f"    最低要求: {node.get('min_required', '18.0.0')}")
        print(f"    路径: {node.get('path', 'N/A')}")
        if show_fix and not node.get("sufficient"):
            print(f"    [修复] 请升级 Node.js 到 {node.get('min_required')} 或更高版本")
    else:
        print("  ✗ 未安装")
        if show_fix:
            print("    [修复] 请安装 Node.js 18 或更高版本: https://nodejs.org")
    
    # Git
    print(f"\n[Git]")
    git = report.get("git", {})
    if git.get("installed"):
        print(f"  ✓ 版本: {git.get('version', 'N/A')}")
    else:
        print("  ✗ 未安装")
        if show_fix:
            print("    [修复] 请安装 Git: https://git-scm.com")
    
    # Docker
    print(f"\n[Docker]")
    docker = report.get("docker", {})
    if docker.get("installed"):
        running_status = "✓" if docker.get("running") else "✗"
        print(f"  ✓ 版本: {docker.get('version', 'N/A')}")
        print(f"  {running_status} 运行状态: {'运行中' if docker.get('running') else '未运行'}")
        if docker.get("compose_version"):
            print(f"  ✓ Compose: {docker.get('compose_version')}")
        if show_fix and not docker.get("running"):
            print("    [修复] 请启动 Docker 服务")
    else:
        print("  ✗ 未安装")
        if show_fix:
            print("    [修复] 请安装 Docker: https://docs.docker.com/get-docker/")
    
    # Ollama
    print(f"\n[Ollama]")
    ollama = report.get("ollama", {})
    if ollama.get("installed"):
        running_status = "✓" if ollama.get("running") else "✗"
        print(f"  ✓ 已安装")
        print(f"  {running_status} 运行状态: {'运行中' if ollama.get('running') else '未运行'}")
        if ollama.get("models"):
            print(f"  可用模型: {', '.join(ollama.get('models', []))}")
    else:
        print("  ✗ 未安装")
        if show_fix:
            print("    [修复] 请安装 Ollama: https://ollama.ai")
    
    # 硬件
    print(f"\n[硬件资源]")
    hw = report.get("hardware", {})
    print(f"  内存: {hw.get('memory_gb', 0)} GB")
    print(f"  CPU: {hw.get('cpu_count', 0)} 核心")
    if hw.get("disk_gb"):
        print(f"  磁盘: {hw.get('disk_gb', 0)} GB (可用 {hw.get('disk_available_gb', 0)} GB)")
    if hw.get("gpu"):
        for gpu in hw.get("gpu", []):
            print(f"  GPU: {gpu.get('name', 'Unknown')} ({gpu.get('memory', 'N/A')})")
    
    # 端口
    print(f"\n[端口检测]")
    ports = report.get("ports", {})
    for name, info in ports.items():
        status = "✓ 可用" if info.get("available") else "✗ 占用"
        print(f"  {status} {name}: {info.get('port', 'N/A')}")
    
    # 推荐
    print(f"\n[部署推荐]")
    mode = recommend_deployment_mode(report)
    mode_desc = {
        "docker": "Docker 部署（推荐）",
        "native": "原生部署（推荐）",
        "backend-only": "仅后端部署",
        "manual": "手动安装",
    }
    print(f"  → {mode_desc.get(mode, mode)}")
    
    print("\n" + "=" * 60)


def parse_args():
    """解析命令行参数。"""
    parser = argparse.ArgumentParser(
        description="RagHubMCP 环境检查工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    parser.add_argument(
        "--json",
        action="store_true",
        help="输出 JSON 格式",
    )
    
    parser.add_argument(
        "--fix",
        action="store_true",
        help="显示修复建议",
    )
    
    parser.add_argument(
        "--port",
        type=int,
        action="append",
        help="检查指定端口（可多次使用）",
    )
    
    return parser.parse_args()


def main():
    """主入口。"""
    args = parse_args()
    
    # 生成报告
    ports = args.port if args.port else None
    report = get_environment_report(ports=ports)
    
    # 添加推荐
    report["recommendation"] = recommend_deployment_mode(report)
    
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print_report(report, show_fix=args.fix)


if __name__ == "__main__":
    main()