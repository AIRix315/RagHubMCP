"""Tests for configuration validation.

Test cases cover:
- TC-CONFIG-001: Port validation (1-65535)
- TC-CONFIG-002: ChromaConfig mode validation
- TC-CONFIG-003: Provider default validation
- TC-CONFIG-004: IndexerConfig chunk_size/overlap validation
- TC-CONFIG-005: HybridConfig weight validation
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from utils.config import (
    ChromaConfig,
    CORSConfig,
    HybridConfig,
    IndexerConfig,
    ProviderCategory,
    ServerConfig,
)


class TestServerConfigValidation:
    """Tests for ServerConfig validation (TC-CONFIG-001)."""

    def test_valid_port(self) -> None:
        """Test valid port numbers."""
        config = ServerConfig(port=8080)
        assert config.port == 8080

        config = ServerConfig(port=1)
        assert config.port == 1

        config = ServerConfig(port=65535)
        assert config.port == 65535

    def test_invalid_port_too_low(self) -> None:
        """Test port below valid range."""
        with pytest.raises(ValidationError, match="greater than or equal to 1"):
            ServerConfig(port=0)

        with pytest.raises(ValidationError, match="greater than or equal to 1"):
            ServerConfig(port=-1)

    def test_invalid_port_too_high(self) -> None:
        """Test port above valid range."""
        with pytest.raises(ValidationError, match="less than or equal to 65535"):
            ServerConfig(port=65536)

        with pytest.raises(ValidationError, match="less than or equal to 65535"):
            ServerConfig(port=100000)


class TestChromaConfigValidation:
    """Tests for ChromaConfig validation (TC-CONFIG-002)."""

    def test_local_mode(self) -> None:
        """Test local mode with persist_dir."""
        config = ChromaConfig(persist_dir="./data/chroma")
        assert config.persist_dir == "./data/chroma"
        assert config.host is None

    def test_remote_mode(self) -> None:
        """Test remote mode with host/port."""
        config = ChromaConfig(host="localhost", port=8000)
        assert config.host == "localhost"
        assert config.port == 8000

    def test_remote_port_validation(self) -> None:
        """Test remote port validation."""
        config = ChromaConfig(host="localhost", port=8000)
        assert config.port == 8000

        with pytest.raises(ValidationError, match="Remote port must be between"):
            ChromaConfig(host="localhost", port=0)

        with pytest.raises(ValidationError, match="Remote port must be between"):
            ChromaConfig(host="localhost", port=70000)


class TestProviderCategoryValidation:
    """Tests for ProviderCategory validation (TC-CONFIG-003)."""

    def test_empty_instances(self) -> None:
        """Test empty instances is valid."""
        config = ProviderCategory(default="", instances=[])
        assert config.default == ""
        assert config.instances == []

    def test_default_exists_in_instances(self) -> None:
        """Test default exists in instances."""
        config = ProviderCategory(
            default="ollama", instances=[{"name": "ollama", "type": "ollama", "model": "nomic"}]
        )
        assert config.default == "ollama"

    def test_default_not_in_instances_raises(self) -> None:
        """Test default not in instances raises error."""
        with pytest.raises(ValidationError, match="Default provider.*not found"):
            ProviderCategory(
                default="unknown",
                instances=[{"name": "ollama", "type": "ollama", "model": "nomic"}],
            )

    def test_default_with_empty_instances_passes(self) -> None:
        """Test default with empty instances passes (no validation needed)."""
        config = ProviderCategory(default="something", instances=[])
        assert config.default == "something"


class TestIndexerConfigValidation:
    """Tests for IndexerConfig validation (TC-CONFIG-004)."""

    def test_valid_chunk_size(self) -> None:
        """Test valid chunk sizes."""
        config = IndexerConfig(chunk_size=500)
        assert config.chunk_size == 500

        config = IndexerConfig(chunk_size=100)  # Need overlap < 100
        assert config.chunk_size == 100

        config = IndexerConfig(chunk_size=10000)
        assert config.chunk_size == 10000

    def test_invalid_chunk_size_too_low(self) -> None:
        """Test chunk size below valid range."""
        with pytest.raises(ValidationError):
            IndexerConfig(chunk_size=49)

        with pytest.raises(ValidationError):
            IndexerConfig(chunk_size=0)

    def test_invalid_chunk_size_too_high(self) -> None:
        """Test chunk size above valid range."""
        with pytest.raises(ValidationError):
            IndexerConfig(chunk_size=10001)

    def test_valid_overlap(self) -> None:
        """Test valid overlap values."""
        config = IndexerConfig(chunk_size=500, chunk_overlap=50)
        assert config.chunk_overlap == 50

        config = IndexerConfig(chunk_size=500, chunk_overlap=0)
        assert config.chunk_overlap == 0

    def test_overlap_less_than_chunk_size(self) -> None:
        """Test overlap must be less than chunk_size."""
        # Valid: overlap < chunk_size
        config = IndexerConfig(chunk_size=500, chunk_overlap=499)
        assert config.chunk_overlap == 499

        # Invalid: overlap >= chunk_size
        with pytest.raises(ValidationError, match="chunk_overlap.*must be less than"):
            IndexerConfig(chunk_size=500, chunk_overlap=500)

        with pytest.raises(ValidationError, match="chunk_overlap.*must be less than"):
            IndexerConfig(chunk_size=500, chunk_overlap=600)

    def test_file_types_validation(self) -> None:
        """Test file types must start with '.'."""
        config = IndexerConfig(file_types=[".py", ".ts"])
        assert config.file_types == [".py", ".ts"]

        with pytest.raises(ValidationError, match="must start with"):
            IndexerConfig(file_types=["py", "ts"])

    def test_max_file_size_validation(self) -> None:
        """Test max file size validation."""
        config = IndexerConfig(max_file_size=1048576)
        assert config.max_file_size == 1048576

        config = IndexerConfig(max_file_size=1)
        assert config.max_file_size == 1

        with pytest.raises(ValidationError):
            IndexerConfig(max_file_size=0)

        with pytest.raises(ValidationError):
            IndexerConfig(max_file_size=200000000)  # Too large


class TestHybridConfigValidation:
    """Tests for HybridConfig validation (TC-CONFIG-005)."""

    def test_valid_weights(self) -> None:
        """Test valid alpha and beta values."""
        config = HybridConfig(alpha=0.5, beta=0.5)
        assert config.alpha == 0.5
        assert config.beta == 0.5

        config = HybridConfig(alpha=0.7, beta=0.3)
        assert config.alpha == 0.7

    def test_weight_sum_validation(self) -> None:
        """Test alpha + beta should roughly sum to 1."""
        # Valid: sum is ~1.0
        config = HybridConfig(alpha=0.5, beta=0.5)
        assert config.alpha + config.beta == 1.0

        # Valid: sum is close to 1.0
        config = HybridConfig(alpha=0.6, beta=0.5)  # 1.1 is acceptable
        assert config.alpha + config.beta == 1.1

        # Invalid: sum is too small
        with pytest.raises(ValidationError, match="alpha \\+ beta"):
            HybridConfig(alpha=0.05, beta=0.02)  # 0.07 is too small

        # Invalid: sum is too large
        with pytest.raises(ValidationError, match="alpha \\+ beta"):
            HybridConfig(alpha=1.0, beta=1.0)  # 2.0 is too large

    def test_rrf_k_validation(self) -> None:
        """Test RRF K constant validation."""
        config = HybridConfig(rrf_k=60)
        assert config.rrf_k == 60

        config = HybridConfig(rrf_k=1)
        assert config.rrf_k == 1

        config = HybridConfig(rrf_k=1000)
        assert config.rrf_k == 1000

        with pytest.raises(ValidationError):
            HybridConfig(rrf_k=0)

        with pytest.raises(ValidationError):
            HybridConfig(rrf_k=1001)


class TestCORSConfigValidation:
    """Tests for CORSConfig validation."""

    def test_default_cors_config(self) -> None:
        """Test default CORS configuration."""
        config = CORSConfig()
        assert "http://localhost:3315" in config.origins
        assert config.allow_credentials is True

    def test_custom_origins(self) -> None:
        """Test custom CORS origins."""
        config = CORSConfig(origins=["https://example.com"])
        assert config.origins == ["https://example.com"]
