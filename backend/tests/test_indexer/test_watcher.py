"""Tests for File Watcher.

Tests cover:
- TC-2.5.1: Watcher initialization
- TC-2.5.2: Start watching directory
- TC-2.5.3: Stop watching
- TC-2.5.4: Event batching with debounce
- TC-2.5.5: File type filtering
- TC-2.5.6: Exclude directories
"""

import sys
import time
from pathlib import Path

import pytest

# Add src to path for imports
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))

from src.indexer.watcher import (
    DebouncedEventHandler,
    FileEvent,
    FileEventType,
    FileWatcher,
    WatcherConfig,
    reset_watcher,
)


@pytest.fixture
def watcher_config() -> WatcherConfig:
    """Create test watcher configuration."""
    return WatcherConfig(
        debounce_seconds=0.1,  # Short for testing
        exclude_dirs=["node_modules", ".git", "__pycache__"],
        file_types=[".py", ".ts", ".js", ".md"],
    )


@pytest.fixture
def captured_events() -> list[list[FileEvent]]:
    """Create a list to capture events."""
    return []


@pytest.fixture
def event_callback(captured_events: list[list[FileEvent]]):
    """Create a callback that captures events."""

    def callback(events: list[FileEvent]) -> None:
        captured_events.append(events)

    return callback


@pytest.fixture
def watcher(
    watcher_config: WatcherConfig,
    event_callback,
) -> FileWatcher:
    """Create a FileWatcher instance for testing."""
    return FileWatcher(watcher_config, event_callback)


class TestWatcherConfig:
    """WatcherConfig 测试类"""

    def test_default_config(self):
        """测试默认配置"""
        config = WatcherConfig()

        assert config.debounce_seconds == 1.0
        assert "node_modules" in config.exclude_dirs
        assert ".py" in config.file_types

    def test_custom_config(self):
        """测试自定义配置"""
        config = WatcherConfig(
            debounce_seconds=2.0,
            exclude_dirs=["custom"],
            file_types=[".custom"],
        )

        assert config.debounce_seconds == 2.0
        assert config.exclude_dirs == ["custom"]
        assert config.file_types == [".custom"]


class TestFileEvent:
    """FileEvent 测试类"""

    def test_file_event_creation(self, tmp_path: Path):
        """测试 FileEvent 创建"""
        event = FileEvent(
            event_type=FileEventType.CREATED,
            path=tmp_path / "test.py",
            is_directory=False,
        )

        assert event.event_type == FileEventType.CREATED
        assert event.path == tmp_path / "test.py"
        assert event.is_directory is False

    def test_file_event_types(self):
        """测试事件类型枚举"""
        assert FileEventType.CREATED.value == "created"
        assert FileEventType.MODIFIED.value == "modified"
        assert FileEventType.DELETED.value == "deleted"


class TestDebouncedEventHandler:
    """DebouncedEventHandler 测试类"""

    def test_event_handler_creation(
        self,
        watcher_config: WatcherConfig,
        event_callback,
    ):
        """测试事件处理器创建"""
        handler = DebouncedEventHandler(event_callback, watcher_config)

        assert handler._config == watcher_config

    def test_should_process_file(
        self,
        watcher_config: WatcherConfig,
        event_callback,
        tmp_path: Path,
    ):
        """测试文件处理判断"""
        handler = DebouncedEventHandler(event_callback, watcher_config)

        # Should process .py file
        assert handler._should_process(tmp_path / "test.py") is True

        # Should not process .txt file (not in file_types)
        assert handler._should_process(tmp_path / "test.txt") is False

        # Should not process file in excluded dir
        assert handler._should_process(tmp_path / "node_modules" / "test.py") is False

    def test_add_event(
        self,
        watcher_config: WatcherConfig,
        event_callback,
        captured_events: list[list[FileEvent]],
        tmp_path: Path,
    ):
        """测试添加事件"""
        handler = DebouncedEventHandler(event_callback, watcher_config)

        handler._add_event(FileEventType.CREATED, tmp_path / "test.py", is_directory=False)

        # Wait for debounce
        time.sleep(0.2)

        assert len(captured_events) == 1
        assert len(captured_events[0]) == 1
        assert captured_events[0][0].event_type == FileEventType.CREATED

    def test_event_consolidation(
        self,
        watcher_config: WatcherConfig,
        event_callback,
        captured_events: list[list[FileEvent]],
        tmp_path: Path,
    ):
        """测试事件合并（创建后删除）"""
        handler = DebouncedEventHandler(event_callback, watcher_config)

        # Add created event
        handler._add_event(FileEventType.CREATED, tmp_path / "test.py", is_directory=False)

        # Immediately add deleted event (should cancel out)
        handler._add_event(FileEventType.DELETED, tmp_path / "test.py", is_directory=False)

        # Wait for debounce
        time.sleep(0.2)

        # Should have no events (created + deleted = nothing)
        assert len(captured_events) == 0


class TestFileWatcher:
    """FileWatcher 测试类"""

    def test_watcher_creation(
        self,
        watcher: FileWatcher,
        watcher_config: WatcherConfig,
    ):
        """TC-2.5.1: Watcher 初始化"""
        assert watcher._config == watcher_config
        assert watcher.is_running is False
        assert watcher.watch_path is None

    def test_start_watching(
        self,
        watcher: FileWatcher,
        tmp_path: Path,
    ):
        """TC-2.5.2: 开始监听目录"""
        # Create a directory to watch
        watch_dir = tmp_path / "watch_test"
        watch_dir.mkdir()

        result = watcher.start(watch_dir)

        assert result is True
        assert watcher.is_running is True
        assert watcher.watch_path == watch_dir.resolve()

    def test_stop_watching(
        self,
        watcher: FileWatcher,
        tmp_path: Path,
    ):
        """TC-2.5.3: 停止监听"""
        watch_dir = tmp_path / "watch_test"
        watch_dir.mkdir()

        watcher.start(watch_dir)
        assert watcher.is_running is True

        watcher.stop()

        assert watcher.is_running is False
        assert watcher.watch_path is None

    def test_start_nonexistent_path(
        self,
        watcher: FileWatcher,
    ):
        """测试监听不存在的路径"""
        result = watcher.start("/nonexistent/path/xyz")

        assert result is False
        assert watcher.is_running is False

    def test_start_file_path(
        self,
        watcher: FileWatcher,
        tmp_path: Path,
    ):
        """测试监听文件（非目录）"""
        file_path = tmp_path / "test.py"
        file_path.write_text("test")

        result = watcher.start(file_path)

        assert result is False
        assert watcher.is_running is False

    def test_double_start(
        self,
        watcher: FileWatcher,
        tmp_path: Path,
    ):
        """测试重复启动"""
        watch_dir = tmp_path / "watch_test"
        watch_dir.mkdir()

        watcher.start(watch_dir)
        result = watcher.start(tmp_path / "another")

        assert result is False
        assert watcher.is_running is True

    def test_context_manager(
        self,
        watcher_config: WatcherConfig,
        event_callback,
        tmp_path: Path,
    ):
        """测试上下文管理器"""
        watch_dir = tmp_path / "watch_test"
        watch_dir.mkdir()

        with FileWatcher(watcher_config, event_callback) as w:
            w.start(watch_dir)
            assert w.is_running is True

        # Should stop on exit
        assert w.is_running is False

    def test_recursive_watching(
        self,
        watcher: FileWatcher,
        tmp_path: Path,
        captured_events: list[list[FileEvent]],
    ):
        """TC-2.5.4: 递归监听"""
        watch_dir = tmp_path / "watch_test"
        watch_dir.mkdir()
        nested_dir = watch_dir / "nested"
        nested_dir.mkdir()

        watcher.start(watch_dir, recursive=True)

        # Create a file in nested directory
        test_file = nested_dir / "test.py"
        test_file.write_text("test")

        # Wait for debounce
        time.sleep(0.3)

        # Should have captured the event
        assert len(captured_events) >= 1

    def test_exclude_directories(
        self,
        watcher: FileWatcher,
        tmp_path: Path,
        captured_events: list[list[FileEvent]],
    ):
        """TC-2.5.6: 排除目录"""
        watch_dir = tmp_path / "watch_test"
        watch_dir.mkdir()

        # Create excluded directory
        excluded_dir = watch_dir / "node_modules"
        excluded_dir.mkdir()

        watcher.start(watch_dir)

        # Create file in excluded directory
        excluded_file = excluded_dir / "test.py"
        excluded_file.write_text("test")

        # Wait for debounce
        time.sleep(0.3)

        # Should not have captured the event
        all_events = [e for batch in captured_events for e in batch]
        excluded_events = [e for e in all_events if "node_modules" in str(e.path)]
        assert len(excluded_events) == 0


class TestSingleton:
    """单例模式测试"""

    def teardown_method(self):
        """Clean up after each test."""
        reset_watcher()

    def test_get_watcher_singleton(self):
        """测试单例获取"""
        from src.indexer.watcher import get_watcher

        config = WatcherConfig(debounce_seconds=0.5)
        watcher1 = get_watcher(config, lambda events: None)
        watcher2 = get_watcher()

        assert watcher1 is watcher2

    def test_reset_watcher(self):
        """测试重置单例"""
        from src.indexer.watcher import get_watcher

        watcher1 = get_watcher(WatcherConfig(), lambda events: None)
        reset_watcher()
        watcher2 = get_watcher(WatcherConfig(), lambda events: None)

        assert watcher1 is not watcher2
