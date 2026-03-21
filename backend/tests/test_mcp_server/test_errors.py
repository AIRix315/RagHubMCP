"""Tests for MCP tools error helpers."""

import json

from src.mcp_server.tools._errors import (
    error_response,
    success_response,
    validate_collection_name,
    validate_documents,
    validate_positive_int,
    validate_query,
    validate_range,
)


class TestErrorResponse:
    """Tests for error_response function."""

    def test_error_response_basic(self):
        """Test basic error response."""
        result = error_response("Something went wrong")

        parsed = json.loads(result)
        assert parsed["error"] == "Something went wrong"

    def test_error_response_with_kwargs(self):
        """Test error response with additional fields."""
        result = error_response("Invalid input", field="name", value="")

        parsed = json.loads(result)
        assert parsed["error"] == "Invalid input"
        assert parsed["field"] == "name"
        assert parsed["value"] == ""

    def test_error_response_format(self):
        """Test error response is properly formatted."""
        result = error_response("test error")

        # Should be valid JSON
        parsed = json.loads(result)
        assert isinstance(parsed, dict)
        assert "error" in parsed


class TestValidateCollectionName:
    """Tests for validate_collection_name function."""

    def test_valid_collection_name(self):
        """Test valid collection name returns None."""
        assert validate_collection_name("my_collection") is None
        assert validate_collection_name("valid-name-123") is None
        assert validate_collection_name("test123") is None

    def test_empty_collection_name(self):
        """Test empty collection name returns error."""
        result = validate_collection_name("")
        assert result is not None
        assert "empty" in result.lower() or "required" in result.lower()

    def test_none_collection_name(self):
        """Test None collection name returns error."""
        result = validate_collection_name(None)
        assert result is not None
        assert "empty" in result.lower() or "non-empty" in result.lower()


class TestValidateQuery:
    """Tests for validate_query function."""

    def test_valid_query(self):
        """Test valid query returns None."""
        assert validate_query("search query") is None
        assert validate_query("another valid query") is None

    def test_empty_query(self):
        """Test empty query returns error."""
        result = validate_query("")
        assert result is not None
        assert "empty" in result.lower() or "non-empty" in result.lower()

    def test_none_query(self):
        """Test None query returns error."""
        result = validate_query(None)
        assert result is not None
        assert "empty" in result.lower() or "non-empty" in result.lower()


class TestValidateDocuments:
    """Tests for validate_documents function."""

    def test_valid_documents(self):
        """Test valid documents returns None."""
        assert validate_documents(["doc1", "doc2", "doc3"]) is None

    def test_empty_documents(self):
        """Test empty documents list returns error."""
        result = validate_documents([])
        assert result is not None
        assert "empty" in result.lower() or "non-empty" in result.lower()

    def test_none_documents(self):
        """Test None documents returns error."""
        result = validate_documents(None)
        assert result is not None
        assert "empty" in result.lower() or "list" in result.lower()


class TestValidatePositiveInt:
    """Tests for validate_positive_int function."""

    def test_valid_positive_int(self):
        """Test valid positive int returns None."""
        assert validate_positive_int(5, "limit") is None
        assert validate_positive_int(100, "top_k") is None

    def test_negative_int(self):
        """Test negative int returns error."""
        result = validate_positive_int(-1, "limit")
        assert result is not None
        assert "positive" in result.lower()

    def test_zero(self):
        """Test zero returns error."""
        result = validate_positive_int(0, "limit")
        assert result is not None
        assert "positive" in result.lower()

    def test_none_value(self):
        """Test None value returns None (optional field)."""
        assert validate_positive_int(None, "limit") is None

    def test_non_int_value(self):
        """Test non-integer value returns error."""
        result = validate_positive_int("5", "limit")  # type: ignore
        assert result is not None
        assert "positive" in result.lower()


class TestValidateRange:
    """Tests for validate_range function."""

    def test_valid_range(self):
        """Test value within range returns None."""
        assert validate_range(0.5, "alpha", 0.0, 1.0) is None
        assert validate_range(0.0, "beta", 0.0, 1.0) is None
        assert validate_range(1.0, "gamma", 0.0, 1.0) is None

    def test_value_below_range(self):
        """Test value below range returns error."""
        result = validate_range(-0.1, "alpha", 0.0, 1.0)
        assert result is not None
        assert "between" in result.lower()

    def test_value_above_range(self):
        """Test value above range returns error."""
        result = validate_range(1.1, "alpha", 0.0, 1.0)
        assert result is not None
        assert "between" in result.lower()

    def test_none_value(self):
        """Test None value returns None (optional field)."""
        assert validate_range(None, "alpha", 0.0, 1.0) is None


class TestSuccessResponse:
    """Tests for success_response function."""

    def test_success_response_default(self):
        """Test default success response."""
        result = success_response()

        parsed = json.loads(result)
        assert parsed["status"] == "success"
        assert "message" in parsed

    def test_success_response_custom_message(self):
        """Test success response with custom message."""
        result = success_response("Document added successfully")

        parsed = json.loads(result)
        assert parsed["status"] == "success"
        assert parsed["message"] == "Document added successfully"

    def test_success_response_with_kwargs(self):
        """Test success response with additional fields."""
        result = success_response("Query completed", count=10, collection="test")

        parsed = json.loads(result)
        assert parsed["status"] == "success"
        assert parsed["message"] == "Query completed"
        assert parsed["count"] == 10
        assert parsed["collection"] == "test"
