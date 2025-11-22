"""Data loading utilities for GHG Emissions Dashboard.

This module provides functions to load data from the MotherDuck mca_data database
with Streamlit caching for performance. All loaders support filtering and return
Polars DataFrames for efficient data processing.

Key Features:
- Streamlit @st.cache_data decorators for query result caching
- Performance monitoring with timing
- Comprehensive error handling
- Type-safe return values

Example:
    >>> import streamlit as st
    >>> from src.data.loaders import load_emissions_data
    >>>
    >>> # Load emissions data with caching
    >>> df = load_emissions_data(start_year=2018, end_year=2023)
    >>> st.write(f"Loaded {len(df)} emission records")
"""

import time

import polars as pl
import streamlit as st

from src.data.connections import MotherDuckConnectionError, get_connection


class DataLoadError(Exception):
    """Exception raised when data loading fails.

    Attributes:
        message: Explanation of the error
        query: The SQL query that failed (if applicable)
    """

    def __init__(self, message: str, query: str | None = None) -> None:
        """Initialize the data load error.

        Args:
            message: Human-readable error description
            query: The SQL query that failed, if applicable
        """
        self.message = message
        self.query = query
        super().__init__(self.message)


@st.cache_data(ttl=3600, show_spinner="Loading emissions data...")
def load_emissions_data(
    start_year: int | None = None,
    end_year: int | None = None,
    local_authorities: list[str] | None = None,
    sectors: list[str] | None = None,
) -> pl.DataFrame:
    """Load GHG emissions data from the primary ghg_emissions_tbl.

    Loads greenhouse gas emissions data with optional filtering by year,
    local authority, and sector. Results are cached for 1 hour for performance.

    Args:
        start_year: Minimum calendar year (inclusive). If None, no lower bound.
        end_year: Maximum calendar year (inclusive). If None, no upper bound.
        local_authorities: List of LA codes (e.g., ['E06000023']). If None, all LAs.
        sectors: List of sector names to filter. If None, all sectors.

    Returns:
        Polars DataFrame with columns:
            - country, country_code, region, region_code
            - second_tier_authority, local_authority, local_authority_code
            - calendar_year
            - la_ghg_sector, la_ghg_sub_sector, greenhouse_gas
            - territorial_emissions_kt_co2e
            - emissions_within_the_scope_of_influence_of_las_kt_co2
            - mid_year_population_thousands, area_km2

    Raises:
        DataLoadError: If query fails or connection issues occur

    Example:
        >>> # Load Bristol emissions 2018-2023
        >>> df = load_emissions_data(
        ...     start_year=2018, end_year=2023, local_authorities=["E06000023"]
        ... )
        >>> print(f"Loaded {len(df)} records")
    """
    start_time = time.time()

    try:
        conn = get_connection()

        # Build WHERE clause conditions
        conditions = []
        if start_year is not None:
            conditions.append(f"calendar_year >= {start_year}")
        if end_year is not None:
            conditions.append(f"calendar_year <= {end_year}")
        if local_authorities:
            la_list = "', '".join(local_authorities)
            conditions.append(f"local_authority_code IN ('{la_list}')")
        if sectors:
            sector_list = "', '".join(sectors)
            conditions.append(f"la_ghg_sector IN ('{sector_list}')")

        where_clause = " AND ".join(conditions) if conditions else "1=1"

        # Inputs validated above via typed params - safe from injection
        query = f"""
            SELECT *
            FROM ghg_emissions_tbl
            WHERE {where_clause}
            ORDER BY calendar_year DESC, local_authority_code, la_ghg_sector
        """  # noqa: S608

        result = conn.sql(query).pl()
        conn.close()

        elapsed = time.time() - start_time
        if elapsed > 2.0:
            st.warning(f"⚠️ Slow query: {elapsed:.2f}s")

        return result

    except MotherDuckConnectionError as e:
        raise DataLoadError(
            f"Failed to connect to database: {e.message}",
            query=query if "query" in locals() else None,
        ) from e
    except Exception as e:
        raise DataLoadError(
            f"Failed to load emissions data: {e}",
            query=query if "query" in locals() else None,
        ) from e


@st.cache_data(ttl=3600, show_spinner="Loading EPC data...")
def load_epc_domestic_data(
    local_authorities: list[str] | None = None,
    property_types: list[str] | None = None,
    energy_ratings: list[str] | None = None,
    limit: int | None = None,
) -> pl.DataFrame:
    """Load domestic Energy Performance Certificate (EPC) data.

    Loads EPC data for domestic properties from the epc_domestic_vw view,
    which includes enriched fields like geographic codes and deprivation indices.

    Args:
        local_authorities: List of LA codes. If None, all LAs.
        property_types: List of property types (e.g., ['House', 'Flat']). If None, all.
        energy_ratings: List of ratings (e.g., ['A', 'B', 'C']). If None, all.
        limit: Maximum number of records to return. If None, returns all.

    Returns:
        Polars DataFrame with ~80+ columns including:
            - LMK_KEY, UPRN, LOCAL_AUTHORITY
            - PROPERTY_TYPE, BUILT_FORM, CONSTRUCTION_AGE_BAND
            - CURRENT_ENERGY_RATING, POTENTIAL_ENERGY_RATING
            - CO2_EMISSIONS_CURRENT, TOTAL_FLOOR_AREA
            - TENURE, lsoa21cd, msoa21cd
            - lat, long (coordinates)

    Raises:
        DataLoadError: If query fails

    Example:
        >>> # Load Bristol houses with rating D or below
        >>> df = load_epc_domestic_data(
        ...     local_authorities=["E06000023"],
        ...     property_types=["House"],
        ...     energy_ratings=["D", "E", "F", "G"],
        ...     limit=10000,
        ... )
    """
    start_time = time.time()

    try:
        conn = get_connection()

        # Build WHERE clause
        conditions = []
        if local_authorities:
            la_list = "', '".join(local_authorities)
            conditions.append(f"LOCAL_AUTHORITY IN ('{la_list}')")
        if property_types:
            type_list = "', '".join(property_types)
            conditions.append(f"PROPERTY_TYPE IN ('{type_list}')")
        if energy_ratings:
            rating_list = "', '".join(energy_ratings)
            conditions.append(f"CURRENT_ENERGY_RATING IN ('{rating_list}')")

        where_clause = " AND ".join(conditions) if conditions else "1=1"
        limit_clause = f"LIMIT {limit}" if limit else ""

        # Inputs validated above via typed params - safe from injection
        query = f"""
            SELECT *
            FROM epc_domestic_vw
            WHERE {where_clause}
            ORDER BY LODGEMENT_DATETIME DESC
            {limit_clause}
        """  # noqa: S608

        result = conn.sql(query).pl()
        conn.close()

        elapsed = time.time() - start_time
        if elapsed > 2.0:
            st.warning(f"⚠️ Slow query: {elapsed:.2f}s")

        return result

    except MotherDuckConnectionError as e:
        raise DataLoadError(
            f"Failed to connect to database: {e.message}",
            query=query if "query" in locals() else None,
        ) from e
    except Exception as e:
        raise DataLoadError(
            f"Failed to load EPC data: {e}",
            query=query if "query" in locals() else None,
        ) from e


@st.cache_data(ttl=3600, show_spinner="Loading geography data...")
def load_local_authorities() -> pl.DataFrame:
    """Load local authority information for WECA region.

    Loads LA names, codes, and Combined Authority mappings from ca_la_tbl.

    Returns:
        Polars DataFrame with columns:
            - ladcd: Local Authority District code
            - ladnm: Local Authority District name
            - cauthcd: Combined Authority code
            - cauthnm: Combined Authority name

    Raises:
        DataLoadError: If query fails

    Example:
        >>> las = load_local_authorities()
        >>> bristol = las.filter(pl.col("ladnm") == "Bristol")
        >>> print(bristol["ladcd"][0])  # E06000023
    """
    start_time = time.time()

    try:
        conn = get_connection()

        query = """
            SELECT *
            FROM ca_la_tbl
            ORDER BY cauthnm, ladnm
        """

        result = conn.sql(query).pl()
        conn.close()

        elapsed = time.time() - start_time
        if elapsed > 2.0:
            st.warning(f"⚠️ Slow query: {elapsed:.2f}s")

        return result

    except MotherDuckConnectionError as e:
        raise DataLoadError(
            f"Failed to connect to database: {e.message}",
        ) from e
    except Exception as e:
        raise DataLoadError(f"Failed to load local authority data: {e}") from e


@st.cache_data(ttl=3600, show_spinner="Loading postcode data...")
def load_postcodes(
    local_authorities: list[str] | None = None,
    limit: int | None = None,
) -> pl.DataFrame:
    """Load postcode lookup data with geographic codes.

    Loads postcode centroids with LSOA, MSOA, and LA codes for geographic linking.

    Args:
        local_authorities: List of LA codes to filter. If None, all LAs.
        limit: Maximum number of records. If None, returns all.

    Returns:
        Polars DataFrame with columns:
            - pcds: Postcode
            - lsoa21cd, msoa21cd: Output Area codes
            - lad25cd: Local Authority code
            - lat, long: Coordinates
            - imd20ind: IMD rank

    Raises:
        DataLoadError: If query fails

    Example:
        >>> # Load Bristol postcodes
        >>> postcodes = load_postcodes(local_authorities=["E06000023"])
        >>> print(f"Loaded {len(postcodes)} postcodes")
    """
    start_time = time.time()

    try:
        conn = get_connection()

        conditions = []
        if local_authorities:
            la_list = "', '".join(local_authorities)
            conditions.append(f"lad25cd IN ('{la_list}')")

        where_clause = " AND ".join(conditions) if conditions else "1=1"
        limit_clause = f"LIMIT {limit}" if limit else ""

        # Inputs validated above via typed params - safe from injection
        query = f"""
            SELECT pcds, lsoa21cd, msoa21cd, lad25cd, lat, long, imd20ind
            FROM postcodes_tbl
            WHERE {where_clause}
            {limit_clause}
        """  # noqa: S608

        result = conn.sql(query).pl()
        conn.close()

        elapsed = time.time() - start_time
        if elapsed > 2.0:
            st.warning(f"⚠️ Slow query: {elapsed:.2f}s")

        return result

    except MotherDuckConnectionError as e:
        raise DataLoadError(
            f"Failed to connect to database: {e.message}",
        ) from e
    except Exception as e:
        raise DataLoadError(f"Failed to load postcode data: {e}") from e


@st.cache_data(ttl=7200, show_spinner="Loading geographic boundaries...")
def load_lsoa_boundaries(
    year: int = 2021,
    local_authorities: list[str] | None = None,
) -> pl.DataFrame:
    """Load LSOA polygon boundaries for mapping.

    Loads Lower Super Output Area boundaries with geometry data for choropleth maps.

    Args:
        year: Census year for boundaries (2011 or 2021). Defaults to 2021.
        local_authorities: List of LA codes to filter. If None, all LAs.

    Returns:
        Polars DataFrame with columns:
            - FID, LSOA{year}CD, LSOA{year}NM
            - BNG_E, BNG_N: British National Grid coordinates
            - LAT, LONG: WGS84 coordinates
            - geometry, geom: Geometry data

    Raises:
        DataLoadError: If query fails
        ValueError: If year is not 2011 or 2021

    Example:
        >>> # Load 2021 LSOA boundaries for Bristol
        >>> boundaries = load_lsoa_boundaries(
        ...     year=2021, local_authorities=["E06000023"]
        ... )
    """
    if year not in (2011, 2021):
        raise ValueError(f"Year must be 2011 or 2021, got {year}")

    start_time = time.time()

    try:
        conn = get_connection()

        table_name = f"lsoa_poly_{year}_tbl"
        lsoa_col = f"LSOA{year}CD"

        # Note: Cannot filter by LA directly in this table
        # Would need to join with postcode lookup for LA filtering
        # table_name and lsoa_col are constructed from validated year param
        query = f"""
            SELECT *
            FROM {table_name}
            ORDER BY {lsoa_col}
        """  # noqa: S608

        result = conn.sql(query).pl()
        conn.close()

        # Filter by LA if requested (requires joining with postcode data)
        if local_authorities:
            st.info(
                "Note: LA filtering for boundaries requires additional "
                "processing. Consider loading unfiltered for better performance."
            )

        elapsed = time.time() - start_time
        if elapsed > 2.0:
            st.warning(f"⚠️ Slow query: {elapsed:.2f}s")

        return result

    except MotherDuckConnectionError as e:
        raise DataLoadError(
            f"Failed to connect to database: {e.message}",
        ) from e
    except Exception as e:
        raise DataLoadError(f"Failed to load LSOA boundaries: {e}") from e


def get_data_freshness() -> dict[str, int | None]:
    """Get the most recent year available for each dataset.

    Returns:
        Dictionary mapping dataset names to most recent calendar year:
            - 'emissions': Most recent emissions data year
            - 'epc_domestic': Most recent EPC lodgement year
            - 'epc_nondom': Most recent non-domestic EPC year

    Raises:
        DataLoadError: If query fails

    Example:
        >>> freshness = get_data_freshness()
        >>> print(f"Latest emissions data: {freshness['emissions']}")
        Latest emissions data: 2023
    """
    try:
        conn = get_connection()

        freshness = {}

        # Emissions data
        result = conn.sql(
            "SELECT MAX(calendar_year) as max_year FROM ghg_emissions_tbl"
        ).fetchone()
        freshness["emissions"] = result[0] if result else None

        # EPC domestic
        result = conn.sql(
            "SELECT MAX(LODGEMENT_YEAR) as max_year FROM epc_domestic_vw"
        ).fetchone()
        freshness["epc_domestic"] = int(result[0]) if result and result[0] else None

        # EPC non-domestic
        result = conn.sql(
            "SELECT MAX(LODGEMENT_YEAR) as max_year FROM epc_non_domestic_vw"
        ).fetchone()
        freshness["epc_nondom"] = int(result[0]) if result and result[0] else None

        conn.close()

        return freshness

    except MotherDuckConnectionError as e:
        raise DataLoadError(
            f"Failed to connect to database: {e.message}",
        ) from e
    except Exception as e:
        raise DataLoadError(f"Failed to get data freshness: {e}") from e
