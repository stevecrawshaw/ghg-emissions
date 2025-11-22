"""Geographic Analysis page for GHG Emissions Dashboard.

Interactive choropleth maps showing emissions patterns by geographic area.
Supports Combined Authority level visualization with boundary polygons.

Created: 2025-11-21
Updated: 2025-11-22 - Added CA choropleth map
"""

import json

import polars as pl
import streamlit as st
from streamlit_folium import st_folium

from src.components.exports import create_export_menu
from src.components.filters import (
    metric_selector,
    single_year_filter,
)
from src.data.connections import MotherDuckConnectionError, get_connection
from src.visualization.maps import create_choropleth_map

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
    Explore spatial patterns of greenhouse gas emissions across Combined Authorities
    in England. Per capita emissions provide a fairer comparison metric due to
    different population sizes and characteristics of each area.
    """
)


def load_ca_boundaries_geojson() -> tuple[dict, pl.DataFrame]:
    """Load Combined Authority boundaries as GeoJSON from MotherDuck.

    Uses DuckDB SPATIAL extension to convert geometry to GeoJSON format.

    Returns:
        Tuple of (GeoJSON dict, DataFrame with CA codes/names)
    """
    conn = get_connection()

    # Load spatial extension
    conn.execute("INSTALL spatial; LOAD spatial;")

    # Query CA boundaries with geometry as GeoJSON
    query = """
    SELECT
        CAUTH25CD as ca_code,
        CAUTH25NM as ca_name,
        LAT as lat,
        LONG as lon,
        ST_AsGeoJSON(geom) as geometry_json
    FROM ca_boundaries_bgc_tbl
    WHERE geom IS NOT NULL
    """

    df = conn.sql(query).pl()
    conn.close()

    # Build GeoJSON FeatureCollection
    features = []
    for row in df.iter_rows(named=True):
        if row["geometry_json"]:
            geometry = json.loads(row["geometry_json"])
            feature = {
                "type": "Feature",
                "properties": {
                    "ca_code": row["ca_code"],
                    "ca_name": row["ca_name"],
                },
                "geometry": geometry,
            }
            features.append(feature)

    geojson = {"type": "FeatureCollection", "features": features}

    return geojson, df.select(["ca_code", "ca_name", "lat", "lon"])


def load_ca_emissions_data(year: int) -> pl.DataFrame:
    """Load emissions data aggregated by Combined Authority.

    Args:
        year: Calendar year to load

    Returns:
        DataFrame with CA-level emissions metrics
    """
    conn = get_connection()

    # Query emissions aggregated by CA, joining via ca_la_tbl
    # Year is validated as integer from slider, safe for query
    query = f"""
    SELECT
        ca.cauthcd as ca_code,
        ca.cauthnm as ca_name,
        SUM(e.grand_total) as total_emissions,
        AVG(e.per_capita_emissions_t_co2e) as per_capita
    FROM emissions_tbl e
    INNER JOIN ca_la_tbl ca ON e.local_authority_code = ca.ladcd
    WHERE e.calendar_year = {year}
    GROUP BY ca.cauthcd, ca.cauthnm
    ORDER BY ca.cauthnm
    """  # noqa: S608

    df = conn.sql(query).pl()
    conn.close()

    return df


# Sidebar filters
st.sidebar.header("📍 Map Filters")

# Year selector
year = single_year_filter(
    min_year=2005,
    max_year=2023,
    default_year=2023,
    key="geo_year",
)

# Metric selector
metrics = {
    "per_capita": "Per Capita (t CO2e per person)",
    "total_emissions": "Total Emissions (kt CO2e)",
}

selected_metric = metric_selector(
    metrics=metrics,
    default_metric="per_capita",
    key="geo_metric",
    help_text="Per capita provides fairer comparison across areas",
)

st.sidebar.markdown("---")
st.sidebar.info(
    """
    **About this map**

    Shows per capita emissions for each
    Combined Authority in England.

    Combined Authorities with North Somerset
    included in the West of England area.
    """
)

# Load data
try:
    with st.spinner("Loading geographic boundaries..."):
        geojson_data, ca_info = load_ca_boundaries_geojson()

    with st.spinner("Loading emissions data..."):
        emissions_df = load_ca_emissions_data(year)

    if emissions_df.is_empty():
        st.warning("⚠️ No emissions data available for the selected year.")
        st.stop()

    # Merge emissions with CA info for complete dataset
    merged_df = emissions_df

    # Display header
    st.markdown("## Per-capita emissions by Combined Authority")
    st.markdown(
        f"""
        Comparison of absolute emissions by area can be challenging due to the
        different population sizes and characteristics of the areas. Per capita
        emissions can be a fairer comparison metric. The following map shows
        per capita emissions for each Combined Authority in {year} .
        """
    )

    st.markdown(
        "Combined Authorities with North Somerset included in the West of England area."
    )

    # Create choropleth map
    legend_name = metrics[selected_metric]

    # Center on England
    center = (52.5, -1.5)
    zoom = 6

    choropleth_map = create_choropleth_map(
        df=merged_df,
        geojson_data=geojson_data,
        location_col="ca_code",
        value_col=selected_metric,
        legend_name=legend_name,
        center=center,
        zoom_start=zoom,
        colorscale="sequential",
        reverse_colors=False,
    )

    # Display map
    st_folium(choropleth_map, width=900, height=600, returned_objects=[])

    st.markdown("---")

    # Summary statistics
    st.markdown("## 📊 Summary Statistics")

    col1, col2, col3, col4 = st.columns(4)

    unit = "t CO2e/person" if selected_metric == "per_capita" else "kt CO2e"

    with col1:
        avg_val = merged_df[selected_metric].mean()
        st.metric(label="Average", value=f"{avg_val:,.2f}")

    with col2:
        min_val = merged_df[selected_metric].min()
        min_ca = merged_df.filter(pl.col(selected_metric) == min_val)["ca_name"][0]
        st.metric(label="Lowest", value=f"{min_val:,.2f}", help=min_ca)

    with col3:
        max_val = merged_df[selected_metric].max()
        max_ca = merged_df.filter(pl.col(selected_metric) == max_val)["ca_name"][0]
        st.metric(label="Highest", value=f"{max_val:,.2f}", help=max_ca)

    with col4:
        # WECA value
        weca_df = merged_df.filter(pl.col("ca_name") == "West of England")
        if not weca_df.is_empty():
            weca_val = weca_df[selected_metric][0]
            st.metric(label="West of England", value=f"{weca_val:,.2f}")
        else:
            st.metric(label="West of England", value="N/A")

    st.markdown("---")

    # Data table
    st.markdown("## 📋 Full Rankings")

    # Sort by selected metric (ascending for per capita - lower is better)
    display_df = merged_df.sort(selected_metric, descending=False)

    # Add rank column
    display_df = display_df.with_row_index("Rank")
    display_df = display_df.with_columns((pl.col("Rank") + 1).alias("Rank"))

    # Format for display
    display_df = display_df.select(
        [
            pl.col("Rank"),
            pl.col("ca_name").alias("Combined Authority"),
            pl.col("total_emissions").round(1).alias("Total (kt CO2e)"),
            pl.col("per_capita").round(2).alias("Per Capita (t CO2e)"),
        ]
    )

    st.dataframe(
        display_df.to_pandas(),
        hide_index=True,
        use_container_width=True,
    )

    # Highlight WECA position
    weca_row = display_df.filter(pl.col("Combined Authority") == "West of England")
    if not weca_row.is_empty():
        rank = weca_row["Rank"][0]
        total = display_df.height
        st.info(
            f"📍 **West of England** ranks **{rank}** of {total} Combined Authorities"
        )

    st.markdown("---")

    # Export options
    st.markdown("## 📥 Export Data")

    create_export_menu(
        df=display_df,
        base_filename=f"ca_emissions_{year}",
        key_prefix="geo_export",
        show_heading=False,
    )

except MotherDuckConnectionError:
    st.error(
        "❌ **Database Connection Error**\n\n"
        "Unable to connect to MotherDuck. Please check your connection and try again."
    )
    st.stop()
except Exception as e:
    st.error(f"❌ **Error Loading Data**: {e}")
    st.info("If this persists, check that the SPATIAL extension is available.")
    st.stop()
