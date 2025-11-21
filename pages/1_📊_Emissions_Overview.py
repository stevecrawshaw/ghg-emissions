"""Emissions Overview Dashboard Page.

Interactive visualization of greenhouse gas emissions for WECA local authorities
and North Somerset (candidate authority) across multiple sectors and time periods.

Features:
- Time series analysis of emissions trends
- Sector breakdown with stacked area charts
- Local authority comparisons
- Per capita and per km² metrics
- Data export functionality
"""

import polars as pl
import streamlit as st
from dotenv import load_dotenv

from src.components.exports import create_data_summary_card, create_export_menu
from src.components.filters import (
    la_selector,
    metric_selector,
    sector_filter,
    year_range_filter,
)
from src.data.mock_data import (
    load_emissions_data_with_fallback,
    load_local_authorities_with_fallback,
)
from src.data.transforms import aggregate_time_series
from src.visualization.charts import (
    create_bar_comparison,
    create_stacked_area,
    create_time_series,
)
from src.visualization.themes import register_weca_template

# Load environment variables
load_dotenv()

# Register WECA template
register_weca_template()

# Page configuration
st.set_page_config(
    page_title="Emissions Overview | WECA Dashboard",
    page_icon="📊",
    layout="wide",
)

# Page header
st.title("📊 Emissions Overview")
st.markdown(
    """
    Analyze greenhouse gas emissions trends across the West of England Combined
    Authority (Bath and North East Somerset, Bristol, South Gloucestershire) and
    North Somerset (candidate authority). Filter by time period, local authority,
    and sector to explore the data.
    """
)

# Sidebar filters
st.sidebar.header("🔍 Filters")

# Load available local authorities (with automatic fallback to mock data)
las_df, is_mock = load_local_authorities_with_fallback()
available_las = las_df["la_name"].to_list()

# Debug: Show available LA names (remove this after verification)
if not is_mock:
    first_five = ", ".join(sorted(available_las)[:5])
    st.sidebar.info(f"📋 Available LAs ({len(available_las)}): {first_five}...")

# Year range filter
start_year, end_year = year_range_filter(
    min_year=2014,
    max_year=2023,
    default_range=(2019, 2023),
    key="year_range_overview",
    help_text="Select the time period for emissions analysis",
)

# Local authority selector
# Use flexible defaults: WECA + North Somerset (candidate authority)
default_las = []
for name in [
    "Bristol, City of",
    "Bristol",
    "Bath and North East Somerset",
    "South Gloucestershire",
    "North Somerset",
]:
    if name in available_las:
        default_las.append(name)

# If no matches found, use first 4 available (to match WECA + North Somerset)
if not default_las:
    default_las = available_las[: min(4, len(available_las))]

selected_las = la_selector(
    local_authorities=available_las,
    default_selection=default_las,
    allow_multiple=True,
    key="la_selector_overview",
    help_text="Select one or more local authorities to analyze",
)

# Available sectors (from CLAUDE.md schema)
sectors = [
    "Industry",
    "Commercial",
    "Public Sector",
    "Domestic",
    "Transport",
    "Agriculture",
    "LULUCF",
]

# Sector filter
selected_sectors = sector_filter(
    sectors=sectors,
    default_selection=sectors,
    allow_all=True,
    key="sector_filter_overview",
    help_text="Select emission sectors to include in analysis",
)

# Metric selector
metrics = {
    "total_emissions": "Total Emissions (kt CO2e)",
    "per_capita": "Per Capita (t CO2e per person)",
    "per_km2": "Emissions Density (t CO2e per km²)",
}

selected_metric = metric_selector(
    metrics=metrics,
    default_metric="total_emissions",
    key="metric_selector_overview",
    help_text="Choose the emission metric to visualize",
)

st.sidebar.markdown("---")

# Load emissions data (with automatic fallback to mock data)
with st.spinner("Loading emissions data..."):
    df, is_mock = load_emissions_data_with_fallback(
        start_year=start_year,
        end_year=end_year,
        local_authorities=selected_las,
        sectors=selected_sectors,
    )

    # Check if data is empty
    if df.is_empty():
        st.warning(
            "No data available for the selected filters. "
            "Please try different filter combinations."
        )
        st.stop()

    # Data summary card
    with st.expander("📋 Dataset Summary", expanded=False):
        create_data_summary_card(df, title="Emissions Data Summary")

    # Main visualizations
    st.markdown("## 📈 Emissions Trends")

    # Time series by local authority
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Time Series by Local Authority")

        # Aggregate by year and LA
        ts_df = aggregate_time_series(
            df,
            group_cols=["calendar_year", "la_name"],
            value_col=selected_metric,
            year_col="calendar_year",
            agg_functions=["sum"],
        )

        # Create time series chart
        fig_ts = create_time_series(
            ts_df,
            x="calendar_year",
            y=f"{selected_metric}_sum",
            color="la_name",
            title=f"Emissions Over Time - {metrics[selected_metric]}",
            x_title="Year",
            y_title=metrics[selected_metric],
            markers=True,
            template="weca",
        )

        st.plotly_chart(fig_ts, width="stretch")

    with col2:
        st.markdown("### Sector Breakdown Over Time")

        # Aggregate by year and sector
        sector_df = aggregate_time_series(
            df,
            group_cols=["calendar_year", "sector"],
            value_col=selected_metric,
            year_col="calendar_year",
            agg_functions=["sum"],
        )

        # Create stacked area chart
        fig_stacked = create_stacked_area(
            sector_df,
            x="calendar_year",
            y=f"{selected_metric}_sum",
            group="sector",
            title=f"Emissions by Sector - {metrics[selected_metric]}",
            x_title="Year",
            y_title=metrics[selected_metric],
            template="weca",
        )

        st.plotly_chart(fig_stacked, width="stretch")

    st.markdown("---")

    # Local authority comparison
    st.markdown("## 🏛️ Local Authority Comparison")

    # Filter for most recent year
    latest_year = df["calendar_year"].max()
    latest_df = df.filter(pl.col("calendar_year") == latest_year)

    # Aggregate by LA
    la_comparison = aggregate_time_series(
        latest_df,
        group_cols=["la_name"],
        value_col=selected_metric,
        year_col="calendar_year",
        agg_functions=["sum"],
    )

    # Sort by value
    la_comparison = la_comparison.sort(f"{selected_metric}_sum", descending=True)

    # Create bar chart
    fig_bar = create_bar_comparison(
        la_comparison,
        x="la_name",
        y=f"{selected_metric}_sum",
        title=f"Emissions Comparison ({latest_year}) - {metrics[selected_metric]}",
        x_title="Local Authority",
        y_title=metrics[selected_metric],
        orientation="v",
        template="weca",
    )

    st.plotly_chart(fig_bar, width="stretch")

    st.markdown("---")

    # Key insights
    st.markdown("## 💡 Key Insights")

    col1, col2, col3 = st.columns(3)

    # Calculate insights
    total_emissions = df[selected_metric].sum()
    avg_annual = total_emissions / ((end_year - start_year + 1) * len(selected_las))

    # Get trend (compare first and last year)
    first_year_total = df.filter(pl.col("calendar_year") == start_year)[
        selected_metric
    ].sum()
    last_year_total = df.filter(pl.col("calendar_year") == end_year)[
        selected_metric
    ].sum()

    if first_year_total > 0:
        pct_change = ((last_year_total - first_year_total) / first_year_total) * 100
    else:
        pct_change = 0

    with col1:
        st.metric(
            label=f"Total {metrics[selected_metric]}",
            value=f"{total_emissions:,.0f}",
            delta=None,
        )

    with col2:
        st.metric(
            label=f"Average Annual ({start_year}-{end_year})",
            value=f"{avg_annual:,.1f}",
            delta=None,
        )

    with col3:
        st.metric(
            label=f"Change ({start_year} to {end_year})",
            value=f"{pct_change:+.1f}%",
            delta=f"{pct_change:+.1f}%",
            delta_color="inverse",  # Decreasing is good for emissions
        )

    st.markdown("---")

    # Data export
    st.markdown("## 📥 Export Data")

    create_export_menu(
        df,
        base_filename=f"weca_emissions_{start_year}_{end_year}",
        formats=["csv", "parquet", "json", "excel"],
        key_prefix="emissions_export",
    )
