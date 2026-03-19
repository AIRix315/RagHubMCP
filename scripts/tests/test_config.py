"""Configuration module tests for RagHubMCP deployment scripts."""

from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

# Add lib to path - use absolute path resolution
_lib_path = Path(__file__).resolve().parent.parent / "lib"
if str(_lib_path) not in sys.path:
    sys.path.insert(0, str(_lib_path))

# Import from lib.config (not scripts/config)
import lib.config as config_module

RagHubConfig = config_module.RagHubConfig
PathsConfig = config_module.PathsConfig
PortsConfig = config_module.PortsConfig
DatabaseConfig = config_module.DatabaseConfig
ModelsConfig = config_module.ModelsConfig
get_config_dir = config_module.get_config_dir
get_config_path = config_module.get_config_path
expand_path = config_module.expand_path
load_config = config_module.load_config
save_config = config_module.save_config
validate_config = config_module.validate_config
init_default_config = config_module.init_default_config
get_default_schema_url = config_module.get_default_schema_url


class TestConfigDataclasses:
    """Test configuration dataclasses."""
    
    def test_paths_config_defaults(self):
        """TC-4.1.1a: PathsConfig 默认值正确"""
        paths = PathsConfig()
        assert paths.install_dir == "~/RagHubMCP"
        assert paths.data_dir == "~/RagHubMCP/data"
        assert paths.logs_dir == "~/RagHubMCP/logs"
        assert paths.docker_data_dir == "~/RagHubMCP/docker-data"
    
    def test_ports_config_defaults(self):
        """TC-4.1.1b: PortsConfig 默认值正确"""
        ports = PortsConfig()
        assert ports.backend == 8818
        assert ports.frontend == 3315
        assert ports.ollama == 11434
        assert ports.qdrant == 6333
    
    def test_database_config_defaults(self):
        """TC-4.1.1c: DatabaseConfig 默认值正确"""
        db = DatabaseConfig()
        assert db.type == "chroma"
        assert db.persist_dir == "~/RagHubMCP/data/chroma"
    
    def test_models_config_defaults(self):
        """TC-4.1.1d: ModelsConfig 默认值正确"""
        models = ModelsConfig()
        assert models.mode == "ollama"
        assert models.embedding_model == "bge-m3"
        assert models.rerank_model == "ms-marco-MiniLM-L-12-v2"
        assert models.llm_model is None
    
    def test_raghub_config_to_dict(self):
        """TC-4.1.1e: RagHubConfig 序列化正确"""
        config = RagHubConfig(schema=get_default_schema_url())
        data = config.to_dict()
        
        assert "$schema" in data
        assert data["version"] == "1.0"
        assert "paths" in data
        assert "ports" in data
        assert "database" in data
        assert "models" in data
    
    def test_raghub_config_to_dict_no_schema(self):
        """TC-4.1.1e2: RagHubConfig 无 schema 时正确"""
        config = RagHubConfig()
        data = config.to_dict()
        
        assert "$schema" not in data  # 没有 schema 时不应该有这个字段
        assert data["version"] == "1.0"
        assert "paths" in data
    
    def test_raghub_config_from_dict(self):
        """TC-4.1.1f: RagHubConfig 反序列化正确"""
        data = {
            "$schema": "https://example.com/schema.json",
            "version": "1.0",
            "paths": {
                "install_dir": "/custom/path",
                "data_dir": "/custom/path/data",
                "logs_dir": "/custom/path/logs",
                "docker_data_dir": "/custom/path/docker-data",
            },
            "ports": {
                "backend": 9000,
                "frontend": 4000,
                "ollama": 11434,
                "qdrant": 6333,
            },
            "database": {
                "type": "qdrant",
                "persist_dir": "/custom/path/data/qdrant",
            },
            "models": {
                "mode": "api",
                "embedding_model": "text-embedding-3-small",
                "rerank_model": "rerank-english-v3.0",
                "llm_model": "gpt-4",
            },
        }
        
        config = RagHubConfig.from_dict(data)
        
        assert config.schema == "https://example.com/schema.json"
        assert config.paths.install_dir == "/custom/path"
        assert config.ports.backend == 9000
        assert config.database.type == "qdrant"
        assert config.models.mode == "api"
        assert config.models.llm_model == "gpt-4"


class TestPathResolution:
    """Test path resolution functions."""
    
    def test_expand_path_home(self):
        """TC-4.1.2a: ~ 展开为用户目录"""
        # 跳过如果 HOME 未设置
        if not os.environ.get("HOME") and not os.environ.get("USERPROFILE"):
            pytest.skip("HOME/USERPROFILE not set")
        
        result = expand_path("~/test")
        # 结果应该是绝对路径
        assert result.is_absolute()
        assert "test" in str(result)
    
    def test_expand_path_absolute(self):
        """TC-4.1.2b: 绝对路径保持不变"""
        result = expand_path("/absolute/path")
        assert result.is_absolute()
    
    def test_get_config_dir(self):
        """TC-4.1.2c: 配置目录路径正确"""
        config_dir = get_config_dir()
        assert ".config" in str(config_dir)
        assert "RagHubMCP" in str(config_dir)
    
    def test_get_config_path(self):
        """TC-4.1.2d: 配置文件路径正确"""
        config_path = get_config_path()
        assert config_path.name == "config.json"
        assert "RagHubMCP" in str(config_path)


class TestConfigValidation:
    """Test configuration validation."""
    
    def test_validate_valid_config(self):
        """TC-4.1.3a: 有效配置验证通过"""
        config = RagHubConfig()
        errors = validate_config(config)
        assert len(errors) == 0
    
    def test_validate_invalid_port(self):
        """TC-4.1.3b: 无效端口被检测"""
        config = RagHubConfig()
        config.ports.backend = 0  # Invalid port
        errors = validate_config(config)
        assert len(errors) > 0
        assert any("backend" in e for e in errors)
    
    def test_validate_invalid_port_too_high(self):
        """TC-4.1.3c: 超出范围的端口被检测"""
        config = RagHubConfig()
        config.ports.frontend = 70000  # Invalid port
        errors = validate_config(config)
        assert len(errors) > 0
    
    def test_validate_invalid_database_type(self):
        """TC-4.1.3d: 无效数据库类型被检测"""
        config = RagHubConfig()
        config.database.type = "invalid"
        errors = validate_config(config)
        assert len(errors) > 0
        assert any("database" in e.lower() for e in errors)
    
    def test_validate_invalid_model_mode(self):
        """TC-4.1.3e: 无效模型模式被检测"""
        config = RagHubConfig()
        config.models.mode = "invalid"
        errors = validate_config(config)
        assert len(errors) > 0


class TestConfigLoadSave:
    """Test configuration loading and saving."""
    
    def test_save_and_load_config(self):
        """TC-4.1.4a: 配置保存和加载正确"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.json"
            
            # 创建并保存配置
            config = RagHubConfig()
            config.ports.backend = 9000
            save_config(config, config_path)
            
            # 验证文件存在
            assert config_path.exists()
            
            # 加载配置
            loaded = load_config(config_path)
            assert loaded.ports.backend == 9000
    
    def test_load_nonexistent_config(self):
        """TC-4.1.4b: 加载不存在的配置返回默认值"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "nonexistent.json"
            config = load_config(config_path)
            
            # 应该返回默认配置
            assert config.version == "1.0"
            assert config.ports.backend == 8818
    
    def test_save_creates_directory(self):
        """TC-4.1.4c: 保存配置时创建目录"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "subdir" / "config.json"
            
            config = RagHubConfig()
            save_config(config, config_path)
            
            assert config_path.parent.exists()
            assert config_path.exists()


class TestInitDefaultConfig:
    """Test default configuration initialization."""
    
    def test_init_default_config(self):
        """TC-4.1.5a: 初始化默认配置"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.json"
            
            with patch.object(config_module, "get_config_path", return_value=config_path):
                config, created = init_default_config()
                
                assert created is True
                assert config.version == "1.0"
                assert config.schema is not None
    
    def test_init_existing_config_no_force(self):
        """TC-4.1.5b: 配置已存在时不覆盖（无 --force）"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.json"
            
            # 创建初始配置
            initial = RagHubConfig()
            initial.ports.backend = 9000
            save_config(initial, config_path)
            
            with patch.object(config_module, "get_config_path", return_value=config_path):
                config, created = init_default_config(force=False)
                
                assert created is False
                assert config.ports.backend == 9000  # 保持原有值
    
    def test_init_existing_config_with_force(self):
        """TC-4.1.5c: 使用 --force 覆盖已有配置"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.json"
            
            # 创建初始配置
            initial = RagHubConfig()
            initial.ports.backend = 9000
            save_config(initial, config_path)
            
            with patch.object(config_module, "get_config_path", return_value=config_path):
                config, created = init_default_config(force=True)
                
                assert created is True
                assert config.ports.backend == 8818  # 恢复默认值


class TestJSONSchema:
    """Test JSON Schema validation."""
    
    def test_schema_url(self):
        """TC-4.1.6a: Schema URL 正确"""
        url = get_default_schema_url()
        assert "raw.githubusercontent.com" in url
        assert "config.schema.json" in url
    
    def test_config_matches_schema(self):
        """TC-4.1.6b: 配置结构与 Schema 匹配"""
        import jsonschema
        
        # 加载 Schema
        schema_path = Path(__file__).parent.parent.parent / "schemas" / "config.schema.json"
        if not schema_path.exists():
            pytest.skip("Schema file not found")
        
        with open(schema_path, encoding="utf-8") as f:
            schema = json.load(f)
        
        # 创建配置
        config = RagHubConfig()
        data = config.to_dict()
        
        # 验证
        try:
            jsonschema.validate(data, schema)
        except jsonschema.ValidationError as e:
            pytest.fail(f"Config does not match schema: {e.message}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])