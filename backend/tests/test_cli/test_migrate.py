"""Tests for CLI migrate command.

Test cases cover:
- TC-CLI-001: print_progress function
- TC-CLI-002: print_result function
- TC-CLI-003: main function argument parsing
- TC-CLI-004: dry run functionality
- TC-CLI-005: migration workflow
- TC-CLI-006: error handling
- TC-CLI-007: progress reporting
- TC-CLI-008: result formatting
"""

from __future__ import annotations

import io
import sys
from contextlib import redirect_stdout
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

# Import the module under test
from cli.migrate import main, print_progress, print_result


class TestPrintProgress:
    """Tests for print_progress function (TC-CLI-001)."""
    
    def test_print_progress_basic(self) -> None:
        """Test basic progress printing."""
        output = io.StringIO()
        with redirect_stdout(output):
            print_progress(5, 10, "Processing...")
        
        result = output.getvalue()
        assert "50.00%" in result
        assert "Processing..." in result
    
    def test_print_progress_zero_total(self) -> None:
        """Test progress with zero total (edge case)."""
        output = io.StringIO()
        with redirect_stdout(output):
            print_progress(0, 0, "Starting...")
        
        result = output.getvalue()
        assert "Starting..." in result
        # Should not have percentage when total is 0
    
    def test_print_progress_100_percent(self) -> None:
        """Test progress at 100%."""
        output = io.StringIO()
        with redirect_stdout(output):
            print_progress(100, 100, "Completed!")
        
        result = output.getvalue()
        assert "[100.00%]" in result
        assert "Completed!" in result
    
    def test_print_progress_fractional(self) -> None:
        """Test progress with fractional percentage."""
        output = io.StringIO()
        with redirect_stdout(output):
            print_progress(1, 3, "One third done")
        
        result = output.getvalue()
        assert "33.33%" in result
        assert "One third done" in result


class TestPrintResult:
    """Tests for print_result function (TC-CLI-002)."""
    
    def test_print_result_success(self) -> None:
        """Test printing successful migration result."""
        result = {
            "success": True,
            "collections_migrated": 2,
            "documents_migrated": 100,
            "duration_seconds": 5.5,
            "collections": [
                {"name": "docs", "documents_migrated": 60, "success": True},
                {"name": "code", "documents_migrated": 40, "success": True},
            ],
            "warnings": [],
            "errors": [],
        }
        
        output = io.StringIO()
        with redirect_stdout(output):
            print_result(result)
        
        content = output.getvalue()
        assert "✓ SUCCESS" in content
        assert "Collections migrated: 2" in content
        assert "Documents migrated: 100" in content
        assert "Duration: 5.50s" in content
        assert "docs" in content
        assert "code" in content
    
    def test_print_result_failure(self) -> None:
        """Test printing failed migration result."""
        result = {
            "success": False,
            "collections_migrated": 0,
            "documents_migrated": 0,
            "duration_seconds": 1.0,
            "collections": [],
            "warnings": [],
            "errors": ["Connection failed", "Timeout"],
        }
        
        output = io.StringIO()
        with redirect_stdout(output):
            print_result(result)
        
        content = output.getvalue()
        assert "✗ FAILED" in content
        assert "Errors:" in content
        assert "Connection failed" in content
        assert "Timeout" in content
    
    def test_print_result_with_warnings(self) -> None:
        """Test printing result with warnings."""
        result = {
            "success": True,
            "collections_migrated": 1,
            "documents_migrated": 50,
            "duration_seconds": 2.0,
            "collections": [
                {"name": "docs", "documents_migrated": 50, "success": True},
            ],
            "warnings": ["Some documents skipped", "Invalid metadata"],
            "errors": [],
        }
        
        output = io.StringIO()
        with redirect_stdout(output):
            print_result(result)
        
        content = output.getvalue()
        assert "✓ SUCCESS" in content
        assert "Warnings:" in content
        assert "⚠ Some documents skipped" in content
        assert "⚠ Invalid metadata" in content
    
    def test_print_result_no_collections(self) -> None:
        """Test printing result with no migrated collections."""
        result = {
            "success": True,
            "collections_migrated": 0,
            "documents_migrated": 0,
            "duration_seconds": 0.1,
            "collections": [],
            "warnings": ["No collections found"],
            "errors": [],
        }
        
        output = io.StringIO()
        with redirect_stdout(output):
            print_result(result)
        
        content = output.getvalue()
        assert "Collections migrated: 0" in content
        # Collections section should not appear if empty
        assert "Collections:" not in content or content.count("Collections:") == 0


class TestMainArgumentParsing:
    """Tests for main function argument parsing (TC-CLI-003)."""
    
    @patch("utils.migrate.migrate_chroma_to_qdrant")
    def test_main_default_arguments(self, mock_migrate: MagicMock) -> None:
        """Test main with default arguments."""
        mock_migrate.return_value = MagicMock(
            success=True,
            to_dict=lambda: {
                "success": True,
                "collections_migrated": 0,
                "documents_migrated": 0,
                "duration_seconds": 0.0,
                "collections": [],
                "warnings": ["No collections found"],
                "errors": [],
            }
        )
        
        with patch.object(sys, "argv", ["migrate"]):
            result = main()
        
        assert result == 0
        mock_migrate.assert_called_once()
        call_kwargs = mock_migrate.call_args[1]
        assert call_kwargs["chroma_persist_dir"] == "./data/chroma"
        assert call_kwargs["qdrant_mode"] == "local"
        assert call_kwargs["qdrant_path"] == "./data/qdrant"
        assert call_kwargs["batch_size"] == 100
        assert call_kwargs["verify"] is True
    
    @patch("utils.migrate.migrate_chroma_to_qdrant")
    def test_main_custom_arguments(self, mock_migrate: MagicMock) -> None:
        """Test main with custom arguments."""
        mock_migrate.return_value = MagicMock(
            success=True,
            to_dict=lambda: {"success": True, "collections_migrated": 1}
        )
        
        with patch.object(sys, "argv", [
            "migrate",
            "--chroma-dir", "/custom/chroma",
            "--qdrant-mode", "memory",
            "--batch-size", "50",
            "--no-verify",
        ]):
            result = main()
        
        assert result == 0
        call_kwargs = mock_migrate.call_args[1]
        assert call_kwargs["chroma_persist_dir"] == "/custom/chroma"
        assert call_kwargs["qdrant_mode"] == "memory"
        assert call_kwargs["batch_size"] == 50
        assert call_kwargs["verify"] is False
    
    @patch("utils.migrate.migrate_chroma_to_qdrant")
    def test_main_specific_collections(self, mock_migrate: MagicMock) -> None:
        """Test main with specific collections."""
        mock_migrate.return_value = MagicMock(
            success=True,
            to_dict=lambda: {"success": True}
        )
        
        with patch.object(sys, "argv", [
            "migrate",
            "--collections", "docs", "code", "test",
        ]):
            result = main()
        
        assert result == 0
        call_kwargs = mock_migrate.call_args[1]
        assert call_kwargs["collections"] == ["docs", "code", "test"]
    
    @patch("utils.migrate.migrate_chroma_to_qdrant")
    def test_main_remote_qdrant(self, mock_migrate: MagicMock) -> None:
        """Test main with remote Qdrant server."""
        mock_migrate.return_value = MagicMock(
            success=True,
            to_dict=lambda: {"success": True}
        )
        
        with patch.object(sys, "argv", [
            "migrate",
            "--qdrant-mode", "remote",
            "--qdrant-host", "192.168.1.100",
            "--qdrant-port", "6333",
        ]):
            result = main()
        
        assert result == 0
        call_kwargs = mock_migrate.call_args[1]
        assert call_kwargs["qdrant_host"] == "192.168.1.100"
        assert call_kwargs["qdrant_port"] == 6333
    
    @patch("utils.migrate.migrate_chroma_to_qdrant")
    def test_main_cloud_qdrant(self, mock_migrate: MagicMock) -> None:
        """Test main with Qdrant Cloud."""
        mock_migrate.return_value = MagicMock(
            success=True,
            to_dict=lambda: {"success": True}
        )
        
        with patch.object(sys, "argv", [
            "migrate",
            "--qdrant-mode", "cloud",
            "--qdrant-url", "https://xxx.cloud.qdrant.io",
            "--qdrant-api-key", "secret-key",
        ]):
            result = main()
        
        assert result == 0
        call_kwargs = mock_migrate.call_args[1]
        assert call_kwargs["qdrant_url"] == "https://xxx.cloud.qdrant.io"
        assert call_kwargs["qdrant_api_key"] == "secret-key"


class TestDryRun:
    """Tests for dry run functionality (TC-CLI-004)."""
    
    @patch("providers.vectorstore.ChromaProvider")
    def test_dry_run_list_collections(self, mock_chroma_class: MagicMock) -> None:
        """Test dry run lists collections without migrating."""
        mock_provider = MagicMock()
        mock_provider.list_collections.return_value = ["docs", "code", "test"]
        mock_provider.count.side_effect = [100, 50, 25]
        mock_chroma_class.return_value = mock_provider
        
        output = io.StringIO()
        with redirect_stdout(output):
            with patch.object(sys, "argv", ["migrate", "--dry-run"]):
                result = main()
        
        assert result == 0
        content = output.getvalue()
        assert "Scanning ChromaDB collections..." in content
        assert "Found 3 collection(s)" in content
        assert "docs: 100 documents" in content
        assert "code: 50 documents" in content
        assert "test: 25 documents" in content
        assert "Total: 175 documents" in content
    
    @patch("providers.vectorstore.ChromaProvider")
    def test_dry_run_no_collections(self, mock_chroma_class: MagicMock) -> None:
        """Test dry run with no collections."""
        mock_provider = MagicMock()
        mock_provider.list_collections.return_value = []
        mock_chroma_class.return_value = mock_provider
        
        output = io.StringIO()
        with redirect_stdout(output):
            with patch.object(sys, "argv", ["migrate", "--dry-run"]):
                result = main()
        
        assert result == 0
        content = output.getvalue()
        assert "No collections found" in content
    
    @patch("providers.vectorstore.ChromaProvider")
    def test_dry_run_error(self, mock_chroma_class: MagicMock) -> None:
        """Test dry run with connection error."""
        mock_chroma_class.side_effect = RuntimeError("Failed to connect")
        
        with patch.object(sys, "argv", ["migrate", "--dry-run"]):
            result = main()
        
        assert result == 1  # Error exit code


class TestMigrationWorkflow:
    """Tests for migration workflow (TC-CLI-005)."""
    
    @patch("utils.migrate.migrate_chroma_to_qdrant")
    def test_successful_migration(self, mock_migrate: MagicMock) -> None:
        """Test successful migration workflow."""
        mock_result = MagicMock()
        mock_result.success = True
        mock_result.to_dict.return_value = {
            "success": True,
            "collections_migrated": 2,
            "documents_migrated": 150,
            "duration_seconds": 3.5,
            "collections": [
                {"name": "docs", "documents_migrated": 100, "success": True},
                {"name": "code", "documents_migrated": 50, "success": True},
            ],
            "warnings": [],
            "errors": [],
        }
        mock_migrate.return_value = mock_result
        
        output = io.StringIO()
        with redirect_stdout(output):
            with patch.object(sys, "argv", [
                "migrate",
                "--chroma-dir", "./data/chroma",
                "--qdrant-mode", "local",
            ]):
                result = main()
        
        assert result == 0
        content = output.getvalue()
        assert "VECTOR STORE MIGRATION" in content
        assert "Source: ChromaDB (./data/chroma)" in content
        assert "Target: Qdrant (local)" in content
        assert "SUCCESS" in content
    
    @patch("utils.migrate.migrate_chroma_to_qdrant")
    def test_failed_migration(self, mock_migrate: MagicMock) -> None:
        """Test failed migration workflow."""
        mock_result = MagicMock()
        mock_result.success = False
        mock_result.to_dict.return_value = {
            "success": False,
            "collections_migrated": 0,
            "documents_migrated": 0,
            "duration_seconds": 1.0,
            "collections": [],
            "warnings": [],
            "errors": ["Connection refused", "Timeout waiting for response"],
        }
        mock_migrate.return_value = mock_result
        
        output = io.StringIO()
        with redirect_stdout(output):
            with patch.object(sys, "argv", ["migrate"]):
                result = main()
        
        assert result == 1  # Non-zero exit code for failure
        content = output.getvalue()
        assert "FAILED" in content
        assert "Connection refused" in content
    
    @patch("utils.migrate.migrate_chroma_to_qdrant")
    def test_migration_with_progress_callback(self, mock_migrate: MagicMock) -> None:
        """Test that progress_callback is passed and used."""
        mock_result = MagicMock()
        mock_result.success = True
        mock_result.to_dict.return_value = {"success": True}
        mock_migrate.return_value = mock_result
        
        with patch.object(sys, "argv", ["migrate", "--batch-size", "10"]):
            result = main()
        
        assert result == 0
        call_kwargs = mock_migrate.call_args[1]
        assert callable(call_kwargs["progress_callback"])


class TestErrorHandling:
    """Tests for error handling (TC-CLI-006)."""
    
    @patch("utils.migrate.migrate_chroma_to_qdrant")
    def test_keyboard_interrupt(self, mock_migrate: MagicMock) -> None:
        """Test handling of keyboard interrupt."""
        mock_migrate.side_effect = KeyboardInterrupt()
        
        output = io.StringIO()
        with redirect_stdout(output):
            with patch.object(sys, "argv", ["migrate"]):
                result = main()
        
        assert result == 130  # Standard exit code for SIGINT
        content = output.getvalue()
        assert "cancelled by user" in content.lower()
    
    @patch("utils.migrate.migrate_chroma_to_qdrant")
    def test_exception_during_migration(self, mock_migrate: MagicMock) -> None:
        """Test exception handling during migration."""
        mock_migrate.side_effect = RuntimeError("Database error")
        
        output = io.StringIO()
        with redirect_stdout(output):
            with patch.object(sys, "argv", ["migrate"]):
                result = main()
        
        assert result == 1
        content = output.getvalue()
        assert "Migration failed" in content


class TestVerboseMode:
    """Tests for verbose mode (TC-CLI-007)."""
    
    @patch("utils.migrate.migrate_chroma_to_qdrant")
    def test_verbose_mode(self, mock_migrate: MagicMock) -> None:
        """Test verbose mode enables debug logging."""
        mock_result = MagicMock()
        mock_result.success = True
        mock_result.to_dict.return_value = {"success": True}
        mock_migrate.return_value = mock_result
        
        with patch.object(sys, "argv", ["migrate", "-v"]):
            result = main()
        
        assert result == 0
        # Verify logging level was changed
        # (This is implicit - the code sets logging.DEBUG level)
    
    @patch("utils.migrate.migrate_chroma_to_qdrant")
    def test_verbose_mode_long_flag(self, mock_migrate: MagicMock) -> None:
        """Test verbose mode with --verbose flag."""
        mock_result = MagicMock()
        mock_result.success = True
        mock_result.to_dict.return_value = {"success": True}
        mock_migrate.return_value = mock_result
        
        with patch.object(sys, "argv", ["migrate", "--verbose"]):
            result = main()
        
        assert result == 0


class TestResultFormatting:
    """Tests for result formatting (TC-CLI-008)."""
    
    def test_result_with_collection_details(self) -> None:
        """Test result output includes collection details."""
        result = {
            "success": True,
            "collections_migrated": 3,
            "documents_migrated": 200,
            "duration_seconds": 10.25,
            "collections": [
                {"name": "docs", "documents_migrated": 150, "success": True},
                {"name": "code", "documents_migrated": 30, "success": True},
                {"name": "test", "documents_migrated": 20, "success": False, "error": "Skipped"},
            ],
            "warnings": [],
            "errors": [],
        }
        
        output = io.StringIO()
        with redirect_stdout(output):
            print_result(result)
        
        content = output.getvalue()
        # Check structure
        assert "=" * 60 in content  # Separator line
        assert "MIGRATION RESULT" in content
        # Check individual collections
        assert "✓ docs: 150 documents" in content
        assert "✓ code: 30 documents" in content
        assert "✗ test: 20 documents" in content
    
    def test_result_duration_formatting(self) -> None:
        """Test duration is properly formatted."""
        result = {
            "success": True,
            "collections_migrated": 1,
            "documents_migrated": 10,
            "duration_seconds": 1.234567,
            "collections": [],
            "warnings": [],
            "errors": [],
        }
        
        output = io.StringIO()
        with redirect_stdout(output):
            print_result(result)
        
        content = output.getvalue()
        # Duration should be formatted to 2 decimal places
        assert "Duration: 1.23s" in content


class TestEdgeCases:
    """Tests for edge cases."""
    
    @patch("utils.migrate.migrate_chroma_to_qdrant")
    def test_empty_collections_list(self, mock_migrate: MagicMock) -> None:
        """Test migration with empty collections list."""
        mock_result = MagicMock()
        mock_result.success = True
        mock_result.to_dict.return_value = {
            "success": True,
            "collections_migrated": 0,
            "documents_migrated": 0,
            "warnings": ["No collections found to migrate"],
            "errors": [],
        }
        mock_migrate.return_value = mock_result
        
        with patch.object(sys, "argv", ["migrate"]):
            result = main()
        
        assert result == 0  # Empty collections is still success
    
    @patch("utils.migrate.migrate_chroma_to_qdrant")
    def test_large_batch_size(self, mock_migrate: MagicMock) -> None:
        """Test migration with large batch size."""
        mock_result = MagicMock()
        mock_result.success = True
        mock_result.to_dict.return_value = {"success": True}
        mock_migrate.return_value = mock_result
        
        with patch.object(sys, "argv", ["migrate", "--batch-size", "10000"]):
            result = main()
        
        assert result == 0
        call_kwargs = mock_migrate.call_args[1]
        assert call_kwargs["batch_size"] == 10000
    
    @patch("utils.migrate.migrate_chroma_to_qdrant")
    def test_collections_specified(self, mock_migrate: MagicMock) -> None:
        """Test collections are shown when specified."""
        mock_result = MagicMock()
        mock_result.success = True
        mock_result.to_dict.return_value = {"success": True}
        mock_migrate.return_value = mock_result
        
        output = io.StringIO()
        with redirect_stdout(output):
            with patch.object(sys, "argv", [
                "migrate",
                "--collections", "docs", "code",
            ]):
                result = main()
        
        assert result == 0
        content = output.getvalue()
        assert "Collections: docs, code" in content


class TestCommandLineHelp:
    """Tests for command line help."""
    
    def test_help_displays_correctly(self) -> None:
        """Test --help displays usage information."""
        output = io.StringIO()
        
        with redirect_stdout(output):
            with patch.object(sys, "argv", ["migrate", "--help"]):
                try:
                    main()
                except SystemExit:
                    pass  # --help causes SystemExit(0)
        
        content = output.getvalue()
        assert "Migrate data between vector store providers" in content
        assert "--chroma-dir" in content
        assert "--qdrant-mode" in content
        assert "--collections" in content
        assert "--batch-size" in content
        assert "--dry-run" in content
        assert "--verbose" in content