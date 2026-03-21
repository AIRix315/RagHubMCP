"""File watcher service for incremental indexing.

This module provides file system monitoring using watchdog:
- Recursive directory watching
- Event handling for created, modified, deleted files
- Debounce support to batch rapid changes
- Thread-safe observer management
"""

from __future__ import annotations

import logging
import threading
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING

from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

if TYPE_CHECKING:
    from watchdog.observers.api import BaseObserver

logger = logging.getLogger(__name__)


class FileEventType(Enum):
    """Types of file events."""

    CREATED = "created"
    MODIFIED = "modified"
    DELETED = "deleted"


@dataclass
class FileEvent:
    """Represents a file system event.

    Attributes:
        event_type: Type of the event (created, modified, deleted).
        path: Absolute path to the affected file.
        is_directory: Whether the event is for a directory.
    """

    event_type: FileEventType
    path: Path
    is_directory: bool = False


@dataclass
class WatcherConfig:
    """Configuration for the file watcher.

    Attributes:
        debounce_seconds: Seconds to wait before processing batched events.
        exclude_dirs: Directory names to exclude from watching.
        file_types: File extensions to watch (empty list = all).
    """

    debounce_seconds: float = 1.0
    exclude_dirs: list[str] = field(
        default_factory=lambda: [
            "node_modules",
            ".git",
            "__pycache__",
            "venv",
            ".venv",
            "dist",
            "build",
        ]
    )
    file_types: list[str] = field(default_factory=lambda: [".py", ".ts", ".js", ".md", ".vue"])


# Type for event callback
EventCallback = Callable[[list[FileEvent]], None]


class DebouncedEventHandler(FileSystemEventHandler):
    """File system event handler with debounce support.

    Batches file events within a debounce window and calls the callback
    with the consolidated list of events.
    """

    def __init__(
        self,
        callback: EventCallback,
        config: WatcherConfig,
    ) -> None:
        """Initialize the event handler.

        Args:
            callback: Function to call with batched events.
            config: Watcher configuration.
        """
        super().__init__()
        self._callback = callback
        self._config = config
        self._pending_events: dict[Path, FileEvent] = {}
        self._lock = threading.Lock()
        self._debounce_timer: threading.Timer | None = None

    def _schedule_callback(self) -> None:
        """Schedule the callback after debounce period."""
        with self._lock:
            if self._debounce_timer is not None:
                self._debounce_timer.cancel()

            self._debounce_timer = threading.Timer(
                self._config.debounce_seconds, self._process_pending_events
            )
            self._debounce_timer.start()

    def _process_pending_events(self) -> None:
        """Process all pending events."""
        with self._lock:
            if not self._pending_events:
                return

            events = list(self._pending_events.values())
            self._pending_events.clear()
            self._debounce_timer = None

        # Call callback outside lock
        try:
            self._callback(events)
        except Exception as e:
            logger.error(f"Error in event callback: {e}")

    def _should_process(self, path: Path) -> bool:
        """Check if the path should be processed.

        Args:
            path: File path to check.

        Returns:
            True if the file should be processed.
        """
        # Skip directories in exclude list
        for part in path.parts:
            if part in self._config.exclude_dirs:
                return False

        # Check file extension
        if self._config.file_types:
            if path.suffix.lower() not in self._config.file_types:
                return False

        return True

    def _add_event(self, event_type: FileEventType, path: Path, is_directory: bool) -> None:
        """Add an event to pending events.

        Args:
            event_type: Type of the event.
            path: File path.
            is_directory: Whether it's a directory.
        """
        if is_directory:
            return  # Skip directory events

        if not self._should_process(path):
            return

        with self._lock:
            # For deleted files, remove any existing modified/created events
            if event_type == FileEventType.DELETED:
                # If file was created and then deleted in same batch, ignore both
                if path in self._pending_events:
                    existing = self._pending_events[path]
                    if existing.event_type == FileEventType.CREATED:
                        del self._pending_events[path]
                        return

                self._pending_events[path] = FileEvent(
                    event_type=event_type, path=path, is_directory=is_directory
                )
            else:
                # For created/modified, update or add
                existing = self._pending_events.get(path)
                if existing is None or existing.event_type == FileEventType.DELETED:
                    # New event or was deleted, treat as created
                    self._pending_events[path] = FileEvent(
                        event_type=FileEventType.CREATED, path=path, is_directory=is_directory
                    )
                else:
                    # Update event
                    self._pending_events[path] = FileEvent(
                        event_type=event_type, path=path, is_directory=is_directory
                    )

        self._schedule_callback()

    def on_created(self, event: FileSystemEvent) -> None:
        """Handle file created event."""
        src_path = event.src_path
        if isinstance(src_path, bytes):
            src_path = src_path.decode("utf-8")
        path = Path(str(src_path)).resolve()
        self._add_event(FileEventType.CREATED, path, event.is_directory)

    def on_modified(self, event: FileSystemEvent) -> None:
        """Handle file modified event."""
        src_path = event.src_path
        if isinstance(src_path, bytes):
            src_path = src_path.decode("utf-8")
        path = Path(str(src_path)).resolve()
        self._add_event(FileEventType.MODIFIED, path, event.is_directory)

    def on_deleted(self, event: FileSystemEvent) -> None:
        """Handle file deleted event."""
        src_path = event.src_path
        if isinstance(src_path, bytes):
            src_path = src_path.decode("utf-8")
        path = Path(str(src_path)).resolve()
        self._add_event(FileEventType.DELETED, path, event.is_directory)


class FileWatcher:
    """File system watcher for incremental indexing.

    Provides:
    - Recursive directory watching
    - Event batching with debounce
    - Thread-safe observer management
    - Start/stop control

    Example:
        >>> config = WatcherConfig(debounce_seconds=1.0)
        >>> def on_events(events):
        ...     for e in events:
        ...         print(f"{e.event_type}: {e.path}")
        >>>
        >>> watcher = FileWatcher(config, on_events)
        >>> watcher.start("/path/to/watch")
        >>> # ... later
        >>> watcher.stop()
    """

    def __init__(
        self,
        config: WatcherConfig,
        on_events: EventCallback,
    ) -> None:
        """Initialize the file watcher.

        Args:
            config: Watcher configuration.
            on_events: Callback function for batched events.
        """
        self._config = config
        self._on_events = on_events
        self._observer: BaseObserver | None = None
        self._watch_path: Path | None = None
        self._running = False
        self._lock = threading.Lock()

    @property
    def is_running(self) -> bool:
        """Check if the watcher is running."""
        return self._running

    @property
    def watch_path(self) -> Path | None:
        """Get the current watch path."""
        return self._watch_path

    def start(self, path: Path | str, recursive: bool = True) -> bool:
        """Start watching a directory.

        Args:
            path: Directory path to watch.
            recursive: Whether to watch subdirectories.

        Returns:
            True if watcher started successfully.
        """
        watch_path = Path(path).resolve()

        with self._lock:
            if self._running:
                logger.warning("Watcher already running")
                return False

            if not watch_path.exists():
                logger.error(f"Path does not exist: {watch_path}")
                return False

            if not watch_path.is_dir():
                logger.error(f"Path is not a directory: {watch_path}")
                return False

            try:
                self._observer = Observer()
                handler = DebouncedEventHandler(self._on_events, self._config)

                self._observer.schedule(handler, str(watch_path), recursive=recursive)
                self._observer.start()

                self._watch_path = watch_path
                self._running = True

                logger.info(f"Started watching: {watch_path} (recursive={recursive})")
                return True

            except Exception as e:
                logger.error(f"Failed to start watcher: {e}")
                self._observer = None
                return False

    def stop(self) -> None:
        """Stop the watcher."""
        with self._lock:
            if not self._running or self._observer is None:
                return

            try:
                self._observer.stop()
                self._observer.join(timeout=5.0)
                logger.info(f"Stopped watching: {self._watch_path}")
            except Exception as e:
                logger.error(f"Error stopping watcher: {e}")
            finally:
                self._observer = None
                self._watch_path = None
                self._running = False

    def __enter__(self) -> FileWatcher:
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.stop()


# Singleton watcher instance for MCP tools
_watcher_instance: FileWatcher | None = None
_watcher_lock = threading.Lock()


def get_watcher(
    config: WatcherConfig | None = None,
    on_events: EventCallback | None = None,
) -> FileWatcher:
    """Get or create the singleton watcher instance.

    Args:
        config: Watcher configuration (required on first call).
        on_events: Event callback (required on first call).

    Returns:
        FileWatcher singleton instance.
    """
    global _watcher_instance

    with _watcher_lock:
        if _watcher_instance is None:
            if config is None:
                config = WatcherConfig()
            if on_events is None:
                # Default no-op callback
                def _no_op_callback(events: list) -> None:
                    """Default no-op event callback."""
                    pass

                on_events = _no_op_callback
            _watcher_instance = FileWatcher(config, on_events)
        return _watcher_instance


def reset_watcher() -> None:
    """Reset the singleton watcher instance (for testing)."""
    global _watcher_instance

    with _watcher_lock:
        if _watcher_instance is not None:
            _watcher_instance.stop()
        _watcher_instance = None
