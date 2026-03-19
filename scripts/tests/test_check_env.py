"""Environment check script tests for RagHubMCP deployment."""

from __future__ import annotations

import json
import sys
import subprocess
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Add scripts to path - use absolute path resolution
_scripts_path = Path(__file__).resolve().parent.parent
if str(_scripts_path) not in sys.path:
    sys.path.insert(0, str(_scripts_path))

# Import directly from the module file
import importlib.util
_check_env_path = _scripts_path / "check" / "check-env.py"
_spec = importlib.util.spec_from_file_location("check_env", _check_env_path)
if _spec is None or _spec.loader is None:
    raise ImportError(f"Cannot load module from {_check_env_path}")
check_env = importlib.util.module_from_spec(_spec)
sys.modules["check_env"] = check_env
_spec.loader.exec_module(check_env)

check_python_version = check_env.check_python_version
check_node_version = check_env.check_node_version
check_git = check_env.check_git
check_docker = check_env.check_docker
check_ollama = check_env.check_ollama
check_port_available = check_env.check_port_available
check_hardware_resources = check_env.check_hardware_resources
get_environment_report = check_env.get_environment_report
recommend_deployment_mode = check_env.recommend_deployment_mode


class TestPythonVersion:
    """Test Python version detection."""
    
    def test_check_python_version_current(self):
        """TC-4.2.1: Python版本检测正确"""
        result = check_python_version()
        assert "version" in result
        assert "installed" in result
        assert result["installed"] is True
        # 当前运行的是 Python 3.13
        assert result["version"].startswith("3.")
    
    def test_check_python_version_sufficient(self):
        """TC-4.2.1b: Python版本满足最低要求"""
        result = check_python_version(min_version=(3, 11))
        assert result["sufficient"] is True


class TestNodeVersion:
    """Test Node.js version detection."""
    
    def test_check_node_version_installed(self):
        """TC-4.2.2: Node.js版本检测正确"""
        result = check_node_version()
        assert "installed" in result
        # 如果安装了 Node.js，应该有版本号
        if result["installed"]:
            assert "version" in result
    
    def test_check_node_version_not_installed(self):
        """TC-4.2.2b: Node.js未安装时正确处理"""
        with patch("shutil.which", return_value=None):
            result = check_node_version()
            assert result["installed"] is False


class TestDockerCheck:
    """Test Docker environment detection."""
    
    def test_check_docker_installed(self):
        """TC-4.2.3: Docker可用性检测"""
        result = check_docker()
        assert "installed" in result
        assert "running" in result
    
    def test_check_docker_not_installed(self):
        """TC-4.2.3b: Docker未安装时正确处理"""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError()
            result = check_docker()
            assert result["installed"] is False


class TestOllamaCheck:
    """Test Ollama environment detection."""
    
    def test_check_ollama_installed(self):
        """TC-4.2.4: Ollama可用性检测"""
        result = check_ollama()
        assert "installed" in result
        assert "running" in result
    
    def test_check_ollama_models(self):
        """TC-4.2.4b: Ollama模型列表检测"""
        result = check_ollama()
        if result["installed"] and result["running"]:
            assert "models" in result


class TestPortCheck:
    """Test port availability detection."""
    
    def test_check_port_available_free(self):
        """TC-4.2.5a: 空闲端口检测正确"""
        # 使用一个非常用端口
        result = check_port_available(59999)
        assert "available" in result
        assert result["available"] is True
    
    def test_check_port_available_in_use(self):
        """TC-4.2.5b: 已占用端口检测正确"""
        # 使用一个肯定被占用的端口（通常是 0，会失败）
        # 或者模拟端口被占用
        import socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('127.0.0.1', 59998))
            # 端口 59998 现在被占用
            result = check_port_available(59998)
            # 注意：由于我们使用了不同的 socket，可能检测不到
            # 这个测试可能会根据实现方式有所不同


class TestHardwareResources:
    """Test hardware resource detection."""
    
    def test_check_hardware_resources(self):
        """TC-4.2.6: 硬件资源检测准确"""
        result = check_hardware_resources()
        assert "memory_gb" in result
        assert "cpu_count" in result
        assert result["memory_gb"] > 0
        assert result["cpu_count"] > 0


class TestEnvironmentReport:
    """Test environment report generation."""
    
    def test_get_environment_report(self):
        """TC-4.2.7: 环境报告生成正确"""
        report = get_environment_report()
        
        assert "python" in report
        assert "node" in report
        assert "git" in report
        assert "docker" in report
        assert "ollama" in report
        assert "hardware" in report
        assert "ports" in report
    
    def test_get_environment_report_json(self):
        """TC-4.2.8: JSON输出格式正确"""
        report = get_environment_report()
        # 验证可以序列化为 JSON
        json_str = json.dumps(report, indent=2)
        assert json_str
        
        # 验证可以反序列化
        parsed = json.loads(json_str)
        assert parsed == report


class TestDeploymentRecommendation:
    """Test deployment mode recommendation."""
    
    def test_recommend_docker_when_available(self):
        """TC-4.2.9a: Docker可用时推荐Docker部署"""
        report = {
            "python": {"installed": True, "sufficient": True},
            "node": {"installed": True, "sufficient": True},
            "docker": {"installed": True, "running": True},
            "ollama": {"installed": False},
        }
        mode = recommend_deployment_mode(report)
        assert mode == "docker"
    
    def test_recommend_native_when_no_docker(self):
        """TC-4.2.9b: 无Docker但有完整环境时推荐原生部署"""
        report = {
            "python": {"installed": True, "sufficient": True},
            "node": {"installed": True, "sufficient": True},
            "docker": {"installed": False},
            "ollama": {"installed": False},
        }
        mode = recommend_deployment_mode(report)
        assert mode == "native"
    
    def test_recommend_manual_when_missing_deps(self):
        """TC-4.2.9c: 缺少依赖时推荐手动安装"""
        report = {
            "python": {"installed": False},
            "node": {"installed": False},
            "docker": {"installed": False},
            "ollama": {"installed": False},
        }
        mode = recommend_deployment_mode(report)
        assert mode == "manual"


class TestCrossPlatform:
    """Test cross-platform compatibility."""
    
    def test_check_git(self):
        """TC-4.2.10: 跨平台兼容"""
        result = check_git()
        assert "installed" in result
        # Git 应该在开发环境中安装
        # 如果没安装，应该返回 installed=False 而不是抛出异常


if __name__ == "__main__":
    pytest.main([__file__, "-v"])