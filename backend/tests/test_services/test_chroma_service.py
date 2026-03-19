"""Tests for ChromaService.

Tests cover:
- TC-SVC-1: Singleton pattern
- TC-SVC-2: Collection creation
- TC-SVC-3: Collection retrieval
- TC-SVC-4: Persistence
"""

import sys
from pathlib import Path

import pytest

# Add src to path for imports
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))

from src.services.chroma_service import (
    ChromaService,
    get_chroma_service,
    reset_chroma_service,
)


class TestChromaService:
    """ChromaService 测试类"""

    def test_create_service(self, tmp_path: Path):
        """TC-SVC-1: 创建服务实例"""
        reset_chroma_service()
        
        persist_dir = tmp_path / "chroma"
        service = ChromaService(persist_dir=str(persist_dir))
        
        assert service.persist_dir == str(persist_dir)
        assert service._client is None  # Lazy initialization

    def test_get_client_lazy_init(self, tmp_path: Path):
        """测试客户端延迟初始化"""
        reset_chroma_service()
        
        persist_dir = tmp_path / "chroma"
        service = ChromaService(persist_dir=str(persist_dir))
        
        # Client is None initially
        assert service._client is None
        
        # Accessing client triggers initialization
        client = service.client
        assert client is not None
        assert service._client is not None
        
        # Subsequent access returns same instance
        client2 = service.client
        assert client is client2

    def test_get_or_create_collection(self, tmp_path: Path):
        """TC-SVC-2: 创建 collection"""
        reset_chroma_service()
        
        persist_dir = tmp_path / "chroma"
        service = ChromaService(persist_dir=str(persist_dir))
        
        # Use use_embedding=False for tests without embedding provider
        collection = service.get_or_create_collection("test_collection", use_embedding=False)
        
        assert collection is not None
        assert collection.name == "test_collection"

    def test_get_existing_collection(self, tmp_path: Path):
        """TC-SVC-3: 获取已存在的 collection"""
        reset_chroma_service()
        
        persist_dir = tmp_path / "chroma"
        service = ChromaService(persist_dir=str(persist_dir))
        
        # Create collection
        service.get_or_create_collection("existing_collection", use_embedding=False)
        
        # Get the same collection
        collection = service.get_collection("existing_collection")
        
        assert collection.name == "existing_collection"

    def test_list_collections(self, tmp_path: Path):
        """测试列出 collections"""
        reset_chroma_service()
        
        persist_dir = tmp_path / "chroma"
        service = ChromaService(persist_dir=str(persist_dir))
        
        # Create multiple collections
        service.get_or_create_collection("collection_1", use_embedding=False)
        service.get_or_create_collection("collection_2", use_embedding=False)
        
        collections = service.list_collections()
        
        assert len(collections) == 2
        names = {c.name for c in collections}
        assert "collection_1" in names
        assert "collection_2" in names

    def test_delete_collection(self, tmp_path: Path):
        """测试删除 collection"""
        reset_chroma_service()
        
        persist_dir = tmp_path / "chroma"
        service = ChromaService(persist_dir=str(persist_dir))
        
        # Create and delete
        service.get_or_create_collection("to_delete", use_embedding=False)
        service.delete_collection("to_delete")
        
        # Verify deletion
        collections = service.list_collections()
        names = {c.name for c in collections}
        assert "to_delete" not in names

    def test_singleton_pattern(self, tmp_path: Path):
        """TC-SVC-4: 单例模式"""
        reset_chroma_service()
        
        persist_dir = tmp_path / "chroma"
        
        service1 = get_chroma_service(str(persist_dir))
        service2 = get_chroma_service()  # No persist_dir needed
        
        assert service1 is service2

    def test_singleton_reset(self, tmp_path: Path):
        """测试单例重置"""
        reset_chroma_service()
        
        persist_dir1 = tmp_path / "chroma1"
        service1 = get_chroma_service(str(persist_dir1))
        
        # Reset
        reset_chroma_service()
        
        # New instance with different path
        persist_dir2 = tmp_path / "chroma2"
        service2 = get_chroma_service(str(persist_dir2))
        
        assert service1 is not service2
        assert service1.persist_dir != service2.persist_dir

    def test_persist_dir_created(self, tmp_path: Path):
        """测试持久化目录自动创建"""
        reset_chroma_service()
        
        persist_dir = tmp_path / "nested" / "chroma"
        assert not persist_dir.exists()
        
        service = ChromaService(persist_dir=str(persist_dir))
        _ = service.client  # Trigger initialization
        
        assert persist_dir.exists()

    def test_get_chroma_service_with_persist_dir(self, tmp_path: Path):
        """测试首次调用提供 persist_dir"""
        reset_chroma_service()
        
        persist_dir = tmp_path / "chroma"
        service = get_chroma_service(str(persist_dir))
        
        assert service is not None
        assert service.persist_dir == str(persist_dir)