"""Mock data generators for local development and testing.

This module provides sample data that matches the MotherDuck schema when
the database is unavailable or for offline development.

Usage:
    from src.data.mock_data import load_emissions_data_with_fallback
    df = load_emissions_data_with_fallback(start_year=2019, end_year=2023)
"""

from datetime import datetime

import polars as pl
import streamlit as st


def get_mock_local_authorities() -> pl.DataFrame:
    """Generate mock local authority lookup data.

    Returns:
        DataFrame with columns: la_code, la_name, region, population
    """
    data = {
        "la_code": ["E06000022", "E06000023", "E06000025", "E06000024"],
        "la_name": [
            "Bath and North East Somerset",
            "Bristol",
            "South Gloucestershire",
            "North Somerset",
        ],
        "region": [
            "South West",
            "South West",
            "South West",
            "South West",
        ],
        "population": [193000, 463000, 285000, 215000],
    }
    return pl.DataFrame(data)


def get_mock_emissions_data(
    start_year: int = 2019,
    end_year: int = 2023,
    local_authorities: list[str] | None = None,
    sectors: list[str] | None = None,
) -> pl.DataFrame:
    """Generate mock emissions data matching the schema.

    Args:
        start_year: Starting year for data
        end_year: Ending year for data
        local_authorities: Filter to specific LAs (names)
        sectors: Filter to specific sectors

    Returns:
        DataFrame with emissions data matching expected schema
    """
    # Default local authorities
    all_las = [
        "Bath and North East Somerset",
        "Bristol",
        "South Gloucestershire",
        "North Somerset",
    ]
    if local_authorities:
        las = [la for la in all_las if la in local_authorities]
    else:
        las = all_las

    # Default sectors (all 8 sectors from ghg_emissions_tbl)
    all_sectors = [
        "Industry",
        "Commercial",
        "Public Sector",
        "Domestic",
        "Transport",
        "Agriculture",
        "LULUCF",
        "Waste",
    ]
    sector_list = [s for s in all_sectors if s in sectors] if sectors else all_sectors

    # Base emissions by LA and sector (kt CO2e for 2023)
    base_emissions = {
        "Bath and North East Somerset": {
            "Industry": 150,
            "Commercial": 120,
            "Public Sector": 45,
            "Domestic": 380,
            "Transport": 420,
            "Agriculture": 25,
            "LULUCF": -15,
            "Waste": 35,
        },
        "Bristol": {
            "Industry": 580,
            "Commercial": 650,
            "Public Sector": 180,
            "Domestic": 890,
            "Transport": 920,
            "Agriculture": 10,
            "LULUCF": -35,
            "Waste": 95,
        },
        "South Gloucestershire": {
            "Industry": 420,
            "Commercial": 290,
            "Public Sector": 95,
            "Domestic": 580,
            "Transport": 680,
            "Agriculture": 45,
            "LULUCF": -25,
            "Waste": 55,
        },
        "North Somerset": {
            "Industry": 210,
            "Commercial": 180,
            "Public Sector": 65,
            "Domestic": 450,
            "Transport": 520,
            "Agriculture": 55,
            "LULUCF": -20,
            "Waste": 40,
        },
    }

    # Population data for per capita calculations
    populations = {
        "Bath and North East Somerset": 193000,
        "Bristol": 463000,
        "South Gloucestershire": 285000,
        "North Somerset": 215000,
    }

    # Area data for per km2 calculations
    areas_km2 = {
        "Bath and North East Somerset": 346,
        "Bristol": 110,
        "South Gloucestershire": 497,
        "North Somerset": 374,
    }

    # Generate data for each year, LA, and sector
    rows = []
    for year in range(start_year, end_year + 1):
        # Simulate declining emissions over time (2-5% per year)
        year_factor = 1.0 - (0.03 * (end_year - year))

        for la in las:
            for sector in sector_list:
                total_emissions = base_emissions[la][sector] * year_factor
                population = populations[la]
                area = areas_km2[la]

                # Add some realistic variation
                import random

                random.seed(hash(f"{year}{la}{sector}"))
                variation = random.uniform(0.95, 1.05)  # noqa: S311
                total_emissions *= variation

                per_capita = (total_emissions * 1000) / population  # tonnes per person
                per_km2 = (total_emissions * 1000) / area  # tonnes per km2

                rows.append(
                    {
                        "calendar_year": year,
                        "la_name": la,
                        "sector": sector,
                        "total_emissions": round(total_emissions, 2),
                        "per_capita": round(per_capita, 2),
                        "per_km2": round(per_km2, 2),
                    }
                )

    return pl.DataFrame(rows)


def get_mock_data_freshness() -> dict[str, int]:
    """Get mock data freshness indicators.

    Returns:
        Dictionary mapping dataset names to most recent year
    """
    current_year = datetime.now().year
    return {
        "emissions": current_year - 2,  # Emissions data has 18-month lag
        "epc_domestic": current_year - 1,
        "epc_nondom": current_year - 1,
        "population": current_year - 1,
        "geography": current_year - 1,
    }


def get_mock_ca_emissions_evidence() -> pl.DataFrame:
    """Generate mock Combined Authority level emissions data.

    Returns:
        DataFrame with CA-level aggregated emissions
    """
    years = range(2014, 2024)
    rows = []

    # WECA total (sum of 3 constituent LAs)
    base_weca = 4200  # kt CO2e in 2023

    for year in years:
        year_factor = 1.0 - (0.03 * (2023 - year))
        total = base_weca * year_factor

        rows.append(
            {
                "calendar_year": year,
                "ca_name": "West of England",
                "total_emissions": round(total, 2),
                "per_capita": round((total * 1000) / 941000, 2),  # WECA pop
            }
        )

    return pl.DataFrame(rows)


# Fallback wrappers that try real data first, then mock data
def load_emissions_data_with_fallback(
    start_year: int | None = None,
    end_year: int | None = None,
    local_authorities: list[str] | None = None,
    sectors: list[str] | None = None,
) -> tuple[pl.DataFrame, bool]:
    """Load emissions data with automatic fallback to mock data.

    Tries to load from MotherDuck first. If connection fails, falls back to
    mock data and displays a warning to the user.

    Args:
        start_year: Minimum calendar year
        end_year: Maximum calendar year
        local_authorities: List of LA names (not codes) to filter
        sectors: List of sector names to filter

    Returns:
        Tuple of (DataFrame, is_mock_data_boolean)
    """
    from src.data.connections import MotherDuckConnectionError
    from src.data.loaders import load_emissions_data, load_local_authorities

    try:
        # Convert LA names to codes for the query
        la_codes = None
        if local_authorities:
            # Load LA lookup table
            las_df = load_local_authorities()
            # Create name to code mapping
            if "ladnm" in las_df.columns and "ladcd" in las_df.columns:
                name_to_code = dict(
                    zip(
                        las_df["ladnm"].to_list(),
                        las_df["ladcd"].to_list(),
                        strict=False,
                    )
                )
                # Convert selected names to codes
                la_codes = [
                    name_to_code.get(la_name, la_name) for la_name in local_authorities
                ]
            else:
                # If columns don't match expected, try as-is
                la_codes = local_authorities

        # Try to load real data with LA codes
        df = load_emissions_data(
            start_year=start_year,
            end_year=end_year,
            local_authorities=la_codes,
            sectors=sectors,
        )
        # Standardize column names to match mock data format
        if "local_authority" in df.columns:
            df = df.rename({"local_authority": "la_name"})
        if "la_ghg_sector" in df.columns:
            df = df.rename({"la_ghg_sector": "sector"})

        # Aggregate sub-sectors to sector level to avoid double counting
        # ghg_emissions_tbl has rows for each sub-sector; we need to sum them by sector
        if "la_ghg_sub_sector" in df.columns and not df.is_empty():
            group_cols = [
                "la_name",
                "local_authority_code",
                "calendar_year",
                "sector",
            ]
            # Aggregate by sector (sum emissions, take first for other fields)
            agg_exprs = [pl.sum("territorial_emissions_kt_co2e")]
            if "mid_year_population_thousands" in df.columns:
                agg_exprs.append(pl.first("mid_year_population_thousands"))
            if "area_km2" in df.columns:
                agg_exprs.append(pl.first("area_km2"))

            df = df.group_by(group_cols).agg(agg_exprs)

        # Add calculated metric columns to match mock data format
        if "territorial_emissions_kt_co2e" in df.columns:
            # total_emissions is the same as territorial_emissions
            df = df.with_columns(
                pl.col("territorial_emissions_kt_co2e").alias("total_emissions")
            )

            # Calculate per capita if population data available
            if "mid_year_population_thousands" in df.columns:
                df = df.with_columns(
                    (
                        pl.col("territorial_emissions_kt_co2e")
                        * 1000
                        / (pl.col("mid_year_population_thousands") * 1000)
                    ).alias("per_capita")
                )

            # Calculate per km2 if area data available
            if "area_km2" in df.columns:
                df = df.with_columns(
                    (
                        pl.col("territorial_emissions_kt_co2e")
                        * 1000
                        / pl.col("area_km2")
                    ).alias("per_km2")
                )

        return df, False  # Real data

    except MotherDuckConnectionError as e:
        # Fall back to mock data
        st.warning(
            f"""
            ### ⚠️ Using Mock Data

            **Database connection failed**: {e.message}

            Showing sample WECA emissions data for development.
            The dashboard is fully functional but using mock data.

            **To use real data**: Ensure MotherDuck is available and `.env` has a
            valid `MOTHERDUCK_TOKEN`, then refresh.
            """
        )
        df = get_mock_emissions_data(
            start_year=start_year or 2014,
            end_year=end_year or 2023,
            local_authorities=local_authorities,
            sectors=sectors,
        )
        return df, True  # Mock data


def load_local_authorities_with_fallback() -> tuple[pl.DataFrame, bool]:
    """Load local authority data with automatic fallback to mock data.

    Returns:
        Tuple of (DataFrame, is_mock_data_boolean)
    """
    from src.data.connections import MotherDuckConnectionError
    from src.data.loaders import load_local_authorities

    try:
        # Try to load real data
        df = load_local_authorities()
        # Standardize column names
        if "ladnm" in df.columns:
            df = df.rename({"ladnm": "la_name"})
        return df, False  # Real data

    except MotherDuckConnectionError:
        # Fall back to mock data (warning already shown by emissions loader)
        df = get_mock_local_authorities()
        return df, True  # Mock data


@st.cache_data(ttl=3600, show_spinner=False)
def get_emissions_year_range() -> tuple[int, int, bool]:
    """Get the available year range from emissions data.

    Queries the database to find the min and max calendar years available.
    Falls back to default range if database unavailable.

    Returns:
        Tuple of (min_year, max_year, is_mock_data)
    """
    from src.data.connections import MotherDuckConnectionError, get_connection

    try:
        conn = get_connection()
        result = conn.sql("""
            SELECT MIN(calendar_year) as min_year, MAX(calendar_year) as max_year
            FROM ghg_emissions_tbl
        """).fetchone()
        conn.close()

        if result and result[0] is not None:
            return int(result[0]), int(result[1]), False
        return 2005, 2023, True  # Fallback if no data

    except MotherDuckConnectionError:
        return 2005, 2023, True  # Mock fallback range


@st.cache_data(ttl=3600, show_spinner=False)
def get_emissions_sectors() -> tuple[list[str], bool]:
    """Get the available sectors from emissions data.

    Queries the database to find all distinct sectors available.
    Falls back to default sectors if database unavailable.

    Returns:
        Tuple of (list of sector names, is_mock_data)
    """
    from src.data.connections import MotherDuckConnectionError, get_connection

    # Default sectors matching the schema
    default_sectors = [
        "Industry",
        "Commercial",
        "Public Sector",
        "Domestic",
        "Transport",
        "Agriculture",
        "LULUCF",
        "Waste",
    ]

    try:
        conn = get_connection()
        result = conn.sql("""
            SELECT DISTINCT la_ghg_sector
            FROM ghg_emissions_tbl
            WHERE la_ghg_sector IS NOT NULL
            ORDER BY la_ghg_sector
        """).fetchall()
        conn.close()

        if result:
            sectors = [row[0] for row in result]
            return sectors, False
        return default_sectors, True  # Fallback if no data

    except MotherDuckConnectionError:
        return default_sectors, True  # Mock fallback


# =============================================================================
# EPC Mock Data Generators
# =============================================================================


def get_mock_epc_domestic_data(
    local_authorities: list[str] | None = None,
    energy_ratings: list[str] | None = None,
    property_types: list[str] | None = None,
    tenures: list[str] | None = None,
    sample_size: int = 5000,
) -> pl.DataFrame:
    """Generate mock domestic EPC data matching the schema.

    Args:
        local_authorities: Filter to specific LA names
        energy_ratings: Filter to specific energy ratings (A-G)
        property_types: Filter to specific property types
        tenures: Filter to specific tenure types
        sample_size: Number of records to generate

    Returns:
        DataFrame with mock EPC domestic data
    """
    import random

    # LA mapping (name to code)
    la_mapping = {
        "Bath and North East Somerset": "E06000022",
        "Bristol": "E06000023",
        "South Gloucestershire": "E06000025",
        "North Somerset": "E06000024",
    }

    # Filter LAs
    if local_authorities:
        las = {k: v for k, v in la_mapping.items() if k in local_authorities}
    else:
        las = la_mapping

    # Distributions based on typical UK EPC data
    all_ratings = ["A", "B", "C", "D", "E", "F", "G"]
    rating_weights = [0.02, 0.12, 0.35, 0.32, 0.12, 0.05, 0.02]  # Realistic UK dist

    all_property_types = ["House", "Flat", "Bungalow", "Maisonette", "Park home"]
    property_weights = [0.55, 0.30, 0.10, 0.04, 0.01]

    all_built_forms = [
        "Detached",
        "Semi-Detached",
        "Mid-Terrace",
        "End-Terrace",
        "Enclosed Mid-Terrace",
        "Enclosed End-Terrace",
    ]
    built_form_weights = [0.22, 0.28, 0.22, 0.15, 0.08, 0.05]

    all_tenures = ["Owner occupied", "Private rented", "Social rented"]
    tenure_weights = [0.63, 0.20, 0.17]

    all_age_bands = [
        "before 1900",
        "1900-1929",
        "1930-1949",
        "1950-1966",
        "1967-1975",
        "1976-1982",
        "1983-1990",
        "1991-1995",
        "1996-2002",
        "2003-2006",
        "2007-2011",
        "2012 onwards",
    ]
    age_band_weights = [
        0.08,
        0.10,
        0.12,
        0.15,
        0.10,
        0.08,
        0.08,
        0.06,
        0.08,
        0.05,
        0.05,
        0.05,
    ]

    # Mapping from age band to construction epoch (cleaned/categorized)
    age_band_to_epoch = {
        "before 1900": "Pre-1900",
        "1900-1929": "1900-1929",
        "1930-1949": "1930-1949",
        "1950-1966": "1950-1966",
        "1967-1975": "1967-1982",
        "1976-1982": "1967-1982",
        "1983-1990": "1983-1995",
        "1991-1995": "1983-1995",
        "1996-2002": "1996-2006",
        "2003-2006": "1996-2006",
        "2007-2011": "2007-present",
        "2012 onwards": "2007-present",
    }

    # Mapping from age band to nominal construction year (mid-point)
    age_band_to_year = {
        "before 1900": 1890,
        "1900-1929": 1915,
        "1930-1949": 1940,
        "1950-1966": 1958,
        "1967-1975": 1971,
        "1976-1982": 1979,
        "1983-1990": 1987,
        "1991-1995": 1993,
        "1996-2002": 1999,
        "2003-2006": 2005,
        "2007-2011": 2009,
        "2012 onwards": 2018,
    }

    all_main_fuels = [
        "mains gas",
        "electricity",
        "oil",
        "LPG",
        "solid fuel",
        "biomass",
    ]
    fuel_weights = [0.78, 0.12, 0.05, 0.02, 0.02, 0.01]

    # SAP rating ranges by energy band
    sap_ranges = {
        "A": (92, 100),
        "B": (81, 91),
        "C": (69, 80),
        "D": (55, 68),
        "E": (39, 54),
        "F": (21, 38),
        "G": (1, 20),
    }

    # Generate mock data
    rows = []
    random.seed(42)  # Reproducible

    for i in range(sample_size):
        # Select LA with weighted distribution (Bristol larger)
        la_names = list(las.keys())
        la_weights = [0.40, 0.25, 0.20, 0.15][: len(la_names)]
        la_name = random.choices(la_names, weights=la_weights)[0]
        la_code = las[la_name]

        # Select current energy rating
        if energy_ratings:
            current_rating = random.choice(
                [r for r in all_ratings if r in energy_ratings]
            )
        else:
            current_rating = random.choices(all_ratings, weights=rating_weights)[0]

        # Potential rating is same or better
        current_idx = all_ratings.index(current_rating)
        potential_idx = max(0, current_idx - random.randint(0, 2))
        potential_rating = all_ratings[potential_idx]

        # SAP scores
        current_sap = random.randint(*sap_ranges[current_rating])
        potential_sap = random.randint(*sap_ranges[potential_rating])

        # Property type
        if property_types:
            prop_type = random.choice(
                [p for p in all_property_types if p in property_types]
            )
        else:
            prop_type = random.choices(all_property_types, weights=property_weights)[0]

        # Built form (correlate with property type)
        if prop_type == "Flat":
            built_form = random.choice(
                ["Enclosed Mid-Terrace", "Enclosed End-Terrace", "Mid-Terrace"]
            )
        elif prop_type == "Bungalow":
            built_form = random.choice(["Detached", "Semi-Detached"])
        else:
            built_form = random.choices(all_built_forms, weights=built_form_weights)[0]

        # Tenure
        if tenures:
            tenure = random.choice([t for t in all_tenures if t in tenures])
        else:
            tenure = random.choices(all_tenures, weights=tenure_weights)[0]

        # Construction age band
        age_band = random.choices(all_age_bands, weights=age_band_weights)[0]

        # Main fuel
        main_fuel = random.choices(all_main_fuels, weights=fuel_weights)[0]

        # Floor area (correlate with property type)
        if prop_type == "Flat":
            floor_area = random.uniform(35, 85)
        elif prop_type == "Bungalow":
            floor_area = random.uniform(50, 120)
        elif prop_type == "Maisonette":
            floor_area = random.uniform(55, 100)
        else:  # House
            floor_area = random.uniform(60, 200)

        # CO2 emissions (correlate with SAP and floor area)
        co2_factor = (100 - current_sap) / 50  # Higher SAP = lower emissions
        co2_current = floor_area * co2_factor * random.uniform(0.03, 0.06)
        co2_potential = (
            floor_area * ((100 - potential_sap) / 50) * random.uniform(0.025, 0.045)
        )

        # Lodgement year (weighted towards recent years)
        year_weights = [0.05, 0.08, 0.10, 0.12, 0.15, 0.20, 0.30]
        lodgement_year = random.choices(range(2018, 2025), weights=year_weights)[0]

        rows.append(
            {
                "lmk_key": f"MOCK-{i:08d}",
                "la_code": la_code,
                "la_name": la_name,
                "current_energy_rating": current_rating,
                "potential_energy_rating": potential_rating,
                "current_energy_efficiency": current_sap,
                "potential_energy_efficiency": potential_sap,
                "property_type": prop_type,
                "built_form": built_form,
                "tenure": tenure,
                "construction_age_band": age_band,
                "construction_epoch": age_band_to_epoch[age_band],
                "nominal_construction_year": age_band_to_year[age_band],
                "main_fuel": main_fuel,
                "total_floor_area": round(floor_area, 1),
                "co2_emissions_current": round(co2_current, 2),
                "co2_emissions_potential": round(co2_potential, 2),
                "lodgement_year": lodgement_year,
                "mains_gas_flag": "Y" if main_fuel == "mains gas" else "N",
            }
        )

    return pl.DataFrame(rows)


def get_epc_rating_distribution() -> dict[str, list[float]]:
    """Get typical UK EPC rating distribution for reference.

    Returns:
        Dictionary with rating distribution percentages
    """
    return {
        "ratings": ["A", "B", "C", "D", "E", "F", "G"],
        "percentages": [2.0, 12.0, 35.0, 32.0, 12.0, 5.0, 2.0],
    }


@st.cache_data(ttl=3600, show_spinner="Loading EPC data...")
def _load_epc_data_cached(
    local_authorities_tuple: tuple[str, ...] | None = None,
    energy_ratings_tuple: tuple[str, ...] | None = None,
    property_types_tuple: tuple[str, ...] | None = None,
    tenures_tuple: tuple[str, ...] | None = None,
) -> pl.DataFrame:
    """Cached inner function to load EPC data from MotherDuck.

    Uses tuples instead of lists for hashability with st.cache_data.

    Args:
        local_authorities_tuple: Filter to specific LA names (as tuple)
        energy_ratings_tuple: Filter to specific energy ratings (as tuple)
        property_types_tuple: Filter to specific property types (as tuple)
        tenures_tuple: Filter to specific tenure types (as tuple)

    Returns:
        DataFrame with EPC data

    Raises:
        Exception: If database connection or query fails
    """
    from src.data.connections import get_connection

    conn = get_connection()

    # Load spatial extension (required for epc_domestic_ods_vw which uses st_astext)
    conn.execute("INSTALL spatial; LOAD spatial;")

    # Build query with filters
    # Use epc_domestic_vw which has actual SAP efficiency scores
    # Filter to WECA local authorities
    query = """
    SELECT
        LMK_KEY AS lmk_key,
        LOCAL_AUTHORITY AS la_code,
        LOCAL_AUTHORITY_LABEL AS la_name,
        CURRENT_ENERGY_RATING AS current_energy_rating,
        POTENTIAL_ENERGY_RATING AS potential_energy_rating,
        CURRENT_ENERGY_EFFICIENCY AS current_energy_efficiency,
        POTENTIAL_ENERGY_EFFICIENCY AS potential_energy_efficiency,
        PROPERTY_TYPE AS property_type,
        BUILT_FORM AS built_form,
        TENURE_CLEAN AS tenure,
        CONSTRUCTION_AGE_BAND AS construction_age_band,
        CONSTRUCTION_EPOCH AS construction_epoch,
        NOMINAL_CONSTRUCTION_YEAR AS nominal_construction_year,
        MAIN_FUEL AS main_fuel,
        TOTAL_FLOOR_AREA AS total_floor_area,
        CO2_EMISSIONS_CURRENT AS co2_emissions_current,
        CO2_EMISSIONS_POTENTIAL AS co2_emissions_potential,
        LODGEMENT_YEAR AS lodgement_year,
        MAINS_GAS_FLAG AS mains_gas_flag
    FROM mca_data.epc_domestic_vw
    WHERE LOCAL_AUTHORITY IN ('E06000022', 'E06000023', 'E06000025', 'E06000024')
    """

    params = []

    if local_authorities_tuple:
        # Convert names to codes if needed
        la_mapping = {
            "Bath and North East Somerset": "E06000022",
            "Bristol": "E06000023",
            "South Gloucestershire": "E06000025",
            "North Somerset": "E06000024",
        }
        la_codes = [la_mapping.get(la, la) for la in local_authorities_tuple]
        placeholders = ", ".join(["?" for _ in la_codes])
        query += f" AND LOCAL_AUTHORITY IN ({placeholders})"
        params.extend(la_codes)

    if energy_ratings_tuple:
        placeholders = ", ".join(["?" for _ in energy_ratings_tuple])
        query += f" AND CURRENT_ENERGY_RATING IN ({placeholders})"
        params.extend(energy_ratings_tuple)

    if property_types_tuple:
        placeholders = ", ".join(["?" for _ in property_types_tuple])
        query += f" AND PROPERTY_TYPE IN ({placeholders})"
        params.extend(property_types_tuple)

    if tenures_tuple:
        placeholders = ", ".join(["?" for _ in tenures_tuple])
        query += f" AND TENURE_CLEAN IN ({placeholders})"
        params.extend(tenures_tuple)

    df = conn.execute(query, params).pl()
    conn.close()
    return df


def load_epc_domestic_with_fallback(
    local_authorities: list[str] | None = None,
    energy_ratings: list[str] | None = None,
    property_types: list[str] | None = None,
    tenures: list[str] | None = None,
) -> tuple[pl.DataFrame, bool]:
    """Load domestic EPC data with automatic fallback to mock data.

    Args:
        local_authorities: Filter to specific LA names
        energy_ratings: Filter to specific energy ratings (A-G)
        property_types: Filter to specific property types
        tenures: Filter to specific tenure types

    Returns:
        Tuple of (DataFrame, is_mock_data_boolean)
    """
    from src.data.connections import MotherDuckConnectionError

    try:
        # Convert lists to tuples for caching (tuples are hashable)
        la_tuple = tuple(local_authorities) if local_authorities else None
        rating_tuple = tuple(energy_ratings) if energy_ratings else None
        prop_tuple = tuple(property_types) if property_types else None
        tenure_tuple = tuple(tenures) if tenures else None

        # Call cached inner function
        df = _load_epc_data_cached(
            local_authorities_tuple=la_tuple,
            energy_ratings_tuple=rating_tuple,
            property_types_tuple=prop_tuple,
            tenures_tuple=tenure_tuple,
        )
        return df, False  # Real data

    except (MotherDuckConnectionError, Exception) as e:
        # Fall back to mock data
        st.warning(
            f"""
            ### ⚠️ Using Mock EPC Data

            **Database connection failed**: {e!s}

            Showing sample WECA EPC data for development.
            The dashboard is fully functional but using mock data.

            **To use real data**: Ensure MotherDuck is available and `.env` has a
            valid `MOTHERDUCK_TOKEN`, then refresh.
            """
        )
        df = get_mock_epc_domestic_data(
            local_authorities=local_authorities,
            energy_ratings=energy_ratings,
            property_types=property_types,
            tenures=tenures,
        )
        return df, True  # Mock data
