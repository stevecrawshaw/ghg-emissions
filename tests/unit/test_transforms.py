"""Unit tests for data transformation utilities.

Tests cover:
- Per capita emissions calculations
- Emissions per km² calculations
- Time series aggregations
- Geographic aggregations (LSOA → MSOA → LA → CA)
- Sector aggregations
- Error handling for invalid inputs
"""

import polars as pl
import pytest

from src.data.transforms import (
    TransformationError,
    aggregate_geographic,
    aggregate_sectors,
    aggregate_time_series,
    calculate_emissions_per_km2,
    calculate_per_capita_emissions,
)


class TestCalculatePerCapitaEmissions:
    """Tests for calculate_per_capita_emissions function."""

    def test_basic_per_capita_calculation(self):
        """Test basic per capita emissions calculation."""
        emissions = pl.DataFrame(
            {
                "local_authority_code": ["E06000023", "E06000022"],
                "calendar_year": [2023, 2023],
                "territorial_emissions_kt_co2e": [1000.0, 500.0],
            }
        )
        population = pl.DataFrame(
            {
                "local_authority_code": ["E06000023", "E06000022"],
                "calendar_year": [2023, 2023],
                "population": [500000, 200000],
            }
        )

        result = calculate_per_capita_emissions(emissions, population)

        assert "per_capita_emissions_t_co2e" in result.columns
        assert result.height == 2
        # Bristol: 1000 kt * 1000 / 500000 = 2.0 t per person
        assert result["per_capita_emissions_t_co2e"][0] == pytest.approx(2.0, rel=0.01)
        # Bath: 500 kt * 1000 / 200000 = 2.5 t per person
        assert result["per_capita_emissions_t_co2e"][1] == pytest.approx(2.5, rel=0.01)

    def test_per_capita_multiple_years(self):
        """Test per capita calculation across multiple years."""
        emissions = pl.DataFrame(
            {
                "local_authority_code": ["E06000023", "E06000023"],
                "calendar_year": [2022, 2023],
                "territorial_emissions_kt_co2e": [1100.0, 1000.0],
            }
        )
        population = pl.DataFrame(
            {
                "local_authority_code": ["E06000023", "E06000023"],
                "calendar_year": [2022, 2023],
                "population": [490000, 500000],
            }
        )

        result = calculate_per_capita_emissions(emissions, population)

        assert result.height == 2
        # Check both years have per capita values
        assert all(result["per_capita_emissions_t_co2e"].is_not_null())

    def test_per_capita_missing_emissions_column(self):
        """Test error when emissions column is missing."""
        emissions = pl.DataFrame(
            {
                "local_authority_code": ["E06000023"],
                "calendar_year": [2023],
                # Missing territorial_emissions_kt_co2e
            }
        )
        population = pl.DataFrame(
            {
                "local_authority_code": ["E06000023"],
                "calendar_year": [2023],
                "population": [500000],
            }
        )

        with pytest.raises(TransformationError) as exc_info:
            calculate_per_capita_emissions(emissions, population)

        assert "missing required columns" in str(exc_info.value).lower()

    def test_per_capita_missing_population_column(self):
        """Test error when population column is missing."""
        emissions = pl.DataFrame(
            {
                "local_authority_code": ["E06000023"],
                "calendar_year": [2023],
                "territorial_emissions_kt_co2e": [1000.0],
            }
        )
        population = pl.DataFrame(
            {
                "local_authority_code": ["E06000023"],
                "calendar_year": [2023],
                # Missing population
            }
        )

        with pytest.raises(TransformationError) as exc_info:
            calculate_per_capita_emissions(emissions, population)

        assert "missing required columns" in str(exc_info.value).lower()

    def test_per_capita_zero_population(self):
        """Test error when population contains zero values."""
        emissions = pl.DataFrame(
            {
                "local_authority_code": ["E06000023"],
                "calendar_year": [2023],
                "territorial_emissions_kt_co2e": [1000.0],
            }
        )
        population = pl.DataFrame(
            {
                "local_authority_code": ["E06000023"],
                "calendar_year": [2023],
                "population": [0],
            }
        )

        with pytest.raises(TransformationError) as exc_info:
            calculate_per_capita_emissions(emissions, population)

        assert "zero or null" in str(exc_info.value).lower()

    def test_per_capita_null_population(self):
        """Test error when population contains null values."""
        emissions = pl.DataFrame(
            {
                "local_authority_code": ["E06000023"],
                "calendar_year": [2023],
                "territorial_emissions_kt_co2e": [1000.0],
            }
        )
        population = pl.DataFrame(
            {
                "local_authority_code": ["E06000023"],
                "calendar_year": [2023],
                "population": [None],
            }
        )

        with pytest.raises(TransformationError) as exc_info:
            calculate_per_capita_emissions(emissions, population)

        assert "zero or null" in str(exc_info.value).lower()

    def test_per_capita_custom_column_names(self):
        """Test per capita calculation with custom column names."""
        emissions = pl.DataFrame(
            {
                "la_code": ["E06000023"],
                "year": [2023],
                "emissions": [1000.0],
            }
        )
        population = pl.DataFrame(
            {
                "la_code": ["E06000023"],
                "year": [2023],
                "pop": [500000],
            }
        )

        result = calculate_per_capita_emissions(
            emissions,
            population,
            emissions_col="emissions",
            population_col="pop",
            geography_col="la_code",
            year_col="year",
        )

        assert result.height == 1
        assert result["per_capita_emissions_t_co2e"][0] == pytest.approx(2.0, rel=0.01)


class TestCalculateEmissionsPerKm2:
    """Tests for calculate_emissions_per_km2 function."""

    def test_basic_emissions_per_km2_calculation(self):
        """Test basic emissions per km² calculation."""
        emissions = pl.DataFrame(
            {
                "local_authority_code": ["E06000023", "E06000022"],
                "calendar_year": [2023, 2023],
                "territorial_emissions_kt_co2e": [1000.0, 500.0],
            }
        )
        area = pl.DataFrame(
            {
                "local_authority_code": ["E06000023", "E06000022"],
                "area_km2": [110.0, 350.0],
            }
        )

        result = calculate_emissions_per_km2(emissions, area)

        assert "emissions_per_km2_kt_co2e" in result.columns
        assert result.height == 2
        # Bristol: 1000 / 110 = 9.09 kt per km²
        assert result["emissions_per_km2_kt_co2e"][0] == pytest.approx(9.09, rel=0.01)
        # Bath: 500 / 350 = 1.43 kt per km²
        assert result["emissions_per_km2_kt_co2e"][1] == pytest.approx(1.43, rel=0.01)

    def test_emissions_per_km2_multiple_years(self):
        """Test emissions per km² across multiple years with same area."""
        emissions = pl.DataFrame(
            {
                "local_authority_code": ["E06000023", "E06000023"],
                "calendar_year": [2022, 2023],
                "territorial_emissions_kt_co2e": [1100.0, 1000.0],
            }
        )
        area = pl.DataFrame(
            {
                "local_authority_code": ["E06000023"],
                "area_km2": [110.0],
            }
        )

        result = calculate_emissions_per_km2(emissions, area)

        assert result.height == 2
        assert all(result["emissions_per_km2_kt_co2e"].is_not_null())

    def test_emissions_per_km2_zero_area(self):
        """Test error when area contains zero values."""
        emissions = pl.DataFrame(
            {
                "local_authority_code": ["E06000023"],
                "calendar_year": [2023],
                "territorial_emissions_kt_co2e": [1000.0],
            }
        )
        area = pl.DataFrame(
            {
                "local_authority_code": ["E06000023"],
                "area_km2": [0.0],
            }
        )

        with pytest.raises(TransformationError) as exc_info:
            calculate_emissions_per_km2(emissions, area)

        assert "zero or null" in str(exc_info.value).lower()

    def test_emissions_per_km2_missing_area_column(self):
        """Test error when area column is missing."""
        emissions = pl.DataFrame(
            {
                "local_authority_code": ["E06000023"],
                "calendar_year": [2023],
                "territorial_emissions_kt_co2e": [1000.0],
            }
        )
        area = pl.DataFrame(
            {
                "local_authority_code": ["E06000023"],
                # Missing area_km2
            }
        )

        with pytest.raises(TransformationError) as exc_info:
            calculate_emissions_per_km2(emissions, area)

        assert "missing required columns" in str(exc_info.value).lower()


class TestAggregateTimeSeries:
    """Tests for aggregate_time_series function."""

    def test_basic_time_series_aggregation(self):
        """Test basic time series aggregation with default functions."""
        df = pl.DataFrame(
            {
                "local_authority_code": ["E06000023", "E06000023", "E06000023"],
                "calendar_year": [2021, 2022, 2023],
                "territorial_emissions_kt_co2e": [1100.0, 1050.0, 1000.0],
            }
        )

        result = aggregate_time_series(
            df,
            group_cols=["local_authority_code"],
            value_col="territorial_emissions_kt_co2e",
        )

        assert result.height == 1
        assert "territorial_emissions_kt_co2e_sum" in result.columns
        assert "territorial_emissions_kt_co2e_mean" in result.columns
        assert "territorial_emissions_kt_co2e_min" in result.columns
        assert "territorial_emissions_kt_co2e_max" in result.columns
        assert "year_start" in result.columns
        assert "year_end" in result.columns

        # Check aggregated values
        assert result["territorial_emissions_kt_co2e_sum"][0] == pytest.approx(
            3150.0, rel=0.01
        )
        assert result["territorial_emissions_kt_co2e_mean"][0] == pytest.approx(
            1050.0, rel=0.01
        )
        assert result["territorial_emissions_kt_co2e_min"][0] == 1000.0
        assert result["territorial_emissions_kt_co2e_max"][0] == 1100.0
        assert result["year_start"][0] == 2021
        assert result["year_end"][0] == 2023

    def test_time_series_aggregation_custom_functions(self):
        """Test time series aggregation with custom aggregation functions."""
        df = pl.DataFrame(
            {
                "local_authority_code": ["E06000023"] * 5,
                "calendar_year": [2019, 2020, 2021, 2022, 2023],
                "territorial_emissions_kt_co2e": [
                    1200.0,
                    1150.0,
                    1100.0,
                    1050.0,
                    1000.0,
                ],
            }
        )

        result = aggregate_time_series(
            df,
            group_cols=["local_authority_code"],
            value_col="territorial_emissions_kt_co2e",
            agg_functions=["median", "std"],
        )

        assert "territorial_emissions_kt_co2e_median" in result.columns
        assert "territorial_emissions_kt_co2e_std" in result.columns

    def test_time_series_aggregation_multiple_groups(self):
        """Test time series aggregation with multiple grouping columns."""
        df = pl.DataFrame(
            {
                "local_authority_code": [
                    "E06000023",
                    "E06000023",
                    "E06000022",
                    "E06000022",
                ],
                "la_ghg_sector": ["Transport", "Transport", "Transport", "Transport"],
                "calendar_year": [2022, 2023, 2022, 2023],
                "territorial_emissions_kt_co2e": [300.0, 290.0, 150.0, 145.0],
            }
        )

        result = aggregate_time_series(
            df,
            group_cols=["local_authority_code", "la_ghg_sector"],
            value_col="territorial_emissions_kt_co2e",
        )

        assert result.height == 2  # Two LAs
        assert set(result.columns) >= {
            "local_authority_code",
            "la_ghg_sector",
            "territorial_emissions_kt_co2e_sum",
        }

    def test_time_series_aggregation_invalid_function(self):
        """Test error with invalid aggregation function."""
        df = pl.DataFrame(
            {
                "local_authority_code": ["E06000023"],
                "calendar_year": [2023],
                "territorial_emissions_kt_co2e": [1000.0],
            }
        )

        with pytest.raises(TransformationError) as exc_info:
            aggregate_time_series(
                df,
                group_cols=["local_authority_code"],
                value_col="territorial_emissions_kt_co2e",
                agg_functions=["invalid_function"],
            )

        assert "invalid aggregation" in str(exc_info.value).lower()

    def test_time_series_aggregation_missing_column(self):
        """Test error when required column is missing."""
        df = pl.DataFrame(
            {
                "local_authority_code": ["E06000023"],
                "calendar_year": [2023],
                # Missing value column
            }
        )

        with pytest.raises(TransformationError) as exc_info:
            aggregate_time_series(
                df,
                group_cols=["local_authority_code"],
                value_col="territorial_emissions_kt_co2e",
            )

        assert "missing required columns" in str(exc_info.value).lower()


class TestAggregateGeographic:
    """Tests for aggregate_geographic function."""

    def test_basic_geographic_aggregation(self):
        """Test basic geographic aggregation from LSOA to LA."""
        lsoa_data = pl.DataFrame(
            {
                "lsoa21cd": ["E01000001", "E01000002", "E01000003"],
                "calendar_year": [2023, 2023, 2023],
                "emissions": [10.0, 15.0, 20.0],
            }
        )
        lookup = pl.DataFrame(
            {
                "lsoa21cd": ["E01000001", "E01000002", "E01000003"],
                "lad25cd": ["E06000023", "E06000023", "E06000022"],
            }
        )

        result = aggregate_geographic(
            lsoa_data,
            lookup,
            from_geography_col="lsoa21cd",
            to_geography_col="lad25cd",
            value_cols=["emissions"],
        )

        assert result.height == 2  # Two LAs
        assert set(result.columns) == {"lad25cd", "calendar_year", "emissions"}
        # Bristol (E06000023): 10 + 15 = 25
        bristol = result.filter(pl.col("lad25cd") == "E06000023")
        assert bristol["emissions"][0] == 25.0
        # Bath (E06000022): 20
        bath = result.filter(pl.col("lad25cd") == "E06000022")
        assert bath["emissions"][0] == 20.0

    def test_geographic_aggregation_multiple_years(self):
        """Test geographic aggregation across multiple years."""
        lsoa_data = pl.DataFrame(
            {
                "lsoa21cd": ["E01000001", "E01000001", "E01000002"],
                "calendar_year": [2022, 2023, 2023],
                "emissions": [12.0, 10.0, 15.0],
            }
        )
        lookup = pl.DataFrame(
            {
                "lsoa21cd": ["E01000001", "E01000002"],
                "lad25cd": ["E06000023", "E06000023"],
            }
        )

        result = aggregate_geographic(
            lsoa_data,
            lookup,
            from_geography_col="lsoa21cd",
            to_geography_col="lad25cd",
            value_cols=["emissions"],
        )

        assert result.height == 2  # Two years for same LA
        year_2022 = result.filter(pl.col("calendar_year") == 2022)
        assert year_2022["emissions"][0] == 12.0
        year_2023 = result.filter(pl.col("calendar_year") == 2023)
        assert year_2023["emissions"][0] == 25.0

    def test_geographic_aggregation_multiple_value_cols(self):
        """Test geographic aggregation with multiple value columns."""
        lsoa_data = pl.DataFrame(
            {
                "lsoa21cd": ["E01000001", "E01000002"],
                "calendar_year": [2023, 2023],
                "emissions": [10.0, 15.0],
                "population": [1500, 2000],
            }
        )
        lookup = pl.DataFrame(
            {
                "lsoa21cd": ["E01000001", "E01000002"],
                "lad25cd": ["E06000023", "E06000023"],
            }
        )

        result = aggregate_geographic(
            lsoa_data,
            lookup,
            from_geography_col="lsoa21cd",
            to_geography_col="lad25cd",
            value_cols=["emissions", "population"],
        )

        assert result.height == 1
        assert result["emissions"][0] == 25.0
        assert result["population"][0] == 3500

    def test_geographic_aggregation_unmatched_geography(self):
        """Test error when geography cannot be matched in lookup."""
        lsoa_data = pl.DataFrame(
            {
                "lsoa21cd": ["E01000001", "E01999999"],  # Second doesn't exist
                "calendar_year": [2023, 2023],
                "emissions": [10.0, 15.0],
            }
        )
        lookup = pl.DataFrame(
            {
                "lsoa21cd": ["E01000001"],  # Only first one in lookup
                "lad25cd": ["E06000023"],
            }
        )

        with pytest.raises(TransformationError) as exc_info:
            aggregate_geographic(
                lsoa_data,
                lookup,
                from_geography_col="lsoa21cd",
                to_geography_col="lad25cd",
                value_cols=["emissions"],
            )

        assert "could not be mapped" in str(exc_info.value).lower()

    def test_geographic_aggregation_non_numeric_value(self):
        """Test error when value column is not numeric."""
        lsoa_data = pl.DataFrame(
            {
                "lsoa21cd": ["E01000001"],
                "calendar_year": [2023],
                "name": ["Bristol 001A"],  # String column
            }
        )
        lookup = pl.DataFrame(
            {
                "lsoa21cd": ["E01000001"],
                "lad25cd": ["E06000023"],
            }
        )

        with pytest.raises(TransformationError) as exc_info:
            aggregate_geographic(
                lsoa_data,
                lookup,
                from_geography_col="lsoa21cd",
                to_geography_col="lad25cd",
                value_cols=["name"],
            )

        assert "must be numeric" in str(exc_info.value).lower()


class TestAggregateSectors:
    """Tests for aggregate_sectors function."""

    def test_basic_sector_aggregation(self):
        """Test basic sector aggregation."""
        df = pl.DataFrame(
            {
                "local_authority_code": ["E06000023", "E06000023", "E06000023"],
                "calendar_year": [2023, 2023, 2023],
                "la_ghg_sector": ["Transport", "Domestic", "Industry"],
                "territorial_emissions_kt_co2e": [300.0, 400.0, 200.0],
            }
        )

        result = aggregate_sectors(
            df,
            sector_col="la_ghg_sector",
            value_col="territorial_emissions_kt_co2e",
        )

        assert result.height == 3  # Three sectors
        assert "territorial_emissions_kt_co2e_total" in result.columns
        assert "record_count" in result.columns
        # Each sector should have one record
        transport = result.filter(pl.col("la_ghg_sector") == "Transport")
        assert transport["territorial_emissions_kt_co2e_total"][0] == 300.0

    def test_sector_aggregation_with_geography(self):
        """Test sector aggregation grouped by geography."""
        df = pl.DataFrame(
            {
                "local_authority_code": [
                    "E06000023",
                    "E06000023",
                    "E06000022",
                    "E06000022",
                ],
                "calendar_year": [2023, 2023, 2023, 2023],
                "la_ghg_sector": ["Transport", "Domestic", "Transport", "Domestic"],
                "territorial_emissions_kt_co2e": [300.0, 400.0, 150.0, 200.0],
            }
        )

        result = aggregate_sectors(
            df,
            sector_col="la_ghg_sector",
            value_col="territorial_emissions_kt_co2e",
            group_cols=["local_authority_code"],
        )

        assert result.height == 4  # Two LAs × two sectors
        # Bristol Transport
        bristol_transport = result.filter(
            (pl.col("local_authority_code") == "E06000023")
            & (pl.col("la_ghg_sector") == "Transport")
        )
        assert bristol_transport["territorial_emissions_kt_co2e_total"][0] == 300.0

    def test_sector_aggregation_multiple_years(self):
        """Test sector aggregation across multiple years."""
        df = pl.DataFrame(
            {
                "local_authority_code": ["E06000023", "E06000023"],
                "calendar_year": [2022, 2023],
                "la_ghg_sector": ["Transport", "Transport"],
                "territorial_emissions_kt_co2e": [310.0, 300.0],
            }
        )

        result = aggregate_sectors(
            df,
            sector_col="la_ghg_sector",
            value_col="territorial_emissions_kt_co2e",
            group_cols=["local_authority_code"],
        )

        assert result.height == 2  # Same sector, two years
        assert result["record_count"].sum() == 2

    def test_sector_aggregation_missing_column(self):
        """Test error when required column is missing."""
        df = pl.DataFrame(
            {
                "local_authority_code": ["E06000023"],
                "calendar_year": [2023],
                # Missing sector column
            }
        )

        with pytest.raises(TransformationError) as exc_info:
            aggregate_sectors(
                df,
                sector_col="la_ghg_sector",
                value_col="territorial_emissions_kt_co2e",
            )

        assert "missing required columns" in str(exc_info.value).lower()

    def test_sector_aggregation_non_numeric_value(self):
        """Test error when value column is not numeric."""
        df = pl.DataFrame(
            {
                "local_authority_code": ["E06000023"],
                "calendar_year": [2023],
                "la_ghg_sector": ["Transport"],
                "name": ["Some name"],  # String value
            }
        )

        with pytest.raises(TransformationError) as exc_info:
            aggregate_sectors(
                df,
                sector_col="la_ghg_sector",
                value_col="name",
            )

        assert "must be numeric" in str(exc_info.value).lower()


class TestTransformationError:
    """Tests for TransformationError exception."""

    def test_error_with_message_only(self):
        """Test error creation with message only."""
        error = TransformationError("Test error")

        assert str(error) == "Test error"
        assert error.message == "Test error"
        assert error.data_info is None

    def test_error_with_data_info(self):
        """Test error creation with additional data info."""
        error = TransformationError(
            "Transformation failed",
            data_info="Column 'x' contains invalid values",
        )

        assert error.message == "Transformation failed"
        assert error.data_info == "Column 'x' contains invalid values"
