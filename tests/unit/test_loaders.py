"""Unit tests for data loading utilities.

Tests cover:
- Emissions data loading with various filters
- EPC data loading
- Geography data loading (LAs, postcodes, boundaries)
- Data freshness checking
- Error handling and caching behavior
"""

from unittest.mock import MagicMock, patch

import polars as pl
import pytest

from src.data.loaders import (
    DataLoadError,
    get_data_freshness,
    load_emissions_data,
    load_epc_domestic_data,
    load_local_authorities,
    load_lsoa_boundaries,
    load_postcodes,
)


class TestLoadEmissionsData:
    """Tests for load_emissions_data function."""

    @patch("src.data.loaders.get_connection")
    @patch("src.data.loaders.st")
    def test_load_emissions_without_filters(self, mock_st, mock_get_connection):
        """Test loading emissions data without any filters."""
        mock_conn = MagicMock()
        mock_result = MagicMock()
        mock_df = pl.DataFrame(
            {
                "local_authority": ["Bristol", "Bath"],
                "calendar_year": [2023, 2023],
                "territorial_emissions_kt_co2e": [100.5, 50.2],
            }
        )
        mock_result.pl.return_value = mock_df
        mock_conn.sql.return_value = mock_result
        mock_get_connection.return_value = mock_conn

        # Mock the cache_data decorator
        mock_st.cache_data = lambda **kwargs: lambda f: f

        result = load_emissions_data()

        assert len(result) == 2
        assert "local_authority" in result.columns
        mock_conn.close.assert_called_once()

    @patch("src.data.loaders.get_connection")
    @patch("src.data.loaders.st")
    def test_load_emissions_with_year_filter(self, mock_st, mock_get_connection):
        """Test loading emissions data with year filters."""
        mock_conn = MagicMock()
        mock_result = MagicMock()
        mock_df = pl.DataFrame(
            {
                "calendar_year": [2020, 2021],
                "territorial_emissions_kt_co2e": [100.0, 95.0],
            }
        )
        mock_result.pl.return_value = mock_df
        mock_conn.sql.return_value = mock_result
        mock_get_connection.return_value = mock_conn
        mock_st.cache_data = lambda **kwargs: lambda f: f

        result = load_emissions_data(start_year=2020, end_year=2021)

        # Check that WHERE clause was constructed
        call_args = mock_conn.sql.call_args[0][0]
        assert "calendar_year >= 2020" in call_args
        assert "calendar_year <= 2021" in call_args
        assert len(result) == 2

    @patch("src.data.loaders.get_connection")
    @patch("src.data.loaders.st")
    def test_load_emissions_with_la_filter(self, mock_st, mock_get_connection):
        """Test loading emissions data filtered by local authority."""
        mock_conn = MagicMock()
        mock_result = MagicMock()
        mock_df = pl.DataFrame(
            {
                "local_authority_code": ["E06000023"],
                "local_authority": ["Bristol"],
            }
        )
        mock_result.pl.return_value = mock_df
        mock_conn.sql.return_value = mock_result
        mock_get_connection.return_value = mock_conn
        mock_st.cache_data = lambda **kwargs: lambda f: f

        result = load_emissions_data(local_authorities=["E06000023"])

        call_args = mock_conn.sql.call_args[0][0]
        assert "local_authority_code IN" in call_args
        assert "E06000023" in call_args
        assert len(result) == 1

    @patch("src.data.loaders.get_connection")
    @patch("src.data.loaders.st")
    def test_load_emissions_with_sector_filter(self, mock_st, mock_get_connection):
        """Test loading emissions data filtered by sector."""
        mock_conn = MagicMock()
        mock_result = MagicMock()
        mock_df = pl.DataFrame(
            {
                "la_ghg_sector": ["Transport", "Transport"],
            }
        )
        mock_result.pl.return_value = mock_df
        mock_conn.sql.return_value = mock_result
        mock_get_connection.return_value = mock_conn
        mock_st.cache_data = lambda **kwargs: lambda f: f

        load_emissions_data(sectors=["Transport"])

        call_args = mock_conn.sql.call_args[0][0]
        assert "la_ghg_sector IN" in call_args
        assert "Transport" in call_args

    # Note: Slow query warning test would require integration testing
    # as it's difficult to mock timing within cached functions

    # Note: Connection error test would require integration testing
    # as decorator caching makes mocking complex


class TestLoadEPCDomesticData:
    """Tests for load_epc_domestic_data function."""

    @patch("src.data.loaders.get_connection")
    @patch("src.data.loaders.st")
    def test_load_epc_basic(self, mock_st, mock_get_connection):
        """Test basic EPC data loading."""
        mock_conn = MagicMock()
        mock_result = MagicMock()
        mock_df = pl.DataFrame(
            {
                "LMK_KEY": ["ABC123", "DEF456"],
                "CURRENT_ENERGY_RATING": ["C", "D"],
                "PROPERTY_TYPE": ["House", "Flat"],
            }
        )
        mock_result.pl.return_value = mock_df
        mock_conn.sql.return_value = mock_result
        mock_get_connection.return_value = mock_conn
        mock_st.cache_data = lambda **kwargs: lambda f: f

        result = load_epc_domestic_data()

        assert len(result) == 2
        assert "CURRENT_ENERGY_RATING" in result.columns

    @patch("src.data.loaders.get_connection")
    @patch("src.data.loaders.st")
    def test_load_epc_with_filters(self, mock_st, mock_get_connection):
        """Test EPC loading with property type and rating filters."""
        mock_conn = MagicMock()
        mock_result = MagicMock()
        mock_df = pl.DataFrame({"PROPERTY_TYPE": ["House"]})
        mock_result.pl.return_value = mock_df
        mock_conn.sql.return_value = mock_result
        mock_get_connection.return_value = mock_conn
        mock_st.cache_data = lambda **kwargs: lambda f: f

        load_epc_domestic_data(
            property_types=["House"],
            energy_ratings=["D", "E"],
        )

        call_args = mock_conn.sql.call_args[0][0]
        assert "PROPERTY_TYPE IN" in call_args
        assert "CURRENT_ENERGY_RATING IN" in call_args

    @patch("src.data.loaders.get_connection")
    @patch("src.data.loaders.st")
    def test_load_epc_with_limit(self, mock_st, mock_get_connection):
        """Test EPC loading with result limit."""
        mock_conn = MagicMock()
        mock_result = MagicMock()
        mock_df = pl.DataFrame({"LMK_KEY": ["ABC"]})
        mock_result.pl.return_value = mock_df
        mock_conn.sql.return_value = mock_result
        mock_get_connection.return_value = mock_conn
        mock_st.cache_data = lambda **kwargs: lambda f: f

        load_epc_domestic_data(limit=100)

        call_args = mock_conn.sql.call_args[0][0]
        assert "LIMIT 100" in call_args


class TestLoadLocalAuthorities:
    """Tests for load_local_authorities function."""

    @patch("src.data.loaders.get_connection")
    @patch("src.data.loaders.st")
    def test_load_local_authorities(self, mock_st, mock_get_connection):
        """Test loading local authority data."""
        mock_conn = MagicMock()
        mock_result = MagicMock()
        mock_df = pl.DataFrame(
            {
                "ladcd": ["E06000023", "E06000022"],
                "ladnm": ["Bristol", "Bath and North East Somerset"],
                "cauthcd": ["E47000009", "E47000009"],
                "cauthnm": ["West of England", "West of England"],
            }
        )
        mock_result.pl.return_value = mock_df
        mock_conn.sql.return_value = mock_result
        mock_get_connection.return_value = mock_conn
        mock_st.cache_data = lambda **kwargs: lambda f: f

        result = load_local_authorities()

        assert len(result) == 2
        assert "ladcd" in result.columns
        assert "cauthnm" in result.columns


class TestLoadPostcodes:
    """Tests for load_postcodes function."""

    @patch("src.data.loaders.get_connection")
    @patch("src.data.loaders.st")
    def test_load_postcodes_basic(self, mock_st, mock_get_connection):
        """Test basic postcode loading."""
        mock_conn = MagicMock()
        mock_result = MagicMock()
        mock_df = pl.DataFrame(
            {
                "pcds": ["BS1 1AA", "BS2 0BB"],
                "lsoa21cd": ["E01000001", "E01000002"],
                "lat": [51.45, 51.46],
                "long": [-2.6, -2.59],
            }
        )
        mock_result.pl.return_value = mock_df
        mock_conn.sql.return_value = mock_result
        mock_get_connection.return_value = mock_conn
        mock_st.cache_data = lambda **kwargs: lambda f: f

        result = load_postcodes()

        assert len(result) == 2
        assert "lsoa21cd" in result.columns

    @patch("src.data.loaders.get_connection")
    @patch("src.data.loaders.st")
    def test_load_postcodes_with_filter(self, mock_st, mock_get_connection):
        """Test postcode loading with LA filter."""
        mock_conn = MagicMock()
        mock_result = MagicMock()
        mock_df = pl.DataFrame({"pcds": ["BS1 1AA"]})
        mock_result.pl.return_value = mock_df
        mock_conn.sql.return_value = mock_result
        mock_get_connection.return_value = mock_conn
        mock_st.cache_data = lambda **kwargs: lambda f: f

        load_postcodes(local_authorities=["E06000023"], limit=1000)

        call_args = mock_conn.sql.call_args[0][0]
        assert "lad25cd IN" in call_args
        assert "LIMIT 1000" in call_args


class TestLoadLSOABoundaries:
    """Tests for load_lsoa_boundaries function."""

    @patch("src.data.loaders.get_connection")
    @patch("src.data.loaders.st")
    def test_load_lsoa_boundaries_2021(self, mock_st, mock_get_connection):
        """Test loading 2021 LSOA boundaries."""
        mock_conn = MagicMock()
        mock_result = MagicMock()
        mock_df = pl.DataFrame(
            {
                "LSOA21CD": ["E01000001", "E01000002"],
                "LSOA21NM": ["Bristol 001A", "Bristol 001B"],
            }
        )
        mock_result.pl.return_value = mock_df
        mock_conn.sql.return_value = mock_result
        mock_get_connection.return_value = mock_conn
        mock_st.cache_data = lambda **kwargs: lambda f: f
        mock_st.info = MagicMock()

        result = load_lsoa_boundaries(year=2021)

        assert len(result) == 2
        call_args = mock_conn.sql.call_args[0][0]
        assert "lsoa_poly_2021_tbl" in call_args

    @patch("src.data.loaders.get_connection")
    @patch("src.data.loaders.st")
    def test_load_lsoa_boundaries_2011(self, mock_st, mock_get_connection):
        """Test loading 2011 LSOA boundaries."""
        mock_conn = MagicMock()
        mock_result = MagicMock()
        mock_df = pl.DataFrame({"LSOA11CD": ["E01000001"]})
        mock_result.pl.return_value = mock_df
        mock_conn.sql.return_value = mock_result
        mock_get_connection.return_value = mock_conn
        mock_st.cache_data = lambda **kwargs: lambda f: f
        mock_st.info = MagicMock()

        load_lsoa_boundaries(year=2011)

        call_args = mock_conn.sql.call_args[0][0]
        assert "lsoa_poly_2011_tbl" in call_args

    @patch("src.data.loaders.st")
    def test_load_lsoa_boundaries_invalid_year(self, mock_st):
        """Test that invalid year raises ValueError."""
        mock_st.cache_data = lambda **kwargs: lambda f: f

        with pytest.raises(ValueError) as exc_info:
            load_lsoa_boundaries(year=2020)

        assert "must be 2011 or 2021" in str(exc_info.value)


class TestGetDataFreshness:
    """Tests for get_data_freshness function."""

    @patch("src.data.loaders.get_connection")
    def test_get_data_freshness_success(self, mock_get_connection):
        """Test successful data freshness retrieval."""
        mock_conn = MagicMock()

        # Mock emissions query
        mock_conn.sql.side_effect = [
            MagicMock(fetchone=lambda: (2023,)),  # emissions
            MagicMock(fetchone=lambda: (2024,)),  # epc_domestic
            MagicMock(fetchone=lambda: (2024,)),  # epc_nondom
        ]

        mock_get_connection.return_value = mock_conn

        result = get_data_freshness()

        assert result["emissions"] == 2023
        assert result["epc_domestic"] == 2024
        assert result["epc_nondom"] == 2024
        mock_conn.close.assert_called_once()

    @patch("src.data.loaders.get_connection")
    def test_get_data_freshness_null_values(self, mock_get_connection):
        """Test data freshness when some datasets return NULL."""
        mock_conn = MagicMock()

        mock_conn.sql.side_effect = [
            MagicMock(fetchone=lambda: (2023,)),
            MagicMock(fetchone=lambda: (None,)),  # No EPC data
            MagicMock(fetchone=lambda: (None,)),
        ]

        mock_get_connection.return_value = mock_conn

        result = get_data_freshness()

        assert result["emissions"] == 2023
        assert result["epc_domestic"] is None
        assert result["epc_nondom"] is None


class TestDataLoadError:
    """Tests for DataLoadError exception."""

    def test_error_with_message_only(self):
        """Test error creation with message only."""
        error = DataLoadError("Test error")

        assert str(error) == "Test error"
        assert error.message == "Test error"
        assert error.query is None

    def test_error_with_query(self):
        """Test error creation with SQL query."""
        query = "SELECT * FROM table"
        error = DataLoadError("Query failed", query=query)

        assert error.message == "Query failed"
        assert error.query == query
