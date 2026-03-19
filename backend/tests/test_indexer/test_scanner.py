"""Tests for File Scanner.

Tests cover:
- TC-1.8.1: 扫描单个文件
- TC-1.8.2: 扫描目录递归
- TC-1.8.3: 文件类型过滤
- TC-1.8.4: 排除目录
- TC-1.8.5: 大文件跳过
- TC-1.8.6: 空目录处理
"""

import sys
from pathlib import Path

import pytest

# Add src to path for imports
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))

from src.indexer.scanner import FileInfo, FileScanner
from src.utils.config import IndexerConfig


@pytest.fixture
def scanner_config() -> IndexerConfig:
    """Create a test scanner configuration."""
    return IndexerConfig(
        chunk_size=500,
        chunk_overlap=50,
        max_file_size=1024 * 10,  # 10KB for testing
        file_types=[".py", ".ts", ".js", ".md", ".vue"],
        exclude_dirs=["node_modules", ".git", "__pycache__", "venv"],
    )


@pytest.fixture
def scanner(scanner_config: IndexerConfig) -> FileScanner:
    """Create a FileScanner with test configuration."""
    return FileScanner(config=scanner_config)


class TestFileScanner:
    """FileScanner 测试类"""

    def test_scan_single_file(self, scanner: FileScanner, tmp_path: Path):
        """TC-1.8.1: 扫描单个文件"""
        # 创建测试文件
        test_file = tmp_path / "test.py"
        test_file.write_text("print('hello')")
        
        # 扫描文件
        results = scanner.scan(test_file)
        
        # 验证
        assert len(results) == 1
        assert results[0].path == test_file.resolve()
        assert results[0].size == len("print('hello')")
        assert results[0].modified_time > 0
        assert results[0].content_hash is None  # 默认不计算 hash

    def test_scan_with_hash(self, scanner: FileScanner, tmp_path: Path):
        """扫描文件并计算 hash"""
        test_file = tmp_path / "test.py"
        test_file.write_text("print('hello')")
        
        results = scanner.scan(test_file, compute_hash=True)
        
        assert len(results) == 1
        assert results[0].content_hash is not None
        assert len(results[0].content_hash) == 32  # MD5 hex length

    def test_scan_directory_recursive(self, scanner: FileScanner, tmp_path: Path):
        """TC-1.8.2: 扫描目录递归"""
        # 创建目录结构
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "main.py").write_text("# main")
        (tmp_path / "src" / "utils").mkdir()
        (tmp_path / "src" / "utils" / "helper.py").write_text("# helper")
        (tmp_path / "src" / "utils" / "types.ts").write_text("// types")
        
        # 扫描
        results = scanner.scan(tmp_path)
        
        # 验证 - 应该找到 3 个文件
        assert len(results) == 3
        file_names = {r.path.name for r in results}
        assert "main.py" in file_names
        assert "helper.py" in file_names
        assert "types.ts" in file_names

    def test_file_type_filter(self, scanner: FileScanner, tmp_path: Path):
        """TC-1.8.3: 文件类型过滤"""
        # 创建不同类型文件
        (tmp_path / "app.py").write_text("# python")
        (tmp_path / "index.ts").write_text("// typescript")
        (tmp_path / "config.json").write_text("{}")  # 不在允许列表
        (tmp_path / "readme.md").write_text("# Readme")
        (tmp_path / "style.css").write_text("body {}")  # 不在允许列表
        
        results = scanner.scan(tmp_path)
        
        # 验证 - 只应该有 .py, .ts, .md
        assert len(results) == 3
        extensions = {r.path.suffix for r in results}
        assert extensions == {".py", ".ts", ".md"}
        
        # 验证被跳过的文件
        skipped_names = {s[0].name for s in scanner.skipped_files}
        assert "config.json" in skipped_names
        assert "style.css" in skipped_names

    def test_exclude_dirs(self, scanner: FileScanner, tmp_path: Path):
        """TC-1.8.4: 排除目录"""
        # 创建目录结构
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "main.py").write_text("# main")
        
        # 创建应该被排除的目录
        (tmp_path / "node_modules").mkdir()
        (tmp_path / "node_modules" / "package.py").write_text("# package")
        
        (tmp_path / ".git").mkdir()
        (tmp_path / ".git" / "config.py").write_text("# git config")
        
        (tmp_path / "__pycache__").mkdir()
        (tmp_path / "__pycache__" / "cache.py").write_text("# cache")
        
        results = scanner.scan(tmp_path)
        
        # 验证 - 只应该找到 src/main.py
        assert len(results) == 1
        assert results[0].path.name == "main.py"

    def test_large_file_skipped(self, scanner: FileScanner, tmp_path: Path):
        """TC-1.8.5: 大文件跳过"""
        # 创建小文件
        small_file = tmp_path / "small.py"
        small_file.write_text("x" * 100)  # 100 bytes
        
        # 创建大文件 (超过 10KB 限制)
        large_file = tmp_path / "large.py"
        large_file.write_text("x" * (1024 * 11))  # 11KB
        
        results = scanner.scan(tmp_path)
        
        # 验证 - 只应该有小文件
        assert len(results) == 1
        assert results[0].path.name == "small.py"
        
        # 验证大文件被记录
        skipped = {s[0].name: s[1] for s in scanner.skipped_files}
        assert "large.py" in skipped
        assert "too large" in skipped["large.py"].lower()

    def test_empty_directory(self, scanner: FileScanner, tmp_path: Path):
        """TC-1.8.6: 空目录处理"""
        # 空目录
        results = scanner.scan(tmp_path)
        
        # 验证 - 应该返回空列表
        assert results == []
        assert len(scanner.skipped_files) == 0

    def test_nonexistent_path(self, scanner: FileScanner):
        """扫描不存在的路径"""
        results = scanner.scan("/nonexistent/path/xyz")
        assert results == []

    def test_scan_file_with_invalid_extension(self, scanner: FileScanner, tmp_path: Path):
        """扫描不允许扩展名的文件"""
        test_file = tmp_path / "test.txt"
        test_file.write_text("hello")
        
        results = scanner.scan(test_file)
        
        assert len(results) == 0
        assert len(scanner.skipped_files) == 1

    def test_scan_deeply_nested(self, scanner: FileScanner, tmp_path: Path):
        """扫描深层嵌套目录"""
        # 创建深层目录
        deep_path = tmp_path / "a" / "b" / "c" / "d" / "e"
        deep_path.mkdir(parents=True)
        (deep_path / "deep.py").write_text("# deep")
        
        results = scanner.scan(tmp_path)
        
        assert len(results) == 1
        assert results[0].path.name == "deep.py"

    def test_scan_symlink_to_file(self, scanner: FileScanner, tmp_path: Path):
        """扫描符号链接文件"""
        # 创建真实文件
        real_file = tmp_path / "real.py"
        real_file.write_text("# real")
        
        # 创建符号链接
        link_file = tmp_path / "link.py"
        try:
            link_file.symlink_to(real_file)
            
            results = scanner.scan(tmp_path)
            
            # 符号链接应该被处理
            # 注意：rglob 会跟随符号链接，所以可能会找到
            assert len(results) >= 1
        except OSError:
            # Windows 上可能需要管理员权限创建符号链接
            pytest.skip("Cannot create symlink on this system")

    def test_multiple_scans_clear_skipped(self, scanner: FileScanner, tmp_path: Path):
        """多次扫描应清空上次跳过记录"""
        # 第一次扫描 - 创建大文件
        large_file = tmp_path / "large.py"
        large_file.write_text("x" * (1024 * 11))
        scanner.scan(tmp_path)
        assert len(scanner.skipped_files) == 1
        
        # 第二次扫描 - 创建小文件
        large_file.unlink()
        small_file = tmp_path / "small.py"
        small_file.write_text("x")
        scanner.scan(tmp_path)
        
        # 跳过记录应该被清空
        assert len(scanner.skipped_files) == 0


class TestFileInfo:
    """FileInfo 数据类测试"""

    def test_file_info_creation(self, tmp_path: Path):
        """测试 FileInfo 创建"""
        test_file = tmp_path / "test.py"
        test_file.write_text("hello")
        stat = test_file.stat()
        
        info = FileInfo(
            path=test_file,
            size=stat.st_size,
            modified_time=stat.st_mtime,
            content_hash="abc123"
        )
        
        assert info.path == test_file
        assert info.size == 5
        assert info.modified_time == stat.st_mtime
        assert info.content_hash == "abc123"

    def test_file_info_without_hash(self, tmp_path: Path):
        """测试 FileInfo 不带 hash"""
        test_file = tmp_path / "test.py"
        test_file.write_text("hello")
        stat = test_file.stat()
        
        info = FileInfo(
            path=test_file,
            size=stat.st_size,
            modified_time=stat.st_mtime,
        )
        
        assert info.content_hash is None