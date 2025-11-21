"""WECA visual identity and theming for charts and visualizations.

This module provides WECA (West of England Combined Authority) brand colors,
Plotly templates, and color scale functions for consistent data visualization.

Based on WECA Brand Guidelines (weca-brand.json).

Example:
    >>> from src.visualization.themes import get_plotly_template, WECA_COLORS
    >>> import plotly.express as px
    >>>
    >>> # Use WECA template for a chart
    >>> fig = px.line(df, x="year", y="emissions")
    >>> fig.update_layout(template=get_plotly_template())
    >>>
    >>> # Use WECA colors
    >>> fig = px.bar(df, x="sector", y="emissions",
    ...              color_discrete_sequence=WECA_COLORS["primary"])
"""

from typing import Any

import plotly.graph_objects as go
import plotly.io as pio

# WECA Brand Colors (from weca-brand.json)

# Primary Colors
WEST_GREEN = "#40A832"  # Primary brand color
FOREST_GREEN = "#1D4F2B"  # Dark green accent
RICH_PURPLE = "#590075"  # Purple accent
CLARET = "#CE132D"  # Red accent
BLACK = "#1F1F1F"  # WECA black

# Secondary Colors
GREY = "#3C3C3C"  # Dark grey
SOFT_GREEN = "#8FCC87"  # Light green for charts
SOFT_PURPLE = "#9C66AB"  # Light purple for charts
SOFT_CLARET = "#ED8073"  # Light red/coral for charts
WARM_GREY = "#A6A6A5"  # Warm grey
WHITE = "#FFFFFF"  # White

# Organized color palettes
WECA_COLORS = {
    "primary": [WEST_GREEN, FOREST_GREEN, RICH_PURPLE, CLARET, BLACK],
    "secondary": [SOFT_GREEN, SOFT_PURPLE, SOFT_CLARET, WARM_GREY, GREY],
    "sequential_green": [WHITE, SOFT_GREEN, WEST_GREEN, FOREST_GREEN, BLACK],
    "diverging": [CLARET, SOFT_CLARET, WHITE, SOFT_GREEN, WEST_GREEN],
    "categorical": [
        WEST_GREEN,
        RICH_PURPLE,
        CLARET,
        SOFT_GREEN,
        SOFT_PURPLE,
        SOFT_CLARET,
        FOREST_GREEN,
        WARM_GREY,
    ],
}


def get_plotly_template() -> dict[str, Any]:
    """Get Plotly template with WECA branding.

    Returns a Plotly template dictionary that applies WECA colors, fonts,
    and styling to all charts.

    Returns:
        Dictionary with Plotly template configuration

    Example:
        >>> import plotly.express as px
        >>> template = get_plotly_template()
        >>> fig = px.scatter(df, x="x", y="y", template=template)
        >>> fig.show()
    """
    template = {
        "layout": {
            # Color theme
            "colorway": WECA_COLORS["categorical"],
            # Typography
            "font": {
                "family": "Open Sans, Trebuchet MS, sans-serif",
                "size": 12,
                "color": BLACK,
            },
            "title": {
                "font": {
                    "family": "Open Sans, Trebuchet MS, sans-serif",
                    "size": 20,
                    "color": BLACK,
                },
                "x": 0.05,  # Left-align title
            },
            # Background colors
            "paper_bgcolor": WHITE,
            "plot_bgcolor": "#F5F5F5",  # Very light grey for plot area
            # Grid and axes
            "xaxis": {
                "gridcolor": "#E0E0E0",
                "linecolor": GREY,
                "zerolinecolor": GREY,
                "title": {"font": {"size": 14}},
            },
            "yaxis": {
                "gridcolor": "#E0E0E0",
                "linecolor": GREY,
                "zerolinecolor": GREY,
                "title": {"font": {"size": 14}},
            },
            # Legend
            "legend": {
                "bgcolor": "rgba(255, 255, 255, 0.8)",
                "bordercolor": GREY,
                "borderwidth": 1,
            },
            # Hover label
            "hoverlabel": {
                "bgcolor": WHITE,
                "bordercolor": WEST_GREEN,
                "font": {"family": "Open Sans, Trebuchet MS, sans-serif"},
            },
        },
        # Trace-specific defaults
        "data": {
            "scatter": [
                {
                    "marker": {"line": {"width": 0.5, "color": WHITE}},
                }
            ],
            "bar": [
                {
                    "marker": {
                        "line": {"width": 0.5, "color": WHITE},
                        "pattern": {"fillmode": "overlay", "size": 10, "solidity": 0.2},
                    },
                }
            ],
            "line": [
                {
                    "line": {"width": 3},
                }
            ],
        },
    }

    return template


def register_weca_template() -> None:
    """Register WECA template as a named Plotly template.

    After calling this function, you can use template="weca" in Plotly figures.

    Example:
        >>> register_weca_template()
        >>> import plotly.express as px
        >>> fig = px.bar(df, x="x", y="y", template="weca")
        >>> fig.show()
    """
    template = get_plotly_template()
    pio.templates["weca"] = go.layout.Template(layout=template["layout"])


def get_sequential_colorscale(
    color: str = "green",
    n_colors: int = 9,
    reverse: bool = False,
) -> list[str]:
    """Get a sequential color scale based on WECA colors.

    Creates a sequential color scale from light to dark for a specified color.

    Args:
        color: Base color ("green", "purple", "red"). Default: "green"
        n_colors: Number of colors in the scale (default: 9)
        reverse: If True, reverse the scale (dark to light)

    Returns:
        List of hex color strings

    Raises:
        ValueError: If color is not recognized

    Example:
        >>> colors = get_sequential_colorscale("green", n_colors=5)
        >>> import plotly.express as px
        >>> fig = px.choropleth(df, locations="code", color="emissions",
        ...                     color_continuous_scale=colors)
    """
    import plotly.express as px

    # Base colors for each scale
    scales = {
        "green": [WHITE, SOFT_GREEN, WEST_GREEN, FOREST_GREEN],
        "purple": [WHITE, SOFT_PURPLE, RICH_PURPLE, BLACK],
        "red": [WHITE, SOFT_CLARET, CLARET, BLACK],
    }

    if color not in scales:
        msg = f"Color '{color}' not recognized. Choose from: {list(scales.keys())}"
        raise ValueError(msg)

    # Use Plotly's color interpolation
    base_colors = scales[color]
    colorscale = px.colors.sample_colorscale(
        base_colors,
        n_colors,
        colortype="rgb",
    )

    # Convert RGB tuples to hex
    hex_colors = [px.colors.label_rgb(c) for c in colorscale]

    if reverse:
        hex_colors = list(reversed(hex_colors))

    return hex_colors


def get_diverging_colorscale(
    n_colors: int = 11,
    reverse: bool = False,
) -> list[str]:
    """Get a diverging color scale using WECA colors.

    Creates a diverging color scale from red (negative) through white (neutral)
    to green (positive), suitable for showing deviations from a baseline.

    Args:
        n_colors: Number of colors in the scale (default: 11, should be odd)
        reverse: If True, reverse the scale (green to red)

    Returns:
        List of hex color strings

    Example:
        >>> colors = get_diverging_colorscale(n_colors=11)
        >>> import plotly.express as px
        >>> # Show emissions change from baseline
        >>> fig = px.choropleth(df, locations="code", color="change_pct",
        ...                     color_continuous_scale=colors)
    """
    import plotly.express as px

    # Diverging: Red (bad) -> White (neutral) -> Green (good)
    base_colors = [CLARET, SOFT_CLARET, WHITE, SOFT_GREEN, WEST_GREEN]

    colorscale = px.colors.sample_colorscale(
        base_colors,
        n_colors,
        colortype="rgb",
    )

    hex_colors = [px.colors.label_rgb(c) for c in colorscale]

    if reverse:
        hex_colors = list(reversed(hex_colors))

    return hex_colors


def get_categorical_colors(n_colors: int | None = None) -> list[str]:
    """Get categorical colors from WECA palette.

    Returns distinct colors suitable for categorical data (sectors, regions, etc.).

    Args:
        n_colors: Number of colors to return. If None, returns all categorical colors.
            If n_colors > available colors, cycles through the palette.

    Returns:
        List of hex color strings

    Example:
        >>> colors = get_categorical_colors(n_colors=4)
        >>> import plotly.express as px
        >>> fig = px.bar(df, x="sector", y="emissions",
        ...              color="sector", color_discrete_sequence=colors)
    """
    colors = WECA_COLORS["categorical"]

    if n_colors is None:
        return colors

    # Cycle through colors if we need more than available
    if n_colors > len(colors):
        return (colors * ((n_colors // len(colors)) + 1))[:n_colors]

    return colors[:n_colors]


def check_color_contrast(
    foreground: str,
    background: str,
) -> tuple[float, str]:
    """Check color contrast ratio for accessibility (WCAG).

    Calculates the contrast ratio between two colors to ensure text readability.
    WCAG guidelines: AA requires 4.5:1 for normal text, 3:1 for large text.

    Args:
        foreground: Hex color code (e.g., "#40A832")
        background: Hex color code (e.g., "#FFFFFF")

    Returns:
        Tuple of (contrast_ratio, wcag_level) where wcag_level is
        "AAA", "AA", or "Fail"

    Example:
        >>> ratio, level = check_color_contrast(WEST_GREEN, WHITE)
        >>> print(f"Contrast ratio: {ratio:.2f}:1 ({level})")
        Contrast ratio: 3.04:1 (AA)
    """

    def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
        """Convert hex to RGB."""
        hex_color = hex_color.lstrip("#")
        return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))  # type: ignore

    def relative_luminance(rgb: tuple[int, int, int]) -> float:
        """Calculate relative luminance."""
        r, g, b = [x / 255 for x in rgb]

        def adjust(c: float) -> float:
            return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

        return 0.2126 * adjust(r) + 0.7152 * adjust(g) + 0.0722 * adjust(b)

    # Calculate luminance for each color
    fg_lum = relative_luminance(hex_to_rgb(foreground))
    bg_lum = relative_luminance(hex_to_rgb(background))

    # Calculate contrast ratio (always > 1)
    lighter = max(fg_lum, bg_lum)
    darker = min(fg_lum, bg_lum)
    contrast_ratio = (lighter + 0.05) / (darker + 0.05)

    # Determine WCAG level
    if contrast_ratio >= 7:
        wcag_level = "AAA"  # Enhanced
    elif contrast_ratio >= 4.5:
        wcag_level = "AA"  # Standard
    else:
        wcag_level = "Fail"

    return contrast_ratio, wcag_level


# Register the WECA template on import
register_weca_template()
