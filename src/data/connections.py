"""Database connection management for MotherDuck.

This module provides functions to connect to the MotherDuck cloud DuckDB instance
containing the mca_data database with GHG emissions, EPC, geographic, and
socio-economic data for the West of England Combined Authority.

Environment Variables:
    MOTHERDUCK_TOKEN: Authentication token for MotherDuck (required)
    MOTHERDUCK_DATABASE: Database name (default: mca_data)

Example:
    >>> from src.data.connections import get_connection
    >>> conn = get_connection()
    >>> result = conn.sql("SELECT COUNT(*) FROM emissions_tbl").fetchone()
"""

import os
import re
from contextlib import suppress

import duckdb


class MotherDuckConnectionError(Exception):
    """Exception raised when MotherDuck connection fails.

    Attributes:
        message: Explanation of the error
        original_error: The original exception that caused this error
    """

    def __init__(self, message: str, original_error: Exception | None = None) -> None:
        """Initialize the connection error.

        Args:
            message: Human-readable error description
            original_error: The underlying exception, if any
        """
        self.message = message
        self.original_error = original_error
        super().__init__(self.message)


def get_connection(database: str = "mca_data") -> duckdb.DuckDBPyConnection:
    """Get a connection to the MotherDuck database.

    Establishes a connection to MotherDuck using the token from the
    MOTHERDUCK_TOKEN environment variable. The connection is read-only
    and provides access to all tables in the specified database.

    Args:
        database: Database name to connect to (default: mca_data)

    Returns:
        Active DuckDB connection to MotherDuck

    Raises:
        MotherDuckConnectionError: If token is missing or connection fails

    Example:
        >>> conn = get_connection()
        >>> data = conn.sql("SELECT * FROM ca_la_tbl LIMIT 5").pl()
        >>> conn.close()
    """
    # Get token from environment
    token = os.getenv("MOTHERDUCK_TOKEN")
    if not token:
        raise MotherDuckConnectionError(
            "MOTHERDUCK_TOKEN environment variable not set. "
            "Please set your MotherDuck authentication token."
        )

    # Construct connection string
    connection_string = f"md:{database}?motherduck_token={token}"

    # Attempt connection
    try:
        conn = duckdb.connect(connection_string, read_only=True)
        return conn
    except duckdb.ConnectionException as e:
        raise MotherDuckConnectionError(
            f"Failed to connect to MotherDuck database '{database}'. "
            f"Check your token and network connection.",
            original_error=e,
        ) from e
    except Exception as e:
        raise MotherDuckConnectionError(
            f"Unexpected error connecting to MotherDuck: {e}",
            original_error=e,
        ) from e


def test_connection(conn: duckdb.DuckDBPyConnection | None = None) -> bool:
    """Test if a MotherDuck connection is working.

    Verifies the connection by running a simple query against the database.
    If no connection is provided, creates a new one for testing.

    Args:
        conn: Optional existing connection to test. If None, creates new connection.

    Returns:
        True if connection is working, False otherwise

    Example:
        >>> if test_connection():
        ...     print("Connection OK")
        >>> conn = get_connection()
        >>> if test_connection(conn):
        ...     print("Existing connection OK")
    """
    close_after_test = False

    try:
        # Create connection if not provided
        if conn is None:
            conn = get_connection()
            close_after_test = True

        # Test with simple query
        result = conn.sql("SELECT 1 AS test").fetchone()

        if close_after_test:
            conn.close()

        return result is not None and result[0] == 1

    except Exception:
        if close_after_test and conn is not None:
            with suppress(Exception):
                conn.close()
        return False


def get_table_list(conn: duckdb.DuckDBPyConnection | None = None) -> list[str]:
    """Get list of all tables in the mca_data database.

    Args:
        conn: Optional existing connection. If None, creates new connection.

    Returns:
        List of table names in the database

    Raises:
        MotherDuckConnectionError: If connection fails

    Example:
        >>> tables = get_table_list()
        >>> print(f"Found {len(tables)} tables")
        >>> "emissions_tbl" in tables
        True
    """
    close_after = False

    try:
        # Create connection if not provided
        if conn is None:
            conn = get_connection()
            close_after = True

        # Query information schema for tables
        result = conn.sql(
            """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'main'
            AND table_type = 'BASE TABLE'
            ORDER BY table_name
            """
        ).fetchall()

        if close_after:
            conn.close()

        return [row[0] for row in result]

    except Exception as e:
        if close_after and conn is not None:
            with suppress(Exception):
                conn.close()
        raise MotherDuckConnectionError(
            f"Failed to retrieve table list: {e}",
            original_error=e,
        ) from e


def get_table_info(
    table_name: str,
    conn: duckdb.DuckDBPyConnection | None = None,
) -> dict[str, str]:
    """Get column information for a specific table.

    Args:
        table_name: Name of the table to inspect
        conn: Optional existing connection. If None, creates new connection.

    Returns:
        Dictionary mapping column names to their data types

    Raises:
        MotherDuckConnectionError: If connection or query fails
        ValueError: If table_name contains invalid characters

    Example:
        >>> info = get_table_info("emissions_tbl")
        >>> print(info["calendar_year"])
        BIGINT
    """
    # Validate table name to prevent SQL injection
    # Only allow alphanumeric characters and underscores
    if not re.match(r"^[a-zA-Z0-9_]+$", table_name):
        raise ValueError(
            f"Invalid table name '{table_name}'. "
            "Only alphanumeric characters and underscores are allowed."
        )

    close_after = False

    try:
        # Create connection if not provided
        if conn is None:
            conn = get_connection()
            close_after = True

        # Query information schema for columns
        # Note: Table names in WHERE clauses cannot be parameterized,
        # but we've validated the input above to prevent injection
        result = conn.sql(
            f"""  # noqa: S608
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = '{table_name}'
            AND table_schema = 'main'
            ORDER BY ordinal_position
            """
        ).fetchall()

        if close_after:
            conn.close()

        return {row[0]: row[1] for row in result}

    except Exception as e:
        if close_after and conn is not None:
            with suppress(Exception):
                conn.close()
        raise MotherDuckConnectionError(
            f"Failed to retrieve table info for '{table_name}': {e}",
            original_error=e,
        ) from e
