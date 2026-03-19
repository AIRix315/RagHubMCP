#!/usr/bin/env python3
"""
RagHubMCP 配置初始化脚本

初始化部署配置文件，支持：
- 交互式选择安装目录
- 生成默认配置
- 预览配置 (--dry-run)
- 强制覆盖 (--force)

配置文件位置：
- Windows: %USERPROFILE%\\.config\\RagHubMCP\\config.json
- macOS/Linux: ~/.config/RagHubMCP/config.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# 添加 lib 目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "lib"))

from config import (
    RagHubConfig,
    PathsConfig,
    PortsConfig,
    DatabaseConfig,
    ModelsConfig,
    get_config_path,
    get_config_dir,
    get_default_schema_url,
    save_config,
    load_config,
    validate_config,
    expand_path,
)


def parse_args():
    """解析命令行参数。"""
    parser = argparse.ArgumentParser(
        description="RagHubMCP 配置初始化工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 交互式初始化
  python init-config.py

  # 指定安装目录
  python init-config.py --install-dir /path/to/RagHubMCP

  # 预览配置（不保存）
  python init-config.py --dry-run

  # 强制覆盖已有配置
  python init-config.py --force
        """
    )
    
    parser.add_argument(
        "--install-dir",
        type=str,
        default=None,
        help="安装目录路径（支持 ~ 和环境变量）"
    )
    
    parser.add_argument(
        "--data-dir",
        type=str,
        default=None,
        help="数据目录路径"
    )
    
    parser.add_argument(
        "--backend-port",
        type=int,
        default=None,
        help="后端API端口"
    )
    
    parser.add_argument(
        "--frontend-port",
        type=int,
        default=None,
        help="前端Web端口"
    )
    
    parser.add_argument(
        "--database-type",
        type=str,
        choices=["chroma", "qdrant"],
        default=None,
        help="向量数据库类型"
    )
    
    parser.add_argument(
        "--model-mode",
        type=str,
        choices=["ollama", "api", "skip"],
        default=None,
        help="模型服务模式"
    )
    
    parser.add_argument(
        "--embedding-model",
        type=str,
        default=None,
        help="Embedding模型名称"
    )
    
    parser.add_argument(
        "--rerank-model",
        type=str,
        default=None,
        help="Rerank模型名称"
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="预览配置（不保存文件）"
    )
    
    parser.add_argument(
        "--force",
        action="store_true",
        help="强制覆盖已存在的配置"
    )
    
    parser.add_argument(
        "--show",
        action="store_true",
        help="显示当前配置"
    )
    
    parser.add_argument(
        "--json",
        action="store_true",
        help="以JSON格式输出"
    )
    
    return parser.parse_args()


def prompt_install_dir() -> str:
    """交互式询问安装目录。"""
    import os
    
    default_dir = "~/RagHubMCP"
    print("\n请选择安装目录:")
    print(f"  [1] {default_dir} (默认)")
    print("  [2] 自定义路径")
    
    try:
        choice = input("请选择 [1-2，默认1]: ").strip()
    except (EOFError, KeyboardInterrupt):
        print("\n已取消")
        sys.exit(0)
    
    if choice == "2":
        try:
            custom_path = input("请输入安装路径: ").strip()
            if custom_path:
                return custom_path
        except (EOFError, KeyboardInterrupt):
            print("\n已取消")
            sys.exit(0)
    
    return default_dir


def create_config(args) -> RagHubConfig:
    """创建配置对象。"""
    # 确定安装目录
    if args.install_dir:
        install_dir = args.install_dir
    elif not args.dry_run and not args.show:
        install_dir = prompt_install_dir()
    else:
        install_dir = "~/RagHubMCP"
    
    # 创建路径配置
    expanded_install = expand_path(install_dir)
    paths = PathsConfig(
        install_dir=str(expanded_install),
        data_dir=str(expanded_install / "data"),
        logs_dir=str(expanded_install / "logs"),
        docker_data_dir=str(expanded_install / "docker-data"),
    )
    
    # 覆盖数据目录（如果指定）
    if args.data_dir:
        paths.data_dir = args.data_dir
    
    # 创建端口配置
    ports = PortsConfig()
    if args.backend_port:
        ports.backend = args.backend_port
    if args.frontend_port:
        ports.frontend = args.frontend_port
    
    # 创建数据库配置
    database = DatabaseConfig(
        type=args.database_type or "chroma",
        persist_dir=str(expanded_install / "data" / "chroma"),
    )
    
    # 创建模型配置
    models = ModelsConfig(
        mode=args.model_mode or "ollama",
        embedding_model=args.embedding_model or "bge-m3",
        rerank_model=args.rerank_model or "ms-marco-MiniLM-L-12-v2",
    )
    
    return RagHubConfig(
        schema=get_default_schema_url(),
        version="1.0",
        paths=paths,
        ports=ports,
        database=database,
        models=models,
    )


def print_config(config: RagHubConfig, as_json: bool = False):
    """打印配置信息。"""
    if as_json:
        print(json.dumps(config.to_dict(), indent=2, ensure_ascii=False))
    else:
        print("\n" + "=" * 50)
        print("RagHubMCP 配置")
        print("=" * 50)
        print(f"\n配置文件: {get_config_path()}")
        print(f"\n[路径配置]")
        for name, path in config.paths.get_resolved_paths().items():
            print(f"  {name}: {path}")
        print(f"\n[端口配置]")
        print(f"  后端API: {config.ports.backend}")
        print(f"  前端Web: {config.ports.frontend}")
        print(f"  Ollama: {config.ports.ollama}")
        print(f"  Qdrant: {config.ports.qdrant}")
        print(f"\n[数据库配置]")
        print(f"  类型: {config.database.type}")
        print(f"  持久化目录: {config.database.persist_dir}")
        print(f"\n[模型配置]")
        print(f"  模式: {config.models.mode}")
        print(f"  Embedding: {config.models.embedding_model}")
        print(f"  Rerank: {config.models.rerank_model}")
        if config.models.llm_model:
            print(f"  LLM: {config.models.llm_model}")
        print()


def main():
    """主入口。"""
    args = parse_args()
    
    config_path = get_config_path()
    
    # 显示当前配置
    if args.show:
        if config_path.exists():
            config = load_config()
            print_config(config, args.json)
        else:
            print("配置文件不存在，请先运行初始化", file=sys.stderr)
            sys.exit(1)
        return
    
    # 创建配置
    config = create_config(args)
    
    # 验证配置
    errors = validate_config(config)
    if errors:
        print("配置验证失败:", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        sys.exit(1)
    
    # 打印配置
    print_config(config, args.json)
    
    # 预览模式
    if args.dry_run:
        print("[预览模式] 配置未保存")
        return
    
    # 检查是否已存在
    if config_path.exists() and not args.force:
        print(f"配置文件已存在: {config_path}")
        print("使用 --force 覆盖现有配置")
        sys.exit(1)
    
    # 保存配置
    saved_path = save_config(config)
    print(f"✓ 配置已保存到: {saved_path}")
    
    # 创建必要的目录
    for name, path in config.paths.get_resolved_paths().items():
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            print(f"✓ 创建目录: {path}")


if __name__ == "__main__":
    main()