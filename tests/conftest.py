"""Pytest configuration and shared fixtures for GHG Emissions Dashboard tests.

This module provides common test fixtures including:
- Mock MotherDuck connections
- Sample data generators
- Reusable test utilities
"""

from pathlib import Path
from unittest.mock import MagicMock

import pytest


@pytest.fixture
def project_root() -> Path:
    """Get the project root directory path.

    Returns:
        Path object pointing to the project root
    """
    return Path(__file__).parent.parent


@pytest.fixture
def schema_path(project_root: Path) -> Path:
    """Get the schema directory path.

    Args:
        project_root: Project root directory fixture

    Returns:
        Path object pointing to the schema directory
    """
    return project_root / "schema"


@pytest.fixture
def mock_duckdb_connection():
    """Create a mock DuckDB connection for testing.

    Returns:
        MagicMock object simulating a DuckDB connection

    Example:
        def test_query(mock_duckdb_connection):
            result = mock_duckdb_connection.sql("SELECT 1")
            assert result is not None
    """
    mock_conn = MagicMock()
    mock_conn.sql.return_value = MagicMock()
    return mock_conn


@pytest.fixture
def sample_emissions_data() -> dict[str, list]:
    """Generate sample emissions data for testing.

    Returns:
        Dictionary with columns as keys and lists as values

    Example:
        def test_transform(sample_emissions_data):
            df = pl.DataFrame(sample_emissions_data)
            assert len(df) == 3
    """
    return {
        "local_authority": ["Bristol", "Bath and North East Somerset", "South Gloucestershire"],
        "local_authority_code": ["E06000023", "E06000022", "E06000025"],
        "calendar_year": [2022, 2022, 2022],
        "grand_total": [2534.5, 1234.8, 1876.3],  # kt CO2e
        "population_000s_mid_year_estimate": [465.9, 196.4, 290.8],
        "area_km2": [110.0, 346.0, 497.0],
    }


@pytest.fixture
def sample_epc_data() -> dict[str, list]:
    """Generate sample EPC data for testing.

    Returns:
        Dictionary with columns as keys and lists as values
    """
    return {
        "LMK_KEY": ["ABC123", "DEF456", "GHI789"],
        "LOCAL_AUTHORITY": ["E06000023", "E06000023", "E06000022"],
        "PROPERTY_TYPE": ["House", "Flat", "House"],
        "CURRENT_ENERGY_RATING": ["C", "D", "B"],
        "CO2_EMISSIONS_CURRENT": [2.5, 3.2, 1.8],
        "TOTAL_FLOOR_AREA": [85.0, 52.0, 120.0],
        "CONSTRUCTION_AGE_BAND": ["1930-1949", "1950-1966", "2007-2011"],
        "TENURE": ["Owner-occupied", "Rented (private)", "Owner-occupied"],
    }


@pytest.fixture(autouse=True)
def reset_environment(monkeypatch):
    """Reset environment variables for each test.

    This fixture automatically runs for every test and ensures
    a clean environment state.

    Args:
        monkeypatch: Pytest monkeypatch fixture
    """
    # Remove any existing MotherDuck token
    monkeypatch.delenv("MOTHERDUCK_TOKEN", raising=False)


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers.

    Args:
        config: Pytest config object
    """
    config.addinivalue_line("markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')")
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "data_quality: marks tests that check data quality")
