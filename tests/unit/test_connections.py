"""Unit tests for MotherDuck database connection management.

Tests cover:
- Connection creation with valid/invalid tokens
- Error handling for connection failures
- Connection testing functionality
- Table listing and introspection
"""

from unittest.mock import MagicMock, patch

import pytest

from src.data.connections import (
    MotherDuckConnectionError,
    get_connection,
    get_table_info,
    get_table_list,
    test_connection,
)


class TestGetConnection:
    """Tests for the get_connection function."""

    def test_connection_without_token_raises_error(self, monkeypatch):
        """Test that missing MOTHERDUCK_TOKEN raises MotherDuckConnectionError."""
        monkeypatch.delenv("MOTHERDUCK_TOKEN", raising=False)

        with pytest.raises(MotherDuckConnectionError) as exc_info:
            get_connection()

        assert "MOTHERDUCK_TOKEN" in str(exc_info.value)
        assert "not set" in str(exc_info.value)

    @patch("src.data.connections.duckdb.connect")
    def test_connection_with_valid_token(self, mock_connect, monkeypatch):
        """Test successful connection with valid token."""
        monkeypatch.setenv("MOTHERDUCK_TOKEN", "test_token_123")
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn

        conn = get_connection()

        assert conn is not None
        mock_connect.assert_called_once()
        call_args = mock_connect.call_args[0][0]
        assert "md:mca_data" in call_args
        assert "motherduck_token=test_token_123" in call_args

    @patch("src.data.connections.duckdb.connect")
    def test_connection_with_custom_database(self, mock_connect, monkeypatch):
        """Test connection to custom database name."""
        monkeypatch.setenv("MOTHERDUCK_TOKEN", "test_token_123")
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn

        conn = get_connection(database="custom_db")

        assert conn is not None
        call_args = mock_connect.call_args[0][0]
        assert "md:custom_db" in call_args

    @patch("src.data.connections.duckdb.connect")
    def test_connection_failure_raises_error(self, mock_connect, monkeypatch):
        """Test that connection failures raise MotherDuckConnectionError."""
        monkeypatch.setenv("MOTHERDUCK_TOKEN", "test_token_123")

        # Simulate connection error
        import duckdb

        mock_connect.side_effect = duckdb.ConnectionException("Connection failed")

        with pytest.raises(MotherDuckConnectionError) as exc_info:
            get_connection()

        assert "Failed to connect" in str(exc_info.value)
        assert exc_info.value.original_error is not None

    @patch("src.data.connections.duckdb.connect")
    def test_connection_read_only_flag(self, mock_connect, monkeypatch):
        """Test that connection is created with read_only=True."""
        monkeypatch.setenv("MOTHERDUCK_TOKEN", "test_token_123")
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn

        get_connection()

        # Check that read_only=True was passed
        _, kwargs = mock_connect.call_args
        assert kwargs.get("read_only") is True


class TestTestConnection:
    """Tests for the test_connection function."""

    @patch("src.data.connections.get_connection")
    def test_connection_test_success(self, mock_get_connection):
        """Test successful connection test."""
        mock_conn = MagicMock()
        mock_result = MagicMock()
        mock_result.fetchone.return_value = (1,)
        mock_conn.sql.return_value = mock_result
        mock_get_connection.return_value = mock_conn

        result = test_connection()

        assert result is True
        mock_conn.sql.assert_called_once_with("SELECT 1 AS test")
        mock_conn.close.assert_called_once()

    @patch("src.data.connections.get_connection")
    def test_connection_test_failure(self, mock_get_connection):
        """Test failed connection test."""
        mock_get_connection.side_effect = MotherDuckConnectionError("Connection failed")

        result = test_connection()

        assert result is False

    def test_connection_test_with_existing_connection(self):
        """Test connection test with provided connection."""
        mock_conn = MagicMock()
        mock_result = MagicMock()
        mock_result.fetchone.return_value = (1,)
        mock_conn.sql.return_value = mock_result

        result = test_connection(conn=mock_conn)

        assert result is True
        # Should not close provided connection
        mock_conn.close.assert_not_called()

    def test_connection_test_with_invalid_result(self):
        """Test connection test with unexpected query result."""
        mock_conn = MagicMock()
        mock_result = MagicMock()
        mock_result.fetchone.return_value = None
        mock_conn.sql.return_value = mock_result

        result = test_connection(conn=mock_conn)

        assert result is False


class TestGetTableList:
    """Tests for the get_table_list function."""

    @patch("src.data.connections.get_connection")
    def test_get_table_list_success(self, mock_get_connection):
        """Test successful table list retrieval."""
        mock_conn = MagicMock()
        mock_result = MagicMock()
        mock_result.fetchall.return_value = [
            ("emissions_tbl",),
            ("epc_domestic_tbl",),
            ("ca_la_tbl",),
        ]
        mock_conn.sql.return_value = mock_result
        mock_get_connection.return_value = mock_conn

        tables = get_table_list()

        assert len(tables) == 3
        assert "emissions_tbl" in tables
        assert "epc_domestic_tbl" in tables
        assert "ca_la_tbl" in tables
        mock_conn.close.assert_called_once()

    @patch("src.data.connections.get_connection")
    def test_get_table_list_with_existing_connection(self, mock_get_connection):
        """Test table list with provided connection."""
        mock_conn = MagicMock()
        mock_result = MagicMock()
        mock_result.fetchall.return_value = [("test_tbl",)]
        mock_conn.sql.return_value = mock_result

        tables = get_table_list(conn=mock_conn)

        assert len(tables) == 1
        # Should not close provided connection
        mock_conn.close.assert_not_called()
        # Should not create new connection
        mock_get_connection.assert_not_called()

    @patch("src.data.connections.get_connection")
    def test_get_table_list_empty_database(self, mock_get_connection):
        """Test table list for empty database."""
        mock_conn = MagicMock()
        mock_result = MagicMock()
        mock_result.fetchall.return_value = []
        mock_conn.sql.return_value = mock_result
        mock_get_connection.return_value = mock_conn

        tables = get_table_list()

        assert tables == []


class TestGetTableInfo:
    """Tests for the get_table_info function."""

    @patch("src.data.connections.get_connection")
    def test_get_table_info_success(self, mock_get_connection):
        """Test successful table info retrieval."""
        mock_conn = MagicMock()
        mock_result = MagicMock()
        mock_result.fetchall.return_value = [
            ("local_authority", "VARCHAR"),
            ("calendar_year", "BIGINT"),
            ("grand_total", "DOUBLE"),
        ]
        mock_conn.sql.return_value = mock_result
        mock_get_connection.return_value = mock_conn

        info = get_table_info("emissions_tbl")

        assert len(info) == 3
        assert info["local_authority"] == "VARCHAR"
        assert info["calendar_year"] == "BIGINT"
        assert info["grand_total"] == "DOUBLE"
        mock_conn.close.assert_called_once()

    @patch("src.data.connections.get_connection")
    def test_get_table_info_with_existing_connection(self, mock_get_connection):
        """Test table info with provided connection."""
        mock_conn = MagicMock()
        mock_result = MagicMock()
        mock_result.fetchall.return_value = [("col1", "VARCHAR")]
        mock_conn.sql.return_value = mock_result

        info = get_table_info("test_tbl", conn=mock_conn)

        assert len(info) == 1
        # Should not close provided connection
        mock_conn.close.assert_not_called()
        # Should not create new connection
        mock_get_connection.assert_not_called()

    @patch("src.data.connections.get_connection")
    def test_get_table_info_nonexistent_table(self, mock_get_connection):
        """Test table info for non-existent table."""
        mock_conn = MagicMock()
        mock_result = MagicMock()
        mock_result.fetchall.return_value = []
        mock_conn.sql.return_value = mock_result
        mock_get_connection.return_value = mock_conn

        info = get_table_info("nonexistent_table")

        assert info == {}

    def test_get_table_info_invalid_table_name(self):
        """Test table info with invalid table name raises ValueError."""
        # Test with SQL injection attempt
        with pytest.raises(ValueError) as exc_info:
            get_table_info("test'; DROP TABLE users; --")

        assert "Invalid table name" in str(exc_info.value)

        # Test with special characters
        with pytest.raises(ValueError):
            get_table_info("table-name")

        # Test with spaces
        with pytest.raises(ValueError):
            get_table_info("table name")


class TestMotherDuckConnectionError:
    """Tests for the MotherDuckConnectionError exception class."""

    def test_error_with_message_only(self):
        """Test error creation with message only."""
        error = MotherDuckConnectionError("Test error message")

        assert str(error) == "Test error message"
        assert error.message == "Test error message"
        assert error.original_error is None

    def test_error_with_original_exception(self):
        """Test error creation with original exception."""
        original = ValueError("Original error")
        error = MotherDuckConnectionError("Wrapped error", original_error=original)

        assert error.message == "Wrapped error"
        assert error.original_error is original
        assert isinstance(error.original_error, ValueError)
