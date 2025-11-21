"""Data transformation utilities for GHG emissions and geographic data.

This module provides functions for:
- Per capita emissions calculations
- Emissions per km² calculations
- Time series aggregations
- Geographic aggregations (LSOA → MSOA → LA → CA)
- Sector aggregations

All functions accept Polars DataFrames and return transformed DataFrames.
"""

import polars as pl


class TransformationError(Exception):
    """Exception raised when data transformation fails.

    Attributes:
        message: Explanation of the error
        data_info: Optional information about the problematic data
    """

    def __init__(self, message: str, data_info: str | None = None) -> None:
        """Initialize the transformation error.

        Args:
            message: Human-readable error description
            data_info: Optional details about the data that caused the error
        """
        self.message = message
        self.data_info = data_info
        super().__init__(self.message)


def calculate_per_capita_emissions(
    emissions_df: pl.DataFrame,
    population_df: pl.DataFrame,
    emissions_col: str = "territorial_emissions_kt_co2e",
    population_col: str = "population",
    geography_col: str = "local_authority_code",
    year_col: str = "calendar_year",
) -> pl.DataFrame:
    """Calculate per capita emissions by joining emissions and population data.

    Joins emissions and population datasets on geography and year, then calculates
    emissions in tonnes CO2e per person.

    Args:
        emissions_df: DataFrame with emissions data (must include geography, year,
            emissions columns)
        population_df: DataFrame with population data (must include geography, year,
            population columns)
        emissions_col: Name of emissions column in kt CO2e
            (default: territorial_emissions_kt_co2e)
        population_col: Name of population column (default: population)
        geography_col: Name of geography code column
            (default: local_authority_code)
        year_col: Name of year column (default: calendar_year)

    Returns:
        DataFrame with original emissions columns plus
        'per_capita_emissions_t_co2e' column

    Raises:
        TransformationError: If required columns are missing or population data
            has zeros/nulls

    Example:
        >>> emissions = pl.DataFrame(
        ...     {
        ...         "local_authority_code": ["E06000023", "E06000022"],
        ...         "calendar_year": [2023, 2023],
        ...         "territorial_emissions_kt_co2e": [1000.0, 500.0],
        ...     }
        ... )
        >>> population = pl.DataFrame(
        ...     {
        ...         "local_authority_code": ["E06000023", "E06000022"],
        ...         "calendar_year": [2023, 2023],
        ...         "population": [500000, 200000],
        ...     }
        ... )
        >>> result = calculate_per_capita_emissions(emissions, population)
        >>> result["per_capita_emissions_t_co2e"][0]
        2.0
    """
    # Validate required columns
    required_emissions_cols = {geography_col, year_col, emissions_col}
    if not required_emissions_cols.issubset(emissions_df.columns):
        missing = required_emissions_cols - set(emissions_df.columns)
        raise TransformationError(
            f"Emissions DataFrame missing required columns: {missing}"
        )

    required_pop_cols = {geography_col, year_col, population_col}
    if not required_pop_cols.issubset(population_df.columns):
        missing = required_pop_cols - set(population_df.columns)
        raise TransformationError(
            f"Population DataFrame missing required columns: {missing}"
        )

    # Check for zero or null populations
    null_count = population_df.filter(
        pl.col(population_col).is_null() | (pl.col(population_col) <= 0)
    ).height

    if null_count > 0:
        raise TransformationError(
            f"Population data contains {null_count} rows with zero or null values",
            data_info=f"Check {population_col} column for data quality issues",
        )

    # Join emissions and population
    result = emissions_df.join(
        population_df.select([geography_col, year_col, population_col]),
        on=[geography_col, year_col],
        how="left",
    )

    # Calculate per capita (convert kt to t, then divide by population)
    result = result.with_columns(
        (pl.col(emissions_col) * 1000 / pl.col(population_col)).alias(
            "per_capita_emissions_t_co2e"
        )
    )

    return result


def calculate_emissions_per_km2(
    emissions_df: pl.DataFrame,
    area_df: pl.DataFrame,
    emissions_col: str = "territorial_emissions_kt_co2e",
    area_col: str = "area_km2",
    geography_col: str = "local_authority_code",
    year_col: str = "calendar_year",
) -> pl.DataFrame:
    """Calculate emissions density (kt CO2e per km²) by joining emissions and area data.

    Joins emissions and area datasets on geography and optionally year, then calculates
    emissions density in kt CO2e per km².

    Args:
        emissions_df: DataFrame with emissions data (must include geography, year,
            emissions columns)
        area_df: DataFrame with area data (must include geography, area columns)
        emissions_col: Name of emissions column in kt CO2e
            (default: territorial_emissions_kt_co2e)
        area_col: Name of area column in km² (default: area_km2)
        geography_col: Name of geography code column
            (default: local_authority_code)
        year_col: Name of year column (default: calendar_year)

    Returns:
        DataFrame with original emissions columns plus
        'emissions_per_km2_kt_co2e' column

    Raises:
        TransformationError: If required columns are missing or area data has
            zeros/nulls

    Example:
        >>> emissions = pl.DataFrame(
        ...     {
        ...         "local_authority_code": ["E06000023"],
        ...         "calendar_year": [2023],
        ...         "territorial_emissions_kt_co2e": [1000.0],
        ...     }
        ... )
        >>> area = pl.DataFrame(
        ...     {"local_authority_code": ["E06000023"], "area_km2": [110.0]}
        ... )
        >>> result = calculate_emissions_per_km2(emissions, area)
        >>> round(result["emissions_per_km2_kt_co2e"][0], 2)
        9.09
    """
    # Validate required columns
    required_emissions_cols = {geography_col, year_col, emissions_col}
    if not required_emissions_cols.issubset(emissions_df.columns):
        missing = required_emissions_cols - set(emissions_df.columns)
        raise TransformationError(
            f"Emissions DataFrame missing required columns: {missing}"
        )

    required_area_cols = {geography_col, area_col}
    if not required_area_cols.issubset(area_df.columns):
        missing = required_area_cols - set(area_df.columns)
        raise TransformationError(f"Area DataFrame missing required columns: {missing}")

    # Check for zero or null areas
    null_count = area_df.filter(
        pl.col(area_col).is_null() | (pl.col(area_col) <= 0)
    ).height

    if null_count > 0:
        raise TransformationError(
            f"Area data contains {null_count} rows with zero or null values",
            data_info=f"Check {area_col} column for data quality issues",
        )

    # Join emissions and area (area typically doesn't change by year)
    result = emissions_df.join(
        area_df.select([geography_col, area_col]),
        on=geography_col,
        how="left",
    )

    # Calculate emissions per km²
    result = result.with_columns(
        (pl.col(emissions_col) / pl.col(area_col)).alias("emissions_per_km2_kt_co2e")
    )

    return result


def aggregate_time_series(
    df: pl.DataFrame,
    group_cols: list[str],
    value_col: str,
    year_col: str = "calendar_year",
    agg_functions: list[str] | None = None,
) -> pl.DataFrame:
    """Aggregate time series data by specified grouping columns.

    Groups data by specified columns and calculates aggregations over time periods.
    Default aggregations: sum, mean, min, max, count.

    Args:
        df: DataFrame with time series data
        group_cols: List of columns to group by
            (e.g., ["local_authority_code", "sector"])
        value_col: Column to aggregate (e.g., "territorial_emissions_kt_co2e")
        year_col: Name of year column (default: calendar_year)
        agg_functions: List of aggregation functions to apply
            (options: "sum", "mean", "median", "min", "max", "count", "std")
            Default: ["sum", "mean", "min", "max", "count"]

    Returns:
        DataFrame with grouped data and aggregated values

    Raises:
        TransformationError: If required columns are missing or aggregation fails

    Example:
        >>> df = pl.DataFrame(
        ...     {
        ...         "local_authority_code": ["E06000023", "E06000023", "E06000022"],
        ...         "calendar_year": [2022, 2023, 2023],
        ...         "territorial_emissions_kt_co2e": [1000.0, 950.0, 500.0],
        ...     }
        ... )
        >>> result = aggregate_time_series(
        ...     df,
        ...     group_cols=["local_authority_code"],
        ...     value_col="territorial_emissions_kt_co2e",
        ... )
    """
    if agg_functions is None:
        agg_functions = ["sum", "mean", "min", "max", "count"]

    # Validate columns
    required_cols = set(group_cols + [value_col, year_col])
    if not required_cols.issubset(df.columns):
        missing = required_cols - set(df.columns)
        raise TransformationError(f"DataFrame missing required columns: {missing}")

    # Validate aggregation functions
    valid_aggs = {"sum", "mean", "median", "min", "max", "count", "std"}
    invalid_aggs = set(agg_functions) - valid_aggs
    if invalid_aggs:
        raise TransformationError(
            f"Invalid aggregation functions: {invalid_aggs}. "
            f"Valid options: {valid_aggs}"
        )

    # Build aggregation expressions
    agg_exprs = []
    for agg_func in agg_functions:
        if agg_func == "sum":
            agg_exprs.append(pl.col(value_col).sum().alias(f"{value_col}_sum"))
        elif agg_func == "mean":
            agg_exprs.append(pl.col(value_col).mean().alias(f"{value_col}_mean"))
        elif agg_func == "median":
            agg_exprs.append(pl.col(value_col).median().alias(f"{value_col}_median"))
        elif agg_func == "min":
            agg_exprs.append(pl.col(value_col).min().alias(f"{value_col}_min"))
        elif agg_func == "max":
            agg_exprs.append(pl.col(value_col).max().alias(f"{value_col}_max"))
        elif agg_func == "count":
            agg_exprs.append(pl.col(value_col).count().alias(f"{value_col}_count"))
        elif agg_func == "std":
            agg_exprs.append(pl.col(value_col).std().alias(f"{value_col}_std"))

    # Also calculate year range
    agg_exprs.extend(
        [
            pl.col(year_col).min().alias("year_start"),
            pl.col(year_col).max().alias("year_end"),
            pl.col(year_col).count().alias("year_count"),
        ]
    )

    # Perform aggregation
    try:
        result = df.group_by(group_cols).agg(agg_exprs)
    except Exception as e:
        raise TransformationError(f"Aggregation failed: {e}") from e

    return result


def aggregate_geographic(
    df: pl.DataFrame,
    lookup_df: pl.DataFrame,
    from_geography_col: str,
    to_geography_col: str,
    value_cols: list[str],
    year_col: str = "calendar_year",
) -> pl.DataFrame:
    """Aggregate data from smaller to larger geographic units.

    Aggregates data from a lower geographic level (e.g., LSOA) to a higher level
    (e.g., LA or CA) using a lookup table.

    Args:
        df: DataFrame with data at lower geographic level
        lookup_df: Lookup DataFrame mapping from_geography to to_geography
        from_geography_col: Column name in df for source geography (e.g., "lsoa21cd")
        to_geography_col: Column name in lookup for target geography (e.g., "lad25cd")
        value_cols: List of numeric columns to aggregate (will be summed)
        year_col: Name of year column (default: calendar_year)

    Returns:
        DataFrame aggregated to the higher geographic level

    Raises:
        TransformationError: If required columns are missing or join fails

    Example:
        >>> lsoa_data = pl.DataFrame(
        ...     {
        ...         "lsoa21cd": ["E01000001", "E01000002"],
        ...         "calendar_year": [2023, 2023],
        ...         "emissions": [10.0, 15.0],
        ...     }
        ... )
        >>> lookup = pl.DataFrame(
        ...     {
        ...         "lsoa21cd": ["E01000001", "E01000002"],
        ...         "lad25cd": ["E06000023", "E06000023"],
        ...     }
        ... )
        >>> result = aggregate_geographic(
        ...     lsoa_data, lookup, "lsoa21cd", "lad25cd", ["emissions"]
        ... )
        >>> result["emissions"][0]
        25.0
    """
    # Validate columns
    required_df_cols = {from_geography_col, year_col} | set(value_cols)
    if not required_df_cols.issubset(df.columns):
        missing = required_df_cols - set(df.columns)
        raise TransformationError(f"Data DataFrame missing required columns: {missing}")

    required_lookup_cols = {from_geography_col, to_geography_col}
    if not required_lookup_cols.issubset(lookup_df.columns):
        missing = required_lookup_cols - set(lookup_df.columns)
        raise TransformationError(
            f"Lookup DataFrame missing required columns: {missing}"
        )

    # Check that value columns are numeric
    for col in value_cols:
        if df[col].dtype not in [
            pl.Float32,
            pl.Float64,
            pl.Int8,
            pl.Int16,
            pl.Int32,
            pl.Int64,
            pl.UInt8,
            pl.UInt16,
            pl.UInt32,
            pl.UInt64,
        ]:
            raise TransformationError(
                f"Column '{col}' must be numeric for aggregation, got {df[col].dtype}"
            )

    # Join with lookup to get target geography
    try:
        joined = df.join(
            lookup_df.select([from_geography_col, to_geography_col]),
            on=from_geography_col,
            how="left",
        )
    except Exception as e:
        raise TransformationError(f"Failed to join with lookup table: {e}") from e

    # Check for unmatched geographies
    null_count = joined.filter(pl.col(to_geography_col).is_null()).height
    if null_count > 0:
        raise TransformationError(
            f"{null_count} rows could not be mapped to target geography",
            data_info=(
                f"Check that all {from_geography_col} values exist in lookup table"
            ),
        )

    # Aggregate to target geography
    group_cols = [to_geography_col, year_col]
    agg_exprs = [pl.col(col).sum().alias(col) for col in value_cols]

    try:
        result = (
            joined.group_by(group_cols)
            .agg(agg_exprs)
            .sort([year_col, to_geography_col])
        )
    except Exception as e:
        raise TransformationError(f"Geographic aggregation failed: {e}") from e

    return result


def aggregate_sectors(
    df: pl.DataFrame,
    sector_col: str,
    value_col: str,
    group_cols: list[str] | None = None,
    year_col: str = "calendar_year",
) -> pl.DataFrame:
    """Aggregate emissions data by sector.

    Groups data by sector (and optionally other columns like geography, year)
    and sums emissions values.

    Args:
        df: DataFrame with sectoral emissions data
        sector_col: Column name for sector (e.g., "la_ghg_sector")
        value_col: Column name for emissions value to aggregate
        group_cols: Additional columns to group by (e.g., ["local_authority_code"])
            If None, groups by sector and year only
        year_col: Name of year column (default: calendar_year)

    Returns:
        DataFrame with sectoral aggregations

    Raises:
        TransformationError: If required columns are missing

    Example:
        >>> df = pl.DataFrame(
        ...     {
        ...         "local_authority_code": ["E06000023", "E06000023"],
        ...         "calendar_year": [2023, 2023],
        ...         "la_ghg_sector": ["Transport", "Domestic"],
        ...         "territorial_emissions_kt_co2e": [300.0, 400.0],
        ...     }
        ... )
        >>> result = aggregate_sectors(
        ...     df,
        ...     sector_col="la_ghg_sector",
        ...     value_col="territorial_emissions_kt_co2e",
        ...     group_cols=["local_authority_code"],
        ... )
    """
    if group_cols is None:
        group_cols = []

    # Validate columns
    required_cols = {sector_col, value_col, year_col} | set(group_cols)
    if not required_cols.issubset(df.columns):
        missing = required_cols - set(df.columns)
        raise TransformationError(f"DataFrame missing required columns: {missing}")

    # Check that value column is numeric
    if df[value_col].dtype not in [
        pl.Float32,
        pl.Float64,
        pl.Int8,
        pl.Int16,
        pl.Int32,
        pl.Int64,
        pl.UInt8,
        pl.UInt16,
        pl.UInt32,
        pl.UInt64,
    ]:
        raise TransformationError(
            f"Value column '{value_col}' must be numeric, got {df[value_col].dtype}"
        )

    # Build grouping columns
    final_group_cols = [sector_col, year_col] + group_cols

    # Aggregate
    try:
        result = (
            df.group_by(final_group_cols)
            .agg(
                [
                    pl.col(value_col).sum().alias(f"{value_col}_total"),
                    pl.col(value_col).count().alias("record_count"),
                ]
            )
            .sort([year_col, sector_col] + group_cols)
        )
    except Exception as e:
        raise TransformationError(f"Sector aggregation failed: {e}") from e

    return result
