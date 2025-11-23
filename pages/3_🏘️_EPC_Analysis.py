"""EPC Analysis Dashboard Page.

Interactive visualization of Energy Performance Certificate (EPC) data for
domestic properties in the WECA region and North Somerset.

Features:
- Energy rating distribution analysis
- Property type breakdown
- Tenure and construction age patterns
- CO2 emissions analysis
- Improvement potential assessment
- Data export functionality
"""

import plotly.express as px
import polars as pl
import streamlit as st
from dotenv import load_dotenv

from src.components.exports import create_data_summary_card, create_export_menu
from src.components.filters import la_selector
from src.data.mock_data import (
    load_epc_domestic_with_fallback,
    load_local_authorities_with_fallback,
)
from src.visualization.charts import (
    create_bar_comparison,
    create_donut_chart,
    create_grouped_bar,
    create_heatmap,
)
from src.visualization.themes import register_weca_template

# Load environment variables
load_dotenv()

# Register WECA template
register_weca_template()

# Page configuration
st.set_page_config(
    page_title="EPC Analysis | WECA Dashboard",
    page_icon="🏘️",
    layout="wide",
)

# Page header
st.title("🏘️ EPC Analysis - Domestic Properties")
st.markdown(
    """
    Analyze Energy Performance Certificate (EPC) data for domestic properties
    across the West of England Combined Authority (Bath and North East Somerset,
    Bristol, South Gloucestershire) and North Somerset. Explore energy ratings,
    property characteristics, and improvement potential.
    """
)

# Sidebar filters
st.sidebar.header("🔍 Filters")

# Load available local authorities
las_df, is_mock = load_local_authorities_with_fallback()
available_las = las_df["la_name"].to_list()

# Local authority selector
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

if not default_las:
    default_las = available_las[: min(4, len(available_las))]

selected_las = la_selector(
    local_authorities=available_las,
    default_selection=default_las,
    allow_multiple=True,
    key="la_selector_epc",
    help_text="Select one or more local authorities to analyze",
)

# Energy rating filter
st.sidebar.markdown("### Energy Ratings")
all_ratings = ["A", "B", "C", "D", "E", "F", "G"]
selected_ratings = st.sidebar.multiselect(
    "Filter by current rating",
    options=all_ratings,
    default=all_ratings,
    key="rating_filter_epc",
    help="Select energy ratings to include (A=best, G=worst)",
)

# Property type filter
st.sidebar.markdown("### Property Type")
all_property_types = ["House", "Flat", "Bungalow", "Maisonette", "Park home"]
selected_property_types = st.sidebar.multiselect(
    "Filter by property type",
    options=all_property_types,
    default=all_property_types,
    key="property_type_filter_epc",
)

# Tenure filter
st.sidebar.markdown("### Tenure")
all_tenures = ["Owner occupied", "Private rented", "Social rented"]
selected_tenures = st.sidebar.multiselect(
    "Filter by tenure",
    options=all_tenures,
    default=all_tenures,
    key="tenure_filter_epc",
)

st.sidebar.markdown("---")

# Load EPC data
with st.spinner("Loading EPC data..."):
    df, is_mock = load_epc_domestic_with_fallback(
        local_authorities=selected_las if selected_las else None,
        energy_ratings=selected_ratings if selected_ratings else None,
        property_types=selected_property_types if selected_property_types else None,
        tenures=selected_tenures if selected_tenures else None,
    )

    # Check if data is empty
    if df.is_empty():
        st.warning(
            "No EPC data available for the selected filters. "
            "Please try different filter combinations."
        )
        st.stop()

    # Data summary card
    with st.expander("📋 Dataset Summary", expanded=False):
        create_data_summary_card(df, title="EPC Data Summary")

    # Key metrics
    st.markdown("## 📊 Key Metrics")

    col1, col2, col3, col4 = st.columns(4)

    total_properties = len(df)
    avg_sap = df["current_energy_efficiency"].mean()
    avg_co2 = df["co2_emissions_current"].mean()

    # Calculate % rated C or above (good ratings)
    good_ratings = df.filter(pl.col("current_energy_rating").is_in(["A", "B", "C"]))
    pct_good = (
        (len(good_ratings) / total_properties * 100) if total_properties > 0 else 0
    )

    with col1:
        st.metric(
            label="Total Properties",
            value=f"{total_properties:,}",
        )

    with col2:
        st.metric(
            label="Average SAP Score",
            value=f"{avg_sap:.1f}" if avg_sap else "N/A",
            help="SAP score 1-100, higher is better",
        )

    with col3:
        st.metric(
            label="Avg CO2 (t/year)",
            value=f"{avg_co2:.1f}" if avg_co2 else "N/A",
            help="Average CO2 emissions per property",
        )

    with col4:
        st.metric(
            label="Rated C or Above",
            value=f"{pct_good:.1f}%",
            help="Percentage of properties with EPC rating A, B, or C",
        )

    st.markdown("---")

    # Main visualizations
    st.markdown("## 📈 Energy Rating Distribution")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Current Energy Ratings")

        # Aggregate by rating
        rating_counts = (
            df.group_by("current_energy_rating")
            .agg(pl.len().alias("count"))
            .sort("current_energy_rating")
        )

        # Ensure all ratings are present
        all_rating_df = pl.DataFrame({"current_energy_rating": all_ratings})
        rating_counts = all_rating_df.join(
            rating_counts, on="current_energy_rating", how="left"
        ).with_columns(pl.col("count").fill_null(0))

        fig_ratings = create_bar_comparison(
            rating_counts,
            x="current_energy_rating",
            y="count",
            title="Properties by Current Energy Rating",
            x_label="Energy Rating",
            y_label="Number of Properties",
            orientation="v",
            template="weca",
        )

        st.plotly_chart(fig_ratings, width="stretch")

    with col2:
        st.markdown("### Rating Distribution by LA")

        # Aggregate by LA and rating
        la_rating_counts = (
            df.group_by(["la_name", "current_energy_rating"])
            .agg(pl.len().alias("count"))
            .sort(["la_name", "current_energy_rating"])
        )

        if not la_rating_counts.is_empty():
            fig_la_ratings = create_grouped_bar(
                la_rating_counts,
                x="current_energy_rating",
                y="count",
                group="la_name",
                title="Energy Ratings by Local Authority",
                x_label="Energy Rating",
                y_label="Number of Properties",
                template="weca",
            )

            st.plotly_chart(fig_la_ratings, width="stretch")

    st.markdown("---")

    # Property characteristics
    st.markdown("## 🏠 Property Characteristics")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Property Type Distribution")

        property_counts = (
            df.group_by("property_type")
            .agg(pl.len().alias("count"))
            .sort("count", descending=True)
        )

        fig_property = create_donut_chart(
            property_counts,
            values="count",
            names="property_type",
            title="Properties by Type",
        )

        st.plotly_chart(fig_property, width="stretch")

    with col2:
        st.markdown("### Tenure Distribution")

        tenure_counts = (
            df.group_by("tenure")
            .agg(pl.len().alias("count"))
            .sort("count", descending=True)
        )

        fig_tenure = create_donut_chart(
            tenure_counts,
            values="count",
            names="tenure",
            title="Properties by Tenure",
        )

        st.plotly_chart(fig_tenure, width="stretch")

    st.markdown("---")

    # Construction age and energy rating relationship
    st.markdown("## 🏗️ Construction Age Analysis")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Properties by Construction Period")

        # Use construction_epoch (cleaned/categorized) with nominal year for sorting
        # Aggregate only by epoch to avoid subdivisions in bar chart
        # Fill null years with 1850 to ensure "Before 1900" sorts first
        age_counts = (
            df.group_by("construction_epoch")
            .agg(
                pl.len().alias("count"),
                pl.col("nominal_construction_year").first().alias("sort_year"),
            )
            .with_columns(pl.col("sort_year").fill_null(1850))
            .sort("sort_year")
            .drop("sort_year")
        )

        fig_age = create_bar_comparison(
            age_counts,
            x="construction_epoch",
            y="count",
            title="Properties by Construction Period",
            x_label="Construction Period",
            y_label="Number of Properties",
            orientation="v",
            template="weca",
        )

        # Rotate x-axis labels
        fig_age.update_layout(xaxis_tickangle=-45)

        st.plotly_chart(fig_age, width="stretch")

    with col2:
        st.markdown("### Energy Rating by Construction Period")

        # Create heatmap of rating vs construction epoch (use long format data)
        # Aggregate by epoch and rating, use a representative year for sorting
        # Fill null years with 1850 to ensure "Before 1900" sorts first
        age_rating = (
            df.group_by(["construction_epoch", "current_energy_rating"])
            .agg(
                pl.len().alias("count"),
                pl.col("nominal_construction_year").first().alias("sort_year"),
            )
            .with_columns(pl.col("sort_year").fill_null(1850))
            .sort(["sort_year", "current_energy_rating"])
        )

        if not age_rating.is_empty():
            # Pivot for heatmap - keep sort_year for ordering y-axis
            rating_order = ["A", "B", "C", "D", "E", "F", "G"]
            epoch_order = (
                age_rating.select(["construction_epoch", "sort_year"])
                .unique()
                .sort("sort_year")["construction_epoch"]
                .to_list()
            )

            pivot_df = age_rating.pivot(
                values="count", index="construction_epoch", on="current_energy_rating"
            ).to_pandas()

            # Reorder rows and columns
            pivot_df = pivot_df.set_index("construction_epoch")
            pivot_df = pivot_df.reindex(index=epoch_order)
            rating_cols = [c for c in rating_order if c in pivot_df.columns]
            pivot_df = pivot_df[rating_cols].fillna(0)

            fig_heatmap = px.imshow(
                pivot_df,
                labels={
                    "x": "Energy Rating",
                    "y": "Construction Period",
                    "color": "Count",
                },
                aspect="auto",
                color_continuous_scale="RdYlGn_r",
            )
            fig_heatmap.update_layout(
                title="Energy Rating Distribution by Construction Period",
                height=400,
            )

            st.plotly_chart(fig_heatmap, width="stretch")

    st.markdown("---")

    # Fuel type analysis
    st.markdown("## ⚡ Heating Fuel Analysis")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Main Heating Fuel")

        # Get fuel counts and limit to top 5 + Other
        fuel_counts = (
            df.filter(pl.col("main_fuel").is_not_null())
            .group_by("main_fuel")
            .agg(pl.len().alias("count"))
            .sort("count", descending=True)
        )

        # Combine anything after top 5 into "Other"
        if len(fuel_counts) > 5:
            top_5 = fuel_counts.head(5)
            other_count = fuel_counts.slice(5)["count"].sum()
            # Cast to UInt32 to match the schema from pl.len()
            other_row = pl.DataFrame(
                {"main_fuel": ["Other"], "count": [other_count]}
            ).cast({"count": pl.UInt32})
            fuel_counts = pl.concat([top_5, other_row])

        fig_fuel = create_bar_comparison(
            fuel_counts,
            x="main_fuel",
            y="count",
            title="Properties by Main Heating Fuel",
            x_label="Fuel Type",
            y_label="Number of Properties",
            orientation="v",
            template="weca",
        )

        st.plotly_chart(fig_fuel, width="stretch")

    with col2:
        st.markdown("### Mains Gas Connection")

        gas_counts = df.group_by("mains_gas_flag").agg(pl.len().alias("count"))

        # Map Y/N to readable labels
        gas_counts = gas_counts.with_columns(
            pl.when(pl.col("mains_gas_flag") == "Y")
            .then(pl.lit("Connected"))
            .otherwise(pl.lit("Not Connected"))
            .alias("gas_status")
        )

        fig_gas = create_donut_chart(
            gas_counts,
            values="count",
            names="gas_status",
            title="Mains Gas Connection",
        )

        st.plotly_chart(fig_gas, width="stretch")

    st.markdown("---")

    # Improvement potential
    st.markdown("## 🎯 Improvement Potential")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Current vs Potential Rating")

        # Calculate improvement potential (use long format data)
        improvement = (
            df.group_by(["current_energy_rating", "potential_energy_rating"])
            .agg(pl.len().alias("count"))
            .sort(["current_energy_rating", "potential_energy_rating"])
        )

        if not improvement.is_empty():
            fig_improvement = create_heatmap(
                improvement,
                x="potential_energy_rating",
                y="current_energy_rating",
                z="count",
                title="Current Rating (rows) vs Potential Rating (columns)",
                x_label="Potential Rating",
                y_label="Current Rating",
            )

            st.plotly_chart(fig_improvement, width="stretch")

    with col2:
        st.markdown("### CO2 Savings Potential")

        # Check if CO2 columns exist and have data
        has_co2_data = (
            "co2_emissions_current" in df.columns
            and "co2_emissions_potential" in df.columns
        )

        if has_co2_data:
            # Filter out nulls and ensure current > potential for savings
            co2_df = df.filter(
                pl.col("co2_emissions_current").is_not_null()
                & pl.col("co2_emissions_potential").is_not_null()
                & (pl.col("co2_emissions_current") > 0)
                & (pl.col("co2_emissions_potential") >= 0)
            )

            if not co2_df.is_empty() and "current_energy_rating" in co2_df.columns:
                # Calculate CO2 savings and aggregate by rating
                co2_savings = (
                    co2_df.with_columns(
                        (
                            pl.col("co2_emissions_current")
                            - pl.col("co2_emissions_potential")
                        ).alias("co2_savings")
                    )
                    .filter(pl.col("current_energy_rating").is_not_null())
                    .group_by("current_energy_rating")
                    .agg(
                        pl.mean("co2_savings").alias("avg_savings"),
                        pl.sum("co2_savings").alias("total_savings"),
                        pl.len().alias("property_count"),
                    )
                    .filter(pl.col("property_count") > 0)
                    .sort("current_energy_rating")
                )

                # Show chart if we have data after aggregation
                if not co2_savings.is_empty() and len(co2_savings) > 0:
                    fig_savings = create_bar_comparison(
                        co2_savings,
                        x="current_energy_rating",
                        y="avg_savings",
                        title="Average CO2 Savings Potential by Current Rating",
                        x_label="Current Energy Rating",
                        y_label="Avg CO2 Savings (t/year)",
                        orientation="v",
                        template="weca",
                    )

                    st.plotly_chart(fig_savings, width="stretch")
                else:
                    st.info(
                        "Insufficient CO2 savings data. This may occur when current "
                        "and potential emissions are equal or data is incomplete."
                    )
            else:
                st.info("No CO2 emissions data available for the selected filters.")
        else:
            st.info("CO2 emissions data not available in this dataset.")

    st.markdown("---")

    # Key insights
    st.markdown("## 💡 Key Insights")

    # Calculate CO2 insights (handle missing columns)
    if has_co2_data:
        co2_valid = df.filter(
            pl.col("co2_emissions_current").is_not_null()
            & pl.col("co2_emissions_potential").is_not_null()
        )
        total_co2_current = co2_valid["co2_emissions_current"].sum()
        total_co2_potential = co2_valid["co2_emissions_potential"].sum()
        total_savings = (
            total_co2_current - total_co2_potential if total_co2_current else 0
        )
        pct_savings = (
            (total_savings / total_co2_current * 100) if total_co2_current else 0
        )
    else:
        total_savings = 0
        pct_savings = 0

    # Properties with poor ratings (E, F, G)
    poor_ratings = df.filter(pl.col("current_energy_rating").is_in(["E", "F", "G"]))
    pct_poor = (
        (len(poor_ratings) / total_properties * 100) if total_properties > 0 else 0
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        if has_co2_data and total_savings > 0:
            st.metric(
                label="Total CO2 Savings Potential",
                value=f"{total_savings:,.1f} t/year",
                delta=f"-{pct_savings:.1f}% potential reduction",
                delta_color="normal",
            )
        else:
            st.metric(
                label="Total CO2 Savings Potential",
                value="N/A",
                help="CO2 data not available for this selection",
            )

    with col2:
        st.metric(
            label="Properties Rated E, F, or G",
            value=f"{len(poor_ratings):,}",
            delta=f"{pct_poor:.1f}% of total",
            delta_color="inverse",
            help="Properties requiring significant improvement",
        )

    with col3:
        # Most common property type
        most_common_type = (
            df.group_by("property_type")
            .agg(pl.len().alias("count"))
            .sort("count", descending=True)
            .head(1)
        )
        if not most_common_type.is_empty():
            common_type = most_common_type["property_type"][0]
            common_count = most_common_type["count"][0]
            pct_common = common_count / total_properties * 100

            st.metric(
                label="Most Common Property Type",
                value=common_type,
                delta=f"{pct_common:.1f}% of properties",
            )

    st.markdown("---")

    # Data export
    st.markdown("## 📥 Export Data")

    create_export_menu(
        df,
        base_filename="weca_epc_domestic",
        formats=["csv", "parquet", "json", "excel"],
        key_prefix="epc_export",
        show_heading=False,
    )
