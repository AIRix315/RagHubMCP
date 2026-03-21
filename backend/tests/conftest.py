"""Pytest configuration."""

import sys
from pathlib import Path

import pytest

# Add src to path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))


@pytest.fixture
def test_data_dir(tmp_path: Path) -> Path:
    """Create a temporary test data directory."""
    data_dir = tmp_path / "test_data"
    data_dir.mkdir()
    return data_dir


@pytest.fixture
def test_config() -> dict:
    """Return test configuration."""
    return {
        "server": {
            "host": "127.0.0.1",
            "port": 8001,
            "debug": True,
        },
        "chroma": {
            "persist_dir": "./test_data/chroma",
        },
        "providers": {
            "embedding": {
                "default": "test-embedding",
                "instances": [],
            },
            "rerank": {
                "default": "flashrank-tiny",
                "instances": [
                    {
                        "name": "flashrank-tiny",
                        "type": "flashrank",
                        "model": "ms-marco-TinyBERT-L-2-v2",
                    }
                ],
            },
        },
        "indexer": {
            "chunk_size": 500,
            "chunk_overlap": 50,
            "max_file_size": 1048576,
            "file_types": [".py", ".ts", ".js", ".md"],
            "exclude_dirs": ["node_modules", ".git", "__pycache__"],
        },
    }
