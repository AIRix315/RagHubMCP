"""Tests for project initialization (TC-1.1.x)."""

import subprocess
import sys
from pathlib import Path

import pytest


class TestProjectInitialization:
    """TC-1.1.x: 项目初始化测试用例."""

    def test_tc_1_1_1_venv_exists(self):
        """TC-1.1.1: 虚拟环境激活成功."""
        venv_path = Path(__file__).parent.parent / "venv"
        # 检查 venv 目录存在
        assert venv_path.exists(), f"venv directory not found at {venv_path}"
        # 检查 Scripts/Scripts 目录存在 (Windows)
        scripts_path = venv_path / "Scripts"
        assert scripts_path.exists(), f"Scripts directory not found at {scripts_path}"
        # 检查 python 可执行文件
        python_exe = scripts_path / "python.exe"
        assert python_exe.exists(), f"python.exe not found at {python_exe}"

    def test_tc_1_1_2_pip_install_success(self):
        """TC-1.1.2: pip install 无报错."""
        # 检查关键依赖是否已安装
        try:
            import fastapi
            import chromadb
            import flashrank
            import pydantic
            import yaml
        except ImportError as e:
            pytest.fail(f"Dependency import failed: {e}")

    def test_tc_1_1_3_core_modules_import(self):
        """TC-1.1.3: 核心模块导入成功."""
        errors = []

        modules = [
            ("fastapi", "FastAPI"),
            ("chromadb", "ChromaDB"),
            ("flashrank", "FlashRank"),
            ("pydantic", "Pydantic"),
            ("pydantic_settings", "Pydantic Settings"),
            ("yaml", "PyYAML"),
            ("httpx", "HTTPX"),
            ("dotenv", "Python Dotenv"),
        ]

        for module_name, display_name in modules:
            try:
                __import__(module_name)
            except ImportError:
                errors.append(display_name)

        assert not errors, f"Failed to import: {', '.join(errors)}"

    def test_tc_1_1_4_config_load_success(self):
        """TC-1.1.4: 配置文件加载成功."""
        import yaml

        config_path = Path(__file__).parent.parent / "config.yaml"
        assert config_path.exists(), f"config.yaml not found at {config_path}"

        with open(config_path, encoding="utf-8") as f:
            config = yaml.safe_load(f)

        # 验证必要配置项
        assert "server" in config, "Missing 'server' config"
        assert "chroma" in config, "Missing 'chroma' config"
        assert "providers" in config, "Missing 'providers' config"
        assert "indexer" in config, "Missing 'indexer' config"

        # 验证 server 配置
        assert "host" in config["server"], "Missing server.host"
        assert "port" in config["server"], "Missing server.port"

        # 验证 providers 配置
        assert "embedding" in config["providers"], "Missing providers.embedding"
        assert "rerank" in config["providers"], "Missing providers.rerank"


class TestProjectStructure:
    """项目结构测试."""

    def test_backend_structure(self):
        """测试后端目录结构."""
        backend_path = Path(__file__).parent.parent

        required_dirs = [
            "src",
            "src/api",
            "src/mcp",
            "src/mcp/tools",
            "src/providers",
            "src/providers/embedding",
            "src/providers/rerank",
            "src/providers/llm",
            "src/chunkers",
            "src/indexer",
            "src/storage",
            "src/utils",
            "tests",
        ]

        for dir_path in required_dirs:
            full_path = backend_path / dir_path
            assert full_path.exists(), f"Directory not found: {dir_path}"

    def test_required_files_exist(self):
        """测试必要文件存在."""
        backend_path = Path(__file__).parent.parent

        required_files = [
            "pyproject.toml",
            "config.yaml",
            ".env.example",
            "src/__init__.py",
            "tests/__init__.py",
            "tests/conftest.py",
        ]

        for file_path in required_files:
            full_path = backend_path / file_path
            assert full_path.exists(), f"File not found: {file_path}"

    def test_pyproject_toml_valid(self):
        """测试 pyproject.toml 有效."""
        import tomllib

        pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
        with open(pyproject_path, "rb") as f:
            config = tomllib.load(f)

        assert "project" in config, "Missing [project] section"
        assert config["project"]["name"] == "raghub-mcp"
        assert "dependencies" in config["project"]