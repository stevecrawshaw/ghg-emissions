"""Geographic Analysis page for GHG Emissions Dashboard.

Interactive choropleth maps showing emissions patterns by geographic area.
Supports multiple geographic levels (LA, LSOA) and metrics.

Created: 2025-11-21
"""

import polars as pl
import streamlit as st
from streamlit_folium import st_folium

from src.components.exports import create_export_menu
from src.components.filters import (
    metric_selector,
    sector_filter,
    single_year_filter,
)
from src.data.connections import MotherDuckConnectionError
from src.data.loaders import load_emissions_data, load_local_authorities
from src.visualization.maps import create_bubble_map

# Page configuration
st.set_page_config(
    page_title="Geographic Analysis - GHG Emissions",
    page_icon="🗺️",
    layout="wide",
)

# Title and description
st.title("🗺️ Geographic Analysis")
st.markdown(
    """
    Explore spatial patterns of greenhouse gas emissions across the West of England
    Combined Authority and North Somerset. Interactive maps reveal geographic
    variations and hotspots.
    """
)

# Sidebar filters
st.sidebar.header("📍 Map Filters")

# Geographic level selector
geo_level = st.sidebar.selectbox(
    "Geographic Level",
    options=["Local Authority"],
    help="Select the geographic granularity for analysis. LSOA and MSOA coming soon.",
)

# Year selector
year = single_year_filter(
    min_year=2019,
    max_year=2023,
    default_year=2023,
    key="geo_year",
)

# Sector filter - all available sectors
sectors = [
    "Transport",
    "Domestic",
    "Industry",
    "Commercial",
    "Public Sector",
    "Agriculture",
    "LULUCF",
]

selected_sectors = sector_filter(
    sectors=sectors,
    default_selection=sectors,
    allow_all=True,
    key="geo_sectors",
    help_text="Select emission sectors to include in analysis",
)

# Metric selector
metrics = {
    "total_emissions": "Total Emissions (kt CO2e)",
    "per_capita": "Per Capita Emissions (t CO2e/person)",
    "per_km2": "Emissions Density (t CO2e/km²)",
}

selected_metric = metric_selector(
    metrics=metrics,
    default_metric="total_emissions",
    key="geo_metric",
)

st.sidebar.markdown("---")

# Load data
try:
    # Load local authorities
    las_df = load_local_authorities()

    # Get WECA + North Somerset LA codes
    weca_ns_names = [
        "Bristol, City of",
        "Bath and North East Somerset",
        "South Gloucestershire",
        "North Somerset",
    ]

    # Filter to WECA + NS and get codes
    weca_ns_df = las_df.filter(pl.col("ladnm").is_in(weca_ns_names))
    weca_ns_codes = weca_ns_df["ladcd"].to_list()

    # Load emissions data for selected year
    df = load_emissions_data(
        start_year=year,
        end_year=year,
        local_authorities=weca_ns_codes,
        sectors=selected_sectors if selected_sectors else None,
    )

    if df.is_empty():
        st.warning("⚠️ No data available for the selected filters.")
        st.stop()

    # Rename columns to match expected names
    df = df.rename({
        "local_authority_code": "la_code",
        "local_authority": "la_name",
    })

    # Aggregate by LA using group_by
    agg_df = (
        df.group_by(["la_code", "la_name"])
        .agg([
            pl.col("territorial_emissions_kt_co2e").sum().alias("total_emissions"),
            pl.col("mid_year_population_thousands").first(),
            pl.col("area_km2").first(),
        ])
    )

    # Calculate per capita and per km2 metrics
    agg_df = agg_df.with_columns([
        (
            pl.col("total_emissions") * 1000
            / (pl.col("mid_year_population_thousands") * 1000)
        ).alias("per_capita"),
        (
            pl.col("total_emissions") * 1000
            / pl.col("area_km2")
        ).alias("per_km2"),
    ])

    # Display summary statistics
    st.markdown("## 📊 Geographic Summary")

    col1, col2, col3, col4 = st.columns(4)

    # Unit for display
    unit = "kt" if selected_metric == "total_emissions" else "t"

    with col1:
        total = agg_df[selected_metric].sum()
        st.metric(
            label="Total",
            value=f"{total:,.1f} {unit}",
        )

    with col2:
        avg = agg_df[selected_metric].mean()
        st.metric(
            label="Average",
            value=f"{avg:,.1f} {unit}",
        )

    with col3:
        max_val = agg_df[selected_metric].max()
        max_la = agg_df.filter(pl.col(selected_metric) == max_val)["la_name"][0]
        st.metric(
            label="Highest",
            value=f"{max_la}",
            delta=f"{max_val:,.1f} {unit}",
        )

    with col4:
        min_val = agg_df[selected_metric].min()
        min_la = agg_df.filter(pl.col(selected_metric) == min_val)["la_name"][0]
        st.metric(
            label="Lowest",
            value=f"{min_la}",
            delta=f"{min_val:,.1f} {unit}",
            delta_color="inverse",
        )

    st.markdown("---")

    # Create map
    st.markdown("## 🗺️ Interactive Map")

    st.info(
        "💡 **Note**: Choropleth maps with LA boundaries require GeoJSON data. "
        "Currently showing bubble map with LA locations. Full choropleth maps with "
        "boundary shading will be added once GeoJSON data is prepared."
    )

    # For now, create a bubble map showing LA locations
    # We need lat/lon for each LA - this would come from LA centroids
    # Placeholder: WECA region center coordinates
    la_coords = {
        "Bristol, City of": (51.4545, -2.5879),
        "Bath and North East Somerset": (51.3811, -2.3590),
        "South Gloucestershire": (51.5374, -2.4736),
        "North Somerset": (51.3873, -2.7770),
    }

    # Add coordinates to dataframe
    agg_df = agg_df.with_columns([
        pl.col("la_name").map_elements(
            lambda x: la_coords.get(x, (51.4545, -2.5879))[0],
            return_dtype=pl.Float64,
        ).alias("lat"),
        pl.col("la_name").map_elements(
            lambda x: la_coords.get(x, (51.4545, -2.5879))[1],
            return_dtype=pl.Float64,
        ).alias("lon"),
    ])

    # Create bubble map
    m = create_bubble_map(
        df=agg_df,
        lat_col="lat",
        lon_col="lon",
        size_col=selected_metric,
        name_col="la_name",
        value_col=selected_metric,
        center=(51.4545, -2.5879),
        zoom_start=10,
        max_radius=50,
    )

    # Display map (use returned_objects=[] to prevent flashing from interactions)
    st_folium(m, width=700, height=600, returned_objects=[])

    st.markdown("---")

    # Data table
    st.markdown("## 📋 Detailed Data")

    # Prepare display dataframe
    display_df = agg_df.select([
        pl.col("la_name").alias("Local Authority"),
        pl.col("total_emissions").alias("Total Emissions (kt CO2e)"),
        pl.col("per_capita").alias("Per Capita (t CO2e/person)"),
        pl.col("per_km2").alias("Emissions Density (t CO2e/km²)"),
    ])

    # Sort by selected metric
    sort_col_map = {
        "total_emissions": "Total Emissions (kt CO2e)",
        "per_capita": "Per Capita (t CO2e/person)",
        "per_km2": "Emissions Density (t CO2e/km²)",
    }
    display_df = display_df.sort(sort_col_map[selected_metric], descending=True)

    st.dataframe(
        display_df,
        width="stretch",
        hide_index=True,
    )

    # Export options
    st.markdown("---")
    st.markdown("### 💾 Export Data")

    create_export_menu(
        df=display_df,
        base_filename=f"geographic_emissions_{year}",
        key_prefix="geo_export",
    )

except MotherDuckConnectionError:
    st.error(
        "❌ **Database Connection Error**\n\n"
        "Unable to connect to MotherDuck. Please check your connection and try again."
    )
    st.stop()
except Exception as e:
    st.error(f"❌ **Error Loading Data**: {e}")
    st.stop()
