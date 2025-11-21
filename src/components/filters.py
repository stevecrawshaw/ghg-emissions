"""Streamlit filter widgets for the dashboard.

This module provides reusable filter widgets that maintain consistent
styling and behavior across the dashboard.

Filter Types:
- Year range selectors
- Geography filters (LA, LSOA, MSOA)
- Sector filters
- Property type filters (for EPC data)
- Energy rating filters

All filters return values that can be directly used in data loading functions.

Example:
    >>> import streamlit as st
    >>> from src.components.filters import year_range_filter, la_selector
    >>>
    >>> # In a Streamlit page
    >>> start_year, end_year = year_range_filter()
    >>> selected_las = la_selector()
    >>> # Use in data loading
    >>> df = load_emissions_data(
    ...     start_year=start_year, end_year=end_year, local_authorities=selected_las
    ... )
"""

from collections.abc import Callable
from typing import Any

import streamlit as st


def year_range_filter(
    min_year: int = 2014,
    max_year: int = 2023,
    default_range: tuple[int, int] | None = None,
    key: str = "year_range",
    help_text: str | None = None,
) -> tuple[int, int]:
    """Create a year range slider filter.

    Args:
        min_year: Minimum year available (default: 2014)
        max_year: Maximum year available (default: 2023)
        default_range: Default selected range (min, max). If None, uses
            (min_year, max_year)
        key: Streamlit widget key for state management
        help_text: Help text to display (optional)

    Returns:
        Tuple of (start_year, end_year) as selected by user

    Example:
        >>> start_year, end_year = year_range_filter(
        ...     min_year=2014, max_year=2023, default_range=(2019, 2023)
        ... )
    """
    if default_range is None:
        default_range = (min_year, max_year)

    if help_text is None:
        help_text = "Select the year range for analysis"

    year_range = st.slider(
        "Year Range",
        min_value=min_year,
        max_value=max_year,
        value=default_range,
        key=key,
        help=help_text,
    )

    return year_range


def single_year_filter(
    min_year: int = 2014,
    max_year: int = 2023,
    default_year: int | None = None,
    key: str = "single_year",
    help_text: str | None = None,
) -> int:
    """Create a single year selector.

    Args:
        min_year: Minimum year available (default: 2014)
        max_year: Maximum year available (default: 2023)
        default_year: Default selected year. If None, uses max_year
        key: Streamlit widget key for state management
        help_text: Help text to display (optional)

    Returns:
        Selected year as integer

    Example:
        >>> year = single_year_filter(default_year=2023)
    """
    if default_year is None:
        default_year = max_year

    if help_text is None:
        help_text = "Select a year for analysis"

    # Create list of years in reverse order (most recent first)
    years = list(range(max_year, min_year - 1, -1))
    default_index = years.index(default_year)

    year = st.selectbox(
        "Year",
        options=years,
        index=default_index,
        key=key,
        help=help_text,
    )

    return int(year)


def la_selector(
    local_authorities: list[str],
    default_selection: list[str] | None = None,
    allow_multiple: bool = True,
    key: str = "la_selector",
    help_text: str | None = None,
) -> list[str] | str:
    """Create a local authority selector.

    Args:
        local_authorities: List of LA names or codes to choose from
        default_selection: Default selected LAs. If None, selects all
        allow_multiple: Allow multiple LA selection (default: True)
        key: Streamlit widget key for state management
        help_text: Help text to display (optional)

    Returns:
        List of selected LA names/codes if allow_multiple=True,
        single LA name/code if allow_multiple=False

    Example:
        >>> las = ["Bristol", "Bath and NES", "South Gloucestershire"]
        >>> selected = la_selector(las, default_selection=["Bristol"])
    """
    if default_selection is None:
        default_selection = local_authorities

    if help_text is None:
        help_text = "Select local authority/authorities"

    if allow_multiple:
        selected = st.multiselect(
            "Local Authorities",
            options=local_authorities,
            default=default_selection,
            key=key,
            help=help_text,
        )
        return selected
    else:
        # Single selection
        default_index = (
            local_authorities.index(default_selection[0]) if default_selection else 0
        )
        selected = st.selectbox(
            "Local Authority",
            options=local_authorities,
            index=default_index,
            key=key,
            help=help_text,
        )
        return selected


def sector_filter(
    sectors: list[str],
    default_selection: list[str] | None = None,
    allow_all: bool = True,
    key: str = "sector_filter",
    help_text: str | None = None,
) -> list[str]:
    """Create a sector multiselect filter.

    Args:
        sectors: List of sector names to choose from
        default_selection: Default selected sectors. If None, selects all
        allow_all: Show "Select All" option (default: True)
        key: Streamlit widget key for state management
        help_text: Help text to display (optional)

    Returns:
        List of selected sector names

    Example:
        >>> sectors = ["Transport", "Domestic", "Industry"]
        >>> selected = sector_filter(sectors, default_selection=["Transport"])
    """
    if default_selection is None:
        default_selection = sectors

    if help_text is None:
        help_text = "Select emission sectors to analyze"

    # Add "Select All" checkbox if enabled
    if allow_all:
        col1, col2 = st.columns([3, 1])
        with col1:
            selected = st.multiselect(
                "Sectors",
                options=sectors,
                default=default_selection,
                key=key,
                help=help_text,
            )
        with col2:
            select_all = st.checkbox("Select All", value=False, key=f"{key}_all")
            if select_all:
                selected = sectors
    else:
        selected = st.multiselect(
            "Sectors",
            options=sectors,
            default=default_selection,
            key=key,
            help=help_text,
        )

    return selected


def property_type_filter(
    property_types: list[str],
    default_selection: list[str] | None = None,
    key: str = "property_type_filter",
    help_text: str | None = None,
) -> list[str]:
    """Create a property type multiselect filter for EPC data.

    Args:
        property_types: List of property types (e.g., "House", "Flat", "Bungalow")
        default_selection: Default selected types. If None, selects all
        key: Streamlit widget key for state management
        help_text: Help text to display (optional)

    Returns:
        List of selected property types

    Example:
        >>> types = ["House", "Flat", "Bungalow", "Maisonette"]
        >>> selected = property_type_filter(types)
    """
    if default_selection is None:
        default_selection = property_types

    if help_text is None:
        help_text = "Select property types to include"

    selected = st.multiselect(
        "Property Types",
        options=property_types,
        default=default_selection,
        key=key,
        help=help_text,
    )

    return selected


def energy_rating_filter(
    ratings: list[str] | None = None,
    default_selection: list[str] | None = None,
    key: str = "energy_rating_filter",
    help_text: str | None = None,
) -> list[str]:
    """Create an energy rating multiselect filter.

    Args:
        ratings: List of energy ratings. If None, uses A-G
        default_selection: Default selected ratings. If None, selects all
        key: Streamlit widget key for state management
        help_text: Help text to display (optional)

    Returns:
        List of selected energy ratings

    Example:
        >>> selected = energy_rating_filter(default_selection=["D", "E", "F"])
    """
    if ratings is None:
        ratings = ["A", "B", "C", "D", "E", "F", "G"]

    if default_selection is None:
        default_selection = ratings

    if help_text is None:
        help_text = "Select energy performance ratings"

    selected = st.multiselect(
        "Energy Ratings",
        options=ratings,
        default=default_selection,
        key=key,
        help=help_text,
    )

    return selected


def geography_level_selector(
    levels: list[str] | None = None,
    default_level: str | None = None,
    key: str = "geography_level",
    help_text: str | None = None,
) -> str:
    """Create a geography level selector (LSOA, MSOA, LA, CA).

    Args:
        levels: List of geography levels. If None, uses ["LSOA", "MSOA", "LA", "CA"]
        default_level: Default selected level. If None, uses "LA"
        key: Streamlit widget key for state management
        help_text: Help text to display (optional)

    Returns:
        Selected geography level as string

    Example:
        >>> level = geography_level_selector(default_level="LSOA")
    """
    if levels is None:
        levels = ["LSOA", "MSOA", "LA", "CA"]

    if default_level is None:
        default_level = "LA"

    if help_text is None:
        help_text = "Select geographic aggregation level"

    level = st.selectbox(
        "Geography Level",
        options=levels,
        index=levels.index(default_level) if default_level in levels else 0,
        key=key,
        help=help_text,
    )

    return level


def comparison_selector(
    options: list[str],
    default_selection: list[str] | None = None,
    max_selections: int = 5,
    key: str = "comparison_selector",
    help_text: str | None = None,
) -> list[str]:
    """Create a selector for comparing multiple entities (LAs, CAs, etc.).

    Args:
        options: List of entities to choose from
        default_selection: Default selected entities. If None, selects first 3
        max_selections: Maximum number of selections allowed (default: 5)
        key: Streamlit widget key for state management
        help_text: Help text to display (optional)

    Returns:
        List of selected entities (limited to max_selections)

    Example:
        >>> cas = ["West of England", "Greater Manchester", "West Midlands"]
        >>> selected = comparison_selector(cas, max_selections=3)
    """
    if default_selection is None:
        default_selection = options[:3] if len(options) >= 3 else options

    if help_text is None:
        help_text = f"Select up to {max_selections} for comparison"

    selected = st.multiselect(
        "Compare",
        options=options,
        default=default_selection,
        max_selections=max_selections,
        key=key,
        help=help_text,
    )

    return selected


def data_freshness_indicator(freshness_data: dict[str, int | None]) -> None:
    """Display data freshness indicator showing latest available data years.

    Args:
        freshness_data: Dictionary mapping dataset names to latest year
            (e.g., {"emissions": 2023, "epc_domestic": 2024})

    Example:
        >>> freshness = {"emissions": 2023, "epc_domestic": 2024}
        >>> data_freshness_indicator(freshness)
    """
    st.sidebar.markdown("### 📅 Data Currency")

    for dataset, year in freshness_data.items():
        if year is not None:
            st.sidebar.caption(f"{dataset.replace('_', ' ').title()}: {year}")
        else:
            st.sidebar.caption(f"{dataset.replace('_', ' ').title()}: No data")


def filter_reset_button(
    key: str = "reset_filters",
    label: str = "Reset Filters",
) -> bool:
    """Create a button to reset all filters to defaults.

    Args:
        key: Streamlit widget key
        label: Button label text

    Returns:
        True if button was clicked, False otherwise

    Example:
        >>> if filter_reset_button():
        ...     st.rerun()
    """
    return st.button(label, key=key, type="secondary")


def create_filter_summary(filters: dict[str, Any]) -> None:
    """Display a summary of currently applied filters.

    Useful for showing users what filters are active.

    Args:
        filters: Dictionary of filter names and their values

    Example:
        >>> filters = {
        ...     "Year Range": (2019, 2023),
        ...     "Local Authorities": ["Bristol", "Bath"],
        ...     "Sectors": ["Transport", "Domestic"],
        ... }
        >>> create_filter_summary(filters)
    """
    st.sidebar.markdown("### 🔍 Active Filters")

    for filter_name, filter_value in filters.items():
        if isinstance(filter_value, list | tuple):
            if len(filter_value) == 0:
                value_str = "None"
            elif len(filter_value) == 1:
                value_str = str(filter_value[0])
            elif len(filter_value) > 3:
                first_three = ", ".join(map(str, filter_value[:3]))
                value_str = f"{first_three}... ({len(filter_value)} total)"
            else:
                value_str = ", ".join(map(str, filter_value))
        else:
            value_str = str(filter_value)

        st.sidebar.caption(f"**{filter_name}:** {value_str}")


def advanced_filter_expander(
    title: str = "Advanced Filters",
    expanded: bool = False,
) -> st.expander:
    """Create an expander for advanced/optional filters.

    Args:
        title: Expander title
        expanded: Whether expander is expanded by default

    Returns:
        Streamlit expander context manager

    Example:
        >>> with advanced_filter_expander():
        ...     min_emissions = st.number_input("Min Emissions")
        ...     max_emissions = st.number_input("Max Emissions")
    """
    return st.expander(title, expanded=expanded)


def metric_selector(
    metrics: dict[str, str],
    default_metric: str | None = None,
    key: str = "metric_selector",
    help_text: str | None = None,
) -> str:
    """Create a metric selector for choosing which value to visualize.

    Args:
        metrics: Dictionary mapping metric codes to display names
            (e.g., {"total": "Total Emissions", "per_capita": "Per Capita"})
        default_metric: Default selected metric code. If None, uses first
        key: Streamlit widget key for state management
        help_text: Help text to display (optional)

    Returns:
        Selected metric code (dictionary key)

    Example:
        >>> metrics = {
        ...     "territorial_emissions": "Territorial Emissions",
        ...     "la_influenced": "LA Influenced Emissions",
        ...     "per_capita": "Per Capita Emissions",
        ... }
        >>> selected = metric_selector(metrics, default_metric="per_capita")
    """
    if default_metric is None:
        default_metric = list(metrics.keys())[0]

    if help_text is None:
        help_text = "Select metric to display"

    # Create reverse mapping for selectbox (display names as options)
    display_names = list(metrics.values())
    default_index = list(metrics.keys()).index(default_metric)

    selected_display = st.selectbox(
        "Metric",
        options=display_names,
        index=default_index,
        key=key,
        help=help_text,
    )

    # Return the metric code (key)
    return [k for k, v in metrics.items() if v == selected_display][0]


# Type alias for filter functions
FilterFunction = Callable[..., Any]
