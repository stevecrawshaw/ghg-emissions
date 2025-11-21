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

    # Default sectors
    all_sectors = [
        "Industry",
        "Commercial",
        "Public Sector",
        "Domestic",
        "Transport",
        "Agriculture",
        "LULUCF",
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
        },
        "Bristol": {
            "Industry": 580,
            "Commercial": 650,
            "Public Sector": 180,
            "Domestic": 890,
            "Transport": 920,
            "Agriculture": 10,
            "LULUCF": -35,
        },
        "South Gloucestershire": {
            "Industry": 420,
            "Commercial": 290,
            "Public Sector": 95,
            "Domestic": 580,
            "Transport": 680,
            "Agriculture": 45,
            "LULUCF": -25,
        },
        "North Somerset": {
            "Industry": 210,
            "Commercial": 180,
            "Public Sector": 65,
            "Domestic": 450,
            "Transport": 520,
            "Agriculture": 55,
            "LULUCF": -20,
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
