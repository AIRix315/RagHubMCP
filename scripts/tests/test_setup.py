"""Setup scripts tests for RagHubMCP deployment."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Add scripts to path
_scripts_path = Path(__file__).resolve().parent.parent
if str(_scripts_path) not in sys.path:
    sys.path.insert(0, str(_scripts_path))


class TestSetupOllama:
    """Test Ollama setup script."""
    
    def test_check_ollama_installed_true(self):
        """TC-4.3.1: Ollama检测正确"""
        import importlib.util
        _path = _scripts_path / "setup" / "setup-ollama.py"
        _spec = importlib.util.spec_from_file_location("setup_ollama", _path)
        if _spec is None or _spec.loader is None:
            pytest.skip("Cannot load module")
        module = importlib.util.module_from_spec(_spec)
        _spec.loader.exec_module(module)
        
        result = module.check_ollama_installed()
        assert "installed" in result
    
    def test_check_ollama_running(self):
        """TC-4.3.2: Ollama服务状态检测"""
        import importlib.util
        _path = _scripts_path / "setup" / "setup-ollama.py"
        _spec = importlib.util.spec_from_file_location("setup_ollama", _path)
        if _spec is None or _spec.loader is None:
            pytest.skip("Cannot load module")
        module = importlib.util.module_from_spec(_spec)
        _spec.loader.exec_module(module)
        
        result = module.check_ollama_running(port=11434)
        assert "running" in result


class TestSetupQdrant:
    """Test Qdrant setup script."""
    
    def test_check_qdrant_docker(self):
        """TC-4.3.3: Qdrant Docker状态检测"""
        import importlib.util
        _path = _scripts_path / "setup" / "setup-qdrant.py"
        _spec = importlib.util.spec_from_file_location("setup_qdrant", _path)
        if _spec is None or _spec.loader is None:
            pytest.skip("Cannot load module")
        module = importlib.util.module_from_spec(_spec)
        _spec.loader.exec_module(module)
        
        result = module.check_qdrant_docker()
        assert "installed" in result
        assert "running" in result
    
    def test_check_qdrant_service(self):
        """TC-4.3.4: Qdrant服务状态检测"""
        import importlib.util
        _path = _scripts_path / "setup" / "setup-qdrant.py"
        _spec = importlib.util.spec_from_file_location("setup_qdrant", _path)
        if _spec is None or _spec.loader is None:
            pytest.skip("Cannot load module")
        module = importlib.util.module_from_spec(_spec)
        _spec.loader.exec_module(module)
        
        result = module.check_qdrant_service(port=6333)
        assert "running" in result
    
    def test_get_qdrant_config(self):
        """TC-4.3.5: Qdrant配置读取"""
        import importlib.util
        _path = _scripts_path / "setup" / "setup-qdrant.py"
        _spec = importlib.util.spec_from_file_location("setup_qdrant", _path)
        if _spec is None or _spec.loader is None:
            pytest.skip("Cannot load module")
        module = importlib.util.module_from_spec(_spec)
        _spec.loader.exec_module(module)
        
        result = module.get_qdrant_config()
        assert "port" in result
        assert "persist_dir" in result


class TestSetupChroma:
    """Test Chroma setup script."""
    
    def test_check_chromadb_installed(self):
        """TC-4.3.6: Chroma安装检测"""
        import importlib.util
        _path = _scripts_path / "setup" / "setup-chroma.py"
        _spec = importlib.util.spec_from_file_location("setup_chroma", _path)
        if _spec is None or _spec.loader is None:
            pytest.skip("Cannot load module")
        module = importlib.util.module_from_spec(_spec)
        _spec.loader.exec_module(module)
        
        result = module.check_chromadb_installed()
        assert "installed" in result
    
    def test_get_chroma_config(self):
        """TC-4.3.7: Chroma配置读取"""
        import importlib.util
        _path = _scripts_path / "setup" / "setup-chroma.py"
        _spec = importlib.util.spec_from_file_location("setup_chroma", _path)
        if _spec is None or _spec.loader is None:
            pytest.skip("Cannot load module")
        module = importlib.util.module_from_spec(_spec)
        _spec.loader.exec_module(module)
        
        result = module.get_chroma_config()
        assert "persist_dir" in result
    
    def test_verify_chromadb(self):
        """TC-4.3.8: Chroma功能验证"""
        import importlib.util
        _path = _scripts_path / "setup" / "setup-chroma.py"
        _spec = importlib.util.spec_from_file_location("setup_chroma", _path)
        if _spec is None or _spec.loader is None:
            pytest.skip("Cannot load module")
        module = importlib.util.module_from_spec(_spec)
        _spec.loader.exec_module(module)
        
        import tempfile
        import os
        import gc
        
        tmpdir = tempfile.mkdtemp()
        try:
            result = module.verify_chromadb(tmpdir)
            assert "working" in result
            assert "message" in result
        finally:
            # Force garbage collection to release file handles
            gc.collect()
            # Try to clean up, ignore errors on Windows
            try:
                import shutil
                shutil.rmtree(tmpdir, ignore_errors=True)
            except Exception:
                pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])