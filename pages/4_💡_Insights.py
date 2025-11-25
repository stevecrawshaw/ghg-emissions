"""Insights & Comparisons Dashboard Page.

Interactive comparison of WECA emissions against other Combined Authorities,
regional benchmarks, and national averages.

Features:
- WECA vs other Combined Authorities ranking
- Time series comparison with England average
- Per capita and total emissions benchmarks
- Rank position indicators
- Data export functionality
"""

import polars as pl
import streamlit as st
from dotenv import load_dotenv

from src.components.exports import create_data_summary_card, create_export_menu
from src.components.filters import (
    metric_selector,
    single_year_filter,
)
from src.utils.config import apply_home_page_label
from src.visualization.charts import (
    create_bar_comparison,
    create_time_series,
)
from src.visualization.themes import (
    CLARET,
    WARM_GREY,
    WEST_GREEN,
    register_weca_template,
)

# Load environment variables
load_dotenv()

# Register WECA template
register_weca_template()

# Page configuration
st.set_page_config(
    page_title="Insights & Comparisons | WECA Dashboard",
    page_icon="💡",
    layout="wide",
)

# Apply Home label to sidebar
apply_home_page_label()

# Page header
st.title("💡 Insights & Comparisons")
st.markdown(
    """
    Compare West of England Combined Authority (WECA) emissions performance
    against other Combined Authorities in England. See how WECA ranks on
    total emissions, per capita emissions, and emissions trends over time.
    """
)


# =============================================================================
# Mock Data Generators for CA Comparison
# =============================================================================


def get_mock_ca_comparison_data(
    min_year: int = 2005, max_year: int = 2023
) -> pl.DataFrame:
    """Generate mock Combined Authority emissions comparison data.

    Args:
        min_year: Start year for data generation
        max_year: End year for data generation

    Returns:
        DataFrame with CA-level emissions for comparison
    """
    import random

    random.seed(42)

    # UK Combined Authorities with approximate emissions (kt CO2e)
    # Based on typical 2022 data patterns
    cas = {
        "West of England": {
            "total_2023": 4200,
            "population": 960000,
            "area_km2": 953,
        },
        "Greater Manchester": {
            "total_2023": 12500,
            "population": 2850000,
            "area_km2": 1276,
        },
        "West Midlands": {
            "total_2023": 11800,
            "population": 2920000,
            "area_km2": 902,
        },
        "Liverpool City Region": {
            "total_2023": 6800,
            "population": 1550000,
            "area_km2": 725,
        },
        "South Yorkshire": {
            "total_2023": 5900,
            "population": 1410000,
            "area_km2": 1552,
        },
        "West Yorkshire": {
            "total_2023": 9200,
            "population": 2350000,
            "area_km2": 1772,
        },
        "Tees Valley": {
            "total_2023": 4800,
            "population": 680000,
            "area_km2": 800,
        },
        "North East": {
            "total_2023": 5200,
            "population": 1150000,
            "area_km2": 2080,
        },
        "Cambridgeshire & Peterborough": {
            "total_2023": 4500,
            "population": 860000,
            "area_km2": 3389,
        },
        "East Midlands": {
            "total_2023": 8500,
            "population": 2200000,
            "area_km2": 2900,
        },
    }

    # Generate time series data (2014-2023)
    rows = []
    years = range(min_year, max_year + 1)

    for ca_name, ca_data in cas.items():
        for year in years:
            # Simulate declining emissions over time (2-4% per year)
            # max_year is base year, earlier years had higher emissions
            year_factor = 1.0 + (0.03 * (max_year - year))
            # Add some realistic variation (not cryptographic)
            variation = random.uniform(0.97, 1.03)  # noqa: S311
            total = ca_data["total_2023"] * year_factor * variation

            # Per capita (tonnes per person)
            per_capita = (total * 1000) / ca_data["population"]

            # Per km2 (tonnes per km2)
            per_km2 = (total * 1000) / ca_data["area_km2"]

            rows.append(
                {
                    "ca_name": ca_name,
                    "calendar_year": year,
                    "total_emissions": round(total, 1),
                    "per_capita": round(per_capita, 2),
                    "per_km2": round(per_km2, 1),
                    "population": ca_data["population"],
                    "area_km2": ca_data["area_km2"],
                }
            )

    return pl.DataFrame(rows)


def get_mock_england_average(
    min_year: int = 2005, max_year: int = 2023
) -> pl.DataFrame:
    """Generate mock England average emissions data.

    Args:
        min_year: Start year for data generation
        max_year: End year for data generation

    Returns:
        DataFrame with England-level emissions averages
    """
    import random

    random.seed(42)

    # England total emissions approximately 320,000 kt CO2e in 2023
    # Population ~56.5 million
    england_2023_total = 320000
    england_population = 56500000
    england_area = 130279  # km2

    rows = []
    for year in range(min_year, max_year + 1):
        # 2023 is base year, earlier years had higher emissions (~2.8% decline per year)
        year_factor = 1.0 + (0.028 * (max_year - year))
        variation = random.uniform(0.98, 1.02)  # noqa: S311
        total = england_2023_total * year_factor * variation

        per_capita = (total * 1000) / england_population
        per_km2 = (total * 1000) / england_area

        rows.append(
            {
                "region": "England",
                "calendar_year": year,
                "total_emissions": round(total, 1),
                "per_capita": round(per_capita, 2),
                "per_km2": round(per_km2, 1),
            }
        )

    return pl.DataFrame(rows)


def load_ca_comparison_with_fallback() -> tuple[pl.DataFrame, bool]:
    """Load CA comparison data with automatic fallback to mock data.

    Returns:
        Tuple of (DataFrame, is_mock_data_boolean)
    """
    from src.data.connections import MotherDuckConnectionError

    try:
        from src.data.connections import get_connection

        conn = get_connection()

        # Query emissions_tbl aggregated by CA using ca_la_tbl lookup
        # This gets all UK CAs for comparison
        query = """
        WITH ca_emissions AS (
            SELECT
                COALESCE(ca.cauthnm, 'Other') as ca_name,
                e.calendar_year,
                SUM(e.grand_total) as total_emissions,
                SUM(e.per_capita_emissions_t_co2e *
                    CASE WHEN e.grand_total > 0 THEN 1 ELSE 0 END) /
                    NULLIF(COUNT(DISTINCT e.local_authority_code), 0) as per_capita
            FROM emissions_tbl e
            LEFT JOIN ca_la_tbl ca ON e.local_authority_code = ca.ladcd
            WHERE ca.cauthnm IS NOT NULL
            GROUP BY ca.cauthnm, e.calendar_year
        )
        SELECT *
        FROM ca_emissions
        ORDER BY calendar_year DESC, ca_name
        """

        df = conn.sql(query).pl()
        conn.close()

        # Check if we got meaningful data
        if df.is_empty() or df.height < 10:
            # Fall back to mock data if query returns insufficient results
            return get_mock_ca_comparison_data(), True

        return df, False

    except (MotherDuckConnectionError, Exception) as e:
        st.warning(
            f"""
            ### ⚠️ Using Mock Comparison Data

            **Database connection failed**: {e!s}

            Showing sample Combined Authority comparison data for development.
            The dashboard is fully functional but using mock data.
            """
        )
        return get_mock_ca_comparison_data(), True


def load_england_average_with_fallback(
    min_year: int = 2005, max_year: int = 2023
) -> tuple[pl.DataFrame, bool]:
    """Load England average data with automatic fallback.

    Args:
        min_year: Minimum year for data
        max_year: Maximum year for data

    Returns:
        Tuple of (DataFrame, is_mock_data_boolean)
    """
    from src.data.connections import MotherDuckConnectionError

    try:
        from src.data.connections import get_connection

        conn = get_connection()

        # Query England total from emissions_tbl
        query = """
        SELECT
            'England' as region,
            calendar_year,
            SUM(grand_total) as total_emissions,
            AVG(per_capita_emissions_t_co2e) as per_capita
        FROM emissions_tbl
        WHERE region_country = 'England'
        GROUP BY calendar_year
        ORDER BY calendar_year
        """

        df = conn.sql(query).pl()
        conn.close()

        if df.is_empty():
            return get_mock_england_average(min_year, max_year), True

        return df, False

    except (MotherDuckConnectionError, Exception):
        return get_mock_england_average(min_year, max_year), True


# =============================================================================
# Load Data First (to get year range)
# =============================================================================

# Load CA comparison data
ca_df, is_ca_mock = load_ca_comparison_with_fallback()

# Get year range from loaded data
data_min_year = int(ca_df["calendar_year"].min())
data_max_year = int(ca_df["calendar_year"].max())

# Load England average with matching year range
england_df, is_england_mock = load_england_average_with_fallback(
    min_year=data_min_year, max_year=data_max_year
)

# =============================================================================
# Sidebar Filters
# =============================================================================

st.sidebar.header("🔍 Filters")

# Year selector with dynamic range from data
selected_year = single_year_filter(
    min_year=data_min_year,
    max_year=data_max_year,
    default_year=data_max_year,
    key="insights_year",
    help_text="Select year for comparison snapshot",
)

# Metric selector
metrics = {
    "total_emissions": "Total Emissions (kt CO2e)",
    "per_capita": "Per Capita (t CO2e per person)",
}

selected_metric = metric_selector(
    metrics=metrics,
    default_metric="per_capita",
    key="insights_metric",
    help_text="Choose the comparison metric",
)

st.sidebar.markdown("---")
st.sidebar.info(
    """
    **About this page**

    Compares WECA emissions against other
    Combined Authorities in England.

    Per capita emissions provide the fairest
    comparison across different-sized areas.
    """
)

# Check data availability
if ca_df.is_empty():
    st.error("No comparison data available. Please check database connection.")
    st.stop()

# =============================================================================
# Key Metrics
# =============================================================================

st.markdown("## 📊 WECA Performance Overview")

# Filter to selected year
year_df = ca_df.filter(pl.col("calendar_year") == selected_year)

# Get WECA data
weca_row = year_df.filter(pl.col("ca_name") == "West of England")
if weca_row.is_empty():
    st.warning("WECA data not found for selected year.")
    weca_value = 0.0
    weca_rank = "N/A"
    total_cas = 0
else:
    weca_value = weca_row[selected_metric][0]

    # Calculate rank (lower is better for emissions)
    ranked_df = year_df.sort(selected_metric, descending=False).with_row_index("rank")
    weca_rank_row = ranked_df.filter(pl.col("ca_name") == "West of England")
    weca_rank = int(weca_rank_row["rank"][0]) + 1 if not weca_rank_row.is_empty() else 0
    total_cas = year_df.height

# England average for selected year
england_year = england_df.filter(pl.col("calendar_year") == selected_year)
england_avg = (
    england_year[selected_metric][0] if not england_year.is_empty() else weca_value
)

# Calculate % difference from England average
if england_avg > 0:
    pct_diff_england = ((weca_value - england_avg) / england_avg) * 100
else:
    pct_diff_england = 0

# Get previous year data for trend
prev_year_df = ca_df.filter(
    (pl.col("calendar_year") == selected_year - 1)
    & (pl.col("ca_name") == "West of England")
)
if not prev_year_df.is_empty():
    prev_value = prev_year_df[selected_metric][0]
    yoy_change = ((weca_value - prev_value) / prev_value) * 100 if prev_value > 0 else 0
else:
    yoy_change = 0

# Display metrics
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        label=f"WECA {metrics[selected_metric].split('(')[0].strip()}",
        value=f"{weca_value:,.1f}",
        help=f"WECA {selected_metric} for {selected_year}",
    )

with col2:
    st.metric(
        label="Rank Among CAs",
        value=f"{weca_rank} of {total_cas}",
        help="Lower emissions = better rank",
    )

with col3:
    st.metric(
        label="vs England Average",
        value=f"{pct_diff_england:+.1f}%",
        delta=f"{pct_diff_england:+.1f}%",
        delta_color="inverse",  # Below average (negative) is good
        help="Negative = below (better than) England average",
    )

with col4:
    st.metric(
        label="Year-on-Year Change",
        value=f"{yoy_change:+.1f}%",
        delta=f"{yoy_change:+.1f}%",
        delta_color="inverse",  # Decreasing emissions is good
        help=f"Change from {selected_year - 1} to {selected_year}",
    )

st.markdown("---")

# =============================================================================
# CA Comparison Chart
# =============================================================================

st.markdown("## 🏛️ Combined Authority Comparison")

# Sort by selected metric
sorted_df = year_df.sort(selected_metric, descending=True)

# Add highlighting column for WECA
sorted_df = sorted_df.with_columns(
    pl.when(pl.col("ca_name") == "West of England")
    .then(pl.lit(WEST_GREEN))
    .otherwise(pl.lit(WARM_GREY))
    .alias("bar_color")
)

# Create comparison bar chart
fig_comparison = create_bar_comparison(
    sorted_df,
    x="ca_name",
    y=selected_metric,
    title=f"Combined Authority {metrics[selected_metric]} ({selected_year})",
    x_label="Combined Authority",
    y_label=metrics[selected_metric],
    orientation="v",
    template="weca",
    color=None,  # We'll customize colors below
)

# Customize bar colors to highlight WECA
colors = [
    WEST_GREEN if ca == "West of England" else WARM_GREY
    for ca in sorted_df["ca_name"].to_list()
]
fig_comparison.update_traces(marker_color=colors)

# Add England average line (only for per capita - total emissions not comparable)
if not england_year.is_empty() and selected_metric == "per_capita":
    fig_comparison.add_hline(
        y=england_avg,
        line_dash="dash",
        line_color=CLARET,
        annotation_text=f"England Avg: {england_avg:.1f}",
        annotation_position="top right",
    )

st.plotly_chart(fig_comparison, use_container_width=True)

st.markdown("---")

# =============================================================================
# Time Series Comparison
# =============================================================================

st.markdown("## 📈 Emissions Trend Over Time")

col1, col2 = st.columns(2)

with col1:
    # WECA time series (only include England for per capita - totals not comparable)
    weca_ts = ca_df.filter(pl.col("ca_name") == "West of England").select(
        [
            pl.col("calendar_year"),
            pl.col(selected_metric),
            pl.lit("West of England").alias("region"),
        ]
    )

    if selected_metric == "per_capita":
        # England comparison only meaningful for per capita
        england_ts = england_df.select(
            [
                pl.col("calendar_year"),
                pl.col(selected_metric),
                pl.lit("England Average").alias("region"),
            ]
        )
        comparison_ts = pl.concat([weca_ts, england_ts]).sort(
            ["region", "calendar_year"]
        )
        title = f"WECA vs England Average - {metrics[selected_metric]}"
    else:
        # For total emissions, just show WECA trend
        comparison_ts = weca_ts.sort("calendar_year")
        title = f"WECA Emissions Trend - {metrics[selected_metric]}"

    fig_trend = create_time_series(
        comparison_ts,
        x="calendar_year",
        y=selected_metric,
        color="region" if selected_metric == "per_capita" else None,
        title=title,
        x_label="Year",
        y_label=metrics[selected_metric],
        markers=True,
        template="weca",
    )

    st.plotly_chart(fig_trend, use_container_width=True)

with col2:
    # Top 5 CAs time series for context
    # Get top 5 by most recent year emissions
    latest_year = ca_df["calendar_year"].max()
    top_cas = (
        ca_df.filter(pl.col("calendar_year") == latest_year)
        .sort(selected_metric, descending=True)
        .head(5)["ca_name"]
        .to_list()
    )

    # Always include WECA
    if "West of England" not in top_cas:
        top_cas = ["West of England"] + top_cas[:4]

    top_ca_ts = ca_df.filter(pl.col("ca_name").is_in(top_cas)).sort(
        ["ca_name", "calendar_year"]
    )

    fig_top_cas = create_time_series(
        top_ca_ts,
        x="calendar_year",
        y=selected_metric,
        color="ca_name",
        title=f"Top Combined Authorities - {metrics[selected_metric]}",
        x_label="Year",
        y_label=metrics[selected_metric],
        markers=True,
        template="weca",
    )

    st.plotly_chart(fig_top_cas, use_container_width=True)

st.markdown("---")

# =============================================================================
# Rankings Table
# =============================================================================

st.markdown("## 🏆 Full Rankings")

# Create rankings table
rankings_df = year_df.sort(selected_metric, descending=False).with_row_index("Rank")
rankings_df = rankings_df.with_columns((pl.col("Rank") + 1).alias("Rank"))

# Select and rename columns for display
display_df = rankings_df.select(
    [
        pl.col("Rank"),
        pl.col("ca_name").alias("Combined Authority"),
        pl.col("total_emissions").alias("Total (kt CO2e)"),
        pl.col("per_capita").alias("Per Capita (t CO2e)"),
    ]
)

# Highlight WECA row
st.dataframe(
    display_df.to_pandas(),
    hide_index=True,
    use_container_width=True,
    column_config={
        "Rank": st.column_config.NumberColumn(format="%d"),
        "Total (kt CO2e)": st.column_config.NumberColumn(format="%.1f"),
        "Per Capita (t CO2e)": st.column_config.NumberColumn(format="%.2f"),
    },
)

# Show WECA position highlight
weca_display = display_df.filter(pl.col("Combined Authority") == "West of England")
if not weca_display.is_empty():
    rank = weca_display["Rank"][0]
    if rank <= 3:
        st.success(f"🏆 WECA ranks **{rank}** out of {total_cas} Combined Authorities!")
    elif rank <= total_cas // 2:
        st.info(
            f"📊 WECA ranks **{rank}** out of {total_cas} - "
            f"in the top half of Combined Authorities"
        )
    else:
        st.warning(
            f"📊 WECA ranks **{rank}** out of {total_cas} - "
            f"room for improvement compared to peers"
        )

st.markdown("---")

# =============================================================================
# Data Summary & Export
# =============================================================================

st.markdown("## 📋 Data Summary")

with st.expander("View Dataset Details", expanded=False):
    create_data_summary_card(ca_df, title="CA Comparison Data Summary")

st.markdown("## 📥 Export Data")

create_export_menu(
    year_df,
    base_filename=f"weca_ca_comparison_{selected_year}",
    formats=["csv", "parquet", "json", "excel"],
    key_prefix="insights_export",
    show_heading=False,
)

# Footer note about data
st.markdown("---")
st.caption(
    """
    **Data Notes:**
    - Combined Authority emissions are aggregated from constituent Local Authorities
    - Per capita emissions provide the most equitable comparison across areas
    - Rankings are based on the selected metric (lower emissions = better rank)
    - England average includes all local authorities, not just those in CAs
    """
)
