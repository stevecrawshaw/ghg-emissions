"""Plotly chart creation functions with WECA branding.

This module provides functions for creating interactive Plotly charts
with consistent WECA visual identity and theming.

Chart Types:
- Time series line charts
- Stacked area charts for sector breakdowns
- Bar charts for geographic comparisons
- Heatmaps for patterns
- Scatter plots for correlations

All charts use WECA template by default and accept Polars DataFrames.

Example:
    >>> from src.visualization.charts import create_time_series
    >>> import polars as pl
    >>>
    >>> df = pl.DataFrame(
    ...     {
    ...         "year": [2019, 2020, 2021, 2022, 2023],
    ...         "emissions": [1000, 950, 900, 850, 800],
    ...     }
    ... )
    >>> fig = create_time_series(df, x="year", y="emissions", title="Emissions Trend")
    >>> fig.show()
"""

from typing import Any

import plotly.express as px
import plotly.graph_objects as go
import polars as pl

from src.visualization.themes import get_categorical_colors, get_plotly_template


class ChartError(Exception):
    """Exception raised for chart creation errors.

    Attributes:
        message: Explanation of the error
        chart_type: Type of chart that failed
    """

    def __init__(self, message: str, chart_type: str | None = None) -> None:
        """Initialize ChartError.

        Args:
            message: Explanation of the error
            chart_type: Type of chart that failed (optional)
        """
        self.message = message
        self.chart_type = chart_type
        super().__init__(self.message)


def _format_column_label(column_name: str) -> str:
    """Convert a column name to a nicely formatted label.

    Args:
        column_name: Raw column name (e.g., 'la_name', 'total_emissions_sum')

    Returns:
        Formatted label (e.g., 'Local Authority', 'Total Emissions')
    """
    # Common replacements for WECA emissions data
    label_map = {
        "la_name": "Local Authority",
        "local_authority": "Local Authority",
        "ca_name": "Combined Authority",
        "calendar_year": "Year",
        "total_emissions": "Total Emissions (kt CO2e)",
        "total_emissions_sum": "Total Emissions (kt CO2e)",
        "per_capita": "Per Capita (t CO2e)",
        "per_capita_sum": "Per Capita (t CO2e)",
        "per_km2": "Per km² (t CO2e)",
        "per_km2_sum": "Per km² (t CO2e)",
        "sector": "Sector",
        "current_energy_rating": "Energy Rating",
        "property_type": "Property Type",
        "main_fuel": "Main Fuel",
        "count": "Count",
        "avg_savings": "Avg CO2 Savings (t/year)",
    }

    if column_name in label_map:
        return label_map[column_name]

    # Default: replace underscores with spaces and title case
    return column_name.replace("_", " ").title()


def create_time_series(
    df: pl.DataFrame,
    x: str,
    y: str | list[str],
    title: str | None = None,
    x_label: str | None = None,
    y_label: str | None = None,
    color: str | None = None,
    markers: bool = True,
    height: int = 500,
    template: dict[str, Any] | None = None,
) -> go.Figure:
    """Create an interactive time series line chart.

    Creates a line chart with optional markers, multiple lines (if y is a list),
    and color grouping. Uses WECA template by default.

    Args:
        df: DataFrame with time series data
        x: Column name for x-axis (typically year or date)
        y: Column name(s) for y-axis values. Can be single column or list
            for multiple lines
        title: Chart title (optional)
        x_label: X-axis label (optional, defaults to column name)
        y_label: Y-axis label (optional, defaults to column name)
        color: Column name for color grouping (e.g., sector, geography)
        markers: Show markers on line (default: True)
        height: Chart height in pixels (default: 500)
        template: Custom Plotly template (default: WECA template)

    Returns:
        Plotly Figure object

    Raises:
        ChartError: If required columns are missing or data is invalid

    Example:
        >>> # Single line
        >>> fig = create_time_series(
        ...     df, x="year", y="emissions", title="Total Emissions"
        ... )
        >>>
        >>> # Multiple lines by sector
        >>> fig = create_time_series(
        ...     df, x="year", y="emissions", color="sector", title="Emissions by Sector"
        ... )
    """
    if template is None:
        template = get_plotly_template()

    # Validate columns
    if x not in df.columns:
        msg = f"Column '{x}' not found in DataFrame"
        raise ChartError(msg, chart_type="time_series")

    y_cols = [y] if isinstance(y, str) else y
    missing_cols = [col for col in y_cols if col not in df.columns]
    if missing_cols:
        msg = f"Columns not found in DataFrame: {missing_cols}"
        raise ChartError(msg, chart_type="time_series")

    if color and color not in df.columns:
        msg = f"Color column '{color}' not found in DataFrame"
        raise ChartError(msg, chart_type="time_series")

    # Create figure - Plotly 6.0+ natively supports Polars DataFrames
    if len(y_cols) == 1 and color:
        # Single y column with color grouping
        fig = px.line(
            df,
            x=x,
            y=y_cols[0],
            color=color,
            markers=markers,
            template=template,
        )
    elif len(y_cols) == 1:
        # Single line, no grouping
        fig = px.line(
            df,
            x=x,
            y=y_cols[0],
            markers=markers,
            template=template,
        )
    else:
        # Multiple y columns - melt DataFrame first
        df_melted = df.select([x] + y_cols).unpivot(
            index=x,
            on=y_cols,
            variable_name="series",
            value_name="value",
        )
        fig = px.line(
            df_melted,
            x=x,
            y="value",
            color="series",
            markers=markers,
            template=template,
        )
        y_label = y_label or "Value"

    # Update layout
    fig.update_layout(
        title=title,
        xaxis_title=x_label or _format_column_label(x),
        yaxis_title=y_label
        or _format_column_label(y if isinstance(y, str) else "Value"),
        height=height,
        hovermode="x unified",
    )

    # Make lines thicker and format hover values
    y_col = y if isinstance(y, str) else y_cols[0]
    x_formatted = _format_column_label(x)
    y_formatted = y_label or _format_column_label(y_col)

    # Update traces with formatted hover template
    for trace in fig.data:
        trace.update(
            line={"width": 3},
            hovertemplate=(
                f"<b>{x_formatted}</b>: %{{x}}<br>"
                f"<b>{y_formatted}</b>: %{{y:.1f}}<br>"
                "<extra>%{fullData.name}</extra>"
            ),
        )

    return fig


def create_stacked_area(
    df: pl.DataFrame,
    x: str,
    y: str,
    group: str,
    title: str | None = None,
    x_label: str | None = None,
    y_label: str | None = None,
    height: int = 500,
    template: dict[str, Any] | None = None,
) -> go.Figure:
    """Create a stacked area chart for showing composition over time.

    Useful for showing sector breakdowns or geographic contributions
    to total emissions.

    Args:
        df: DataFrame with data
        x: Column name for x-axis (typically year or date)
        y: Column name for y-axis values
        group: Column name for stacking groups (e.g., sector)
        title: Chart title (optional)
        x_label: X-axis label (optional)
        y_label: Y-axis label (optional)
        height: Chart height in pixels (default: 500)
        template: Custom Plotly template (default: WECA template)

    Returns:
        Plotly Figure object

    Raises:
        ChartError: If required columns are missing

    Example:
        >>> fig = create_stacked_area(
        ...     df,
        ...     x="year",
        ...     y="emissions",
        ...     group="sector",
        ...     title="Emissions by Sector Over Time",
        ... )
    """
    if template is None:
        template = get_plotly_template()

    # Validate columns
    required_cols = [x, y, group]
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        msg = f"Columns not found in DataFrame: {missing_cols}"
        raise ChartError(msg, chart_type="stacked_area")

    # Create figure - Plotly 6.0+ natively supports Polars DataFrames
    fig = px.area(
        df,
        x=x,
        y=y,
        color=group,
        template=template,
    )

    # Format labels
    x_formatted = x_label or _format_column_label(x)
    y_formatted = y_label or _format_column_label(y)
    group_formatted = _format_column_label(group)

    # Update layout
    fig.update_layout(
        title=title,
        xaxis_title=x_formatted,
        yaxis_title=y_formatted,
        height=height,
        hovermode="x unified",
    )

    # Update traces with formatted hover template
    for trace in fig.data:
        trace.update(
            hovertemplate=(
                f"<b>{x_formatted}</b>: %{{x}}<br>"
                f"<b>{y_formatted}</b>: %{{y:.1f}}<br>"
                f"<b>{group_formatted}</b>: %{{fullData.name}}<extra></extra>"
            ),
        )

    # Update traces for better stacking
    fig.update_traces(
        mode="lines",
        line={"width": 0.5},
        stackgroup="one",
    )

    return fig


def create_bar_comparison(
    df: pl.DataFrame,
    x: str,
    y: str,
    title: str | None = None,
    x_label: str | None = None,
    y_label: str | None = None,
    color: str | None = None,
    orientation: str = "v",
    height: int = 500,
    sort_by: str | None = None,
    ascending: bool = False,
    template: dict[str, Any] | None = None,
) -> go.Figure:
    """Create a bar chart for comparing values across categories.

    Useful for comparing emissions across local authorities or sectors.

    Args:
        df: DataFrame with data
        x: Column name for x-axis (categorical)
        y: Column name for y-axis (values)
        title: Chart title (optional)
        x_label: X-axis label (optional)
        y_label: Y-axis label (optional)
        color: Column name for color grouping (optional)
        orientation: Bar orientation - "v" (vertical) or "h" (horizontal)
        height: Chart height in pixels (default: 500)
        sort_by: Column to sort by (optional, typically x or y)
        ascending: Sort order (default: False for descending)
        template: Custom Plotly template (default: WECA template)

    Returns:
        Plotly Figure object

    Raises:
        ChartError: If required columns are missing or orientation invalid

    Example:
        >>> # Compare local authorities
        >>> fig = create_bar_comparison(
        ...     df,
        ...     x="local_authority",
        ...     y="emissions",
        ...     title="Emissions by Local Authority",
        ...     sort_by="emissions",
        ... )
        >>>
        >>> # Horizontal bars for long labels
        >>> fig = create_bar_comparison(
        ...     df, x="local_authority", y="emissions", orientation="h"
        ... )
    """
    if template is None:
        template = get_plotly_template()

    # Validate orientation
    if orientation not in ["v", "h"]:
        msg = f"Invalid orientation '{orientation}'. Must be 'v' or 'h'"
        raise ChartError(msg, chart_type="bar_comparison")

    # Validate columns
    required_cols = [x, y]
    if color:
        required_cols.append(color)
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        msg = f"Columns not found in DataFrame: {missing_cols}"
        raise ChartError(msg, chart_type="bar_comparison")

    # Sort if requested
    if sort_by:
        if sort_by not in df.columns:
            msg = f"Sort column '{sort_by}' not found in DataFrame"
            raise ChartError(msg, chart_type="bar_comparison")
        df = df.sort(sort_by, descending=not ascending)

    # Create figure - Plotly 6.0+ natively supports Polars DataFrames
    fig = px.bar(
        df,
        x=x if orientation == "v" else y,
        y=y if orientation == "v" else x,
        color=color,
        orientation=orientation,
        template=template,
    )

    # Format labels
    x_formatted = x_label or _format_column_label(x)
    y_formatted = y_label or _format_column_label(y)

    # Update layout
    fig.update_layout(
        title=title,
        xaxis_title=x_formatted if orientation == "v" else y_formatted,
        yaxis_title=y_formatted if orientation == "v" else x_formatted,
        height=height,
    )

    # Update traces with formatted hover template
    if orientation == "v":
        hover = (
            f"<b>{x_formatted}</b>: %{{x}}<br>"
            f"<b>{y_formatted}</b>: %{{y:.1f}}<extra></extra>"
        )
    else:
        hover = (
            f"<b>{x_formatted}</b>: %{{y}}<br>"
            f"<b>{y_formatted}</b>: %{{x:.1f}}<extra></extra>"
        )
    fig.update_traces(hovertemplate=hover)

    return fig


def create_heatmap(
    df: pl.DataFrame,
    x: str,
    y: str,
    z: str,
    title: str | None = None,
    x_label: str | None = None,
    y_label: str | None = None,
    colorscale: str = "RdYlGn_r",
    height: int = 600,
    template: dict[str, Any] | None = None,
) -> go.Figure:
    """Create a heatmap for showing patterns across two dimensions.

    Useful for showing emissions by geography and time, or correlations
    between variables.

    Args:
        df: DataFrame with data
        x: Column name for x-axis
        y: Column name for y-axis
        z: Column name for cell values (color intensity)
        title: Chart title (optional)
        x_label: X-axis label (optional)
        y_label: Y-axis label (optional)
        colorscale: Plotly colorscale name (default: "RdYlGn_r" - red
            to green reversed)
        height: Chart height in pixels (default: 600)
        template: Custom Plotly template (default: WECA template)

    Returns:
        Plotly Figure object

    Raises:
        ChartError: If required columns are missing

    Example:
        >>> # Emissions by LA and year
        >>> fig = create_heatmap(
        ...     df,
        ...     x="calendar_year",
        ...     y="local_authority",
        ...     z="emissions",
        ...     title="Emissions Patterns",
        ... )
    """
    if template is None:
        template = get_plotly_template()

    # Validate columns
    required_cols = [x, y, z]
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        msg = f"Columns not found in DataFrame: {missing_cols}"
        raise ChartError(msg, chart_type="heatmap")

    # Pivot data for heatmap
    pivot_df = df.pivot(values=z, index=y, columns=x)

    # Extract data directly from Polars without pandas conversion
    # Get y labels (the index column values)
    y_labels = pivot_df[y].to_list()
    # Get x labels (all columns except the index)
    x_labels = [c for c in pivot_df.columns if c != y]
    # Get values as numpy array (excluding the index column)
    values = pivot_df.select(pl.exclude(y)).to_numpy()

    # Create figure using imshow with numpy array
    fig = px.imshow(
        values,
        x=x_labels,
        y=y_labels,
        labels={"x": x_label or x, "y": y_label or y, "color": z},
        aspect="auto",
        color_continuous_scale=colorscale,
    )

    # Update layout - exclude title from template to avoid conflict
    layout_kwargs = {k: v for k, v in template["layout"].items() if k != "title"}
    fig.update_layout(
        title=title,
        height=height,
        **layout_kwargs,
    )

    # Update hover template
    fig.update_traces(
        hovertemplate=f"{x_label or x}: %{{x}}<br>"
        f"{y_label or y}: %{{y}}<br>"
        f"{z}: %{{z:.2f}}<extra></extra>"
    )

    return fig


def create_scatter(
    df: pl.DataFrame,
    x: str,
    y: str,
    title: str | None = None,
    x_label: str | None = None,
    y_label: str | None = None,
    color: str | None = None,
    size: str | None = None,
    hover_data: list[str] | None = None,
    trendline: bool = False,
    height: int = 500,
    template: dict[str, Any] | None = None,
) -> go.Figure:
    """Create a scatter plot for showing correlations and distributions.

    Useful for exploring relationships between variables (e.g., emissions
    vs population, emissions vs deprivation).

    Args:
        df: DataFrame with data
        x: Column name for x-axis
        y: Column name for y-axis
        title: Chart title (optional)
        x_label: X-axis label (optional)
        y_label: Y-axis label (optional)
        color: Column name for color grouping (optional)
        size: Column name for marker size (optional)
        hover_data: Additional columns to show on hover (optional)
        trendline: Add OLS trendline (default: False)
        height: Chart height in pixels (default: 500)
        template: Custom Plotly template (default: WECA template)

    Returns:
        Plotly Figure object

    Raises:
        ChartError: If required columns are missing

    Example:
        >>> # Emissions vs population
        >>> fig = create_scatter(
        ...     df,
        ...     x="population",
        ...     y="emissions",
        ...     color="local_authority",
        ...     size="area_km2",
        ...     trendline=True,
        ...     title="Emissions vs Population",
        ... )
    """
    if template is None:
        template = get_plotly_template()

    # Validate columns
    required_cols = [x, y]
    if color:
        required_cols.append(color)
    if size:
        required_cols.append(size)
    if hover_data:
        required_cols.extend(hover_data)

    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        msg = f"Columns not found in DataFrame: {missing_cols}"
        raise ChartError(msg, chart_type="scatter")

    # Create figure - Plotly 6.0+ natively supports Polars DataFrames
    fig = px.scatter(
        df,
        x=x,
        y=y,
        color=color,
        size=size,
        hover_data=hover_data,
        trendline="ols" if trendline else None,
        template=template,
    )

    # Update layout
    fig.update_layout(
        title=title,
        xaxis_title=x_label or x,
        yaxis_title=y_label or y,
        height=height,
    )

    # Make markers slightly larger
    fig.update_traces(marker={"size": 10, "opacity": 0.7, "line": {"width": 0.5}})

    return fig


def create_grouped_bar(
    df: pl.DataFrame,
    x: str,
    y: str,
    group: str,
    title: str | None = None,
    x_label: str | None = None,
    y_label: str | None = None,
    orientation: str = "v",
    height: int = 500,
    barmode: str = "group",
    template: dict[str, Any] | None = None,
) -> go.Figure:
    """Create a grouped or stacked bar chart for multi-category comparisons.

    Useful for comparing values across multiple dimensions (e.g., emissions
    by sector across different local authorities).

    Args:
        df: DataFrame with data
        x: Column name for x-axis (categorical)
        y: Column name for y-axis (values)
        group: Column name for grouping/stacking bars
        title: Chart title (optional)
        x_label: X-axis label (optional)
        y_label: Y-axis label (optional)
        orientation: Bar orientation - "v" (vertical) or "h" (horizontal)
        height: Chart height in pixels (default: 500)
        barmode: Bar mode - "group" (side-by-side) or "stack" (stacked)
        template: Custom Plotly template (default: WECA template)

    Returns:
        Plotly Figure object

    Raises:
        ChartError: If required columns are missing or parameters invalid

    Example:
        >>> # Compare sectors across LAs
        >>> fig = create_grouped_bar(
        ...     df,
        ...     x="local_authority",
        ...     y="emissions",
        ...     group="sector",
        ...     title="Emissions by LA and Sector",
        ... )
        >>>
        >>> # Stacked bars
        >>> fig = create_grouped_bar(
        ...     df, x="local_authority", y="emissions", group="sector", barmode="stack"
        ... )
    """
    if template is None:
        template = get_plotly_template()

    # Validate parameters
    if orientation not in ["v", "h"]:
        msg = f"Invalid orientation '{orientation}'. Must be 'v' or 'h'"
        raise ChartError(msg, chart_type="grouped_bar")

    if barmode not in ["group", "stack"]:
        msg = f"Invalid barmode '{barmode}'. Must be 'group' or 'stack'"
        raise ChartError(msg, chart_type="grouped_bar")

    # Validate columns
    required_cols = [x, y, group]
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        msg = f"Columns not found in DataFrame: {missing_cols}"
        raise ChartError(msg, chart_type="grouped_bar")

    # Create figure - Plotly 6.0+ natively supports Polars DataFrames
    fig = px.bar(
        df,
        x=x if orientation == "v" else y,
        y=y if orientation == "v" else x,
        color=group,
        orientation=orientation,
        barmode=barmode,
        template=template,
    )

    # Update layout
    fig.update_layout(
        title=title,
        xaxis_title=x_label or (x if orientation == "v" else y),
        yaxis_title=y_label or (y if orientation == "v" else x),
        height=height,
    )

    return fig


def add_reference_line(
    fig: go.Figure,
    y: float | None = None,
    x: float | None = None,
    label: str | None = None,
    color: str = "#CE132D",
    dash: str = "dash",
) -> go.Figure:
    """Add a horizontal or vertical reference line to a chart.

    Useful for showing targets, baselines, or thresholds (e.g., net zero
    target line, baseline year).

    Args:
        fig: Plotly Figure to add line to
        y: Y-value for horizontal line (mutually exclusive with x)
        x: X-value for vertical line (mutually exclusive with y)
        label: Label for the line (optional)
        color: Line color (default: WECA Claret for warnings/targets)
        dash: Line style - "solid", "dash", "dot", "dashdot" (default: "dash")

    Returns:
        Updated Plotly Figure

    Raises:
        ChartError: If neither or both x and y are provided

    Example:
        >>> fig = create_time_series(df, x="year", y="emissions")
        >>> fig = add_reference_line(fig, y=0, label="Net Zero Target", color="#1D4F2B")
    """
    if (y is None and x is None) or (y is not None and x is not None):
        msg = "Must provide exactly one of y (horizontal) or x (vertical)"
        raise ChartError(msg, chart_type="reference_line")

    if y is not None:
        # Horizontal line
        fig.add_hline(
            y=y,
            line_dash=dash,
            line_color=color,
            annotation_text=label,
            annotation_position="right",
        )
    else:
        # Vertical line
        fig.add_vline(
            x=x,
            line_dash=dash,
            line_color=color,
            annotation_text=label,
            annotation_position="top",
        )

    return fig


def create_donut_chart(
    df: pl.DataFrame,
    values: str,
    names: str,
    title: str | None = None,
    height: int = 500,
    hole_size: float = 0.4,
    template: dict[str, Any] | None = None,
) -> go.Figure:
    """Create a donut chart for showing proportions.

    Useful for showing sector breakdowns or property type distributions.

    Args:
        df: DataFrame with data
        values: Column name for slice values
        names: Column name for slice labels
        title: Chart title (optional)
        height: Chart height in pixels (default: 500)
        hole_size: Size of center hole (0-1, default: 0.4)
        template: Custom Plotly template (default: WECA template)

    Returns:
        Plotly Figure object

    Raises:
        ChartError: If required columns are missing

    Example:
        >>> fig = create_donut_chart(
        ...     df,
        ...     values="emissions",
        ...     names="sector",
        ...     title="Emissions by Sector (2023)",
        ... )
    """
    if template is None:
        template = get_plotly_template()

    # Validate columns
    required_cols = [values, names]
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        msg = f"Columns not found in DataFrame: {missing_cols}"
        raise ChartError(msg, chart_type="donut_chart")

    # Get categorical colors
    n_slices = len(df)
    colors = get_categorical_colors(n_slices)

    # Create figure
    fig = go.Figure(
        data=[
            go.Pie(
                labels=df[names].to_list(),
                values=df[values].to_list(),
                hole=hole_size,
                marker={"colors": colors},
            )
        ]
    )

    # Update layout - exclude title from template to avoid conflict
    layout_kwargs = {k: v for k, v in template["layout"].items() if k != "title"}
    fig.update_layout(
        title=title,
        height=height,
        **layout_kwargs,
    )

    return fig
