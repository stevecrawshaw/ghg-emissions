"""Folium map creation functions with WECA branding.

This module provides functions for creating interactive Folium maps
for geographic visualization of emissions and EPC data.

Map Types:
- Choropleth maps for emissions by geography (LSOA, MSOA, LA)
- Point maps for properties (EPC locations)
- Boundary overlays (LA, CA boundaries)
- Multi-layer maps with controls

All maps use WECA colors and styling where applicable.

Example:
    >>> from src.visualization.maps import create_choropleth_map
    >>> import polars as pl
    >>>
    >>> # Create emissions choropleth
    >>> map_obj = create_choropleth_map(
    ...     df=emissions_df,
    ...     geojson_data=boundaries,
    ...     location_col="lsoa_code",
    ...     value_col="emissions",
    ...     legend_name="Emissions (kt CO2e)",
    ... )
    >>> map_obj.save("emissions_map.html")
"""

from typing import Any

import folium
import polars as pl

from src.visualization.themes import (
    CLARET,
    SOFT_CLARET,
    SOFT_GREEN,
    WEST_GREEN,
    WHITE,
)


class MapError(Exception):
    """Exception raised for map creation errors.

    Attributes:
        message: Explanation of the error
        map_type: Type of map that failed
    """

    def __init__(self, message: str, map_type: str | None = None) -> None:
        """Initialize MapError.

        Args:
            message: Explanation of the error
            map_type: Type of map that failed (optional)
        """
        self.message = message
        self.map_type = map_type
        super().__init__(self.message)


def create_base_map(
    center: tuple[float, float] = (51.4545, -2.5879),
    zoom_start: int = 10,
    tiles: str = "CartoDB positron",
    height: str = "600px",
    width: str = "100%",
) -> folium.Map:
    """Create a base Folium map centered on Bristol/WECA region.

    Args:
        center: Map center coordinates (lat, lon). Default: Bristol city center
        zoom_start: Initial zoom level (default: 10 for WECA region)
        tiles: Base map tiles - "CartoDB positron" (light), "CartoDB dark_matter"
            (dark), "OpenStreetMap" (default OSM). Default: CartoDB positron
            for clean, professional look
        height: Map height as CSS string (default: "600px")
        width: Map width as CSS string (default: "100%")

    Returns:
        Folium Map object

    Example:
        >>> base_map = create_base_map(zoom_start=9)  # Wider WECA view
        >>> # Add layers to base_map
        >>> base_map.save("map.html")
    """
    m = folium.Map(
        location=center,
        zoom_start=zoom_start,
        tiles=tiles,
        width=width,
        height=height,
    )

    return m


def create_choropleth_map(
    df: pl.DataFrame,
    geojson_data: dict[str, Any] | str,
    location_col: str,
    value_col: str,
    legend_name: str,
    center: tuple[float, float] = (51.4545, -2.5879),
    zoom_start: int = 10,
    colorscale: str = "sequential",
    reverse_colors: bool = False,
    bins: int | None = None,
    nan_fill_color: str = "#CCCCCC",
    tiles: str = "CartoDB positron",
    height: str = "600px",
) -> folium.Map:
    """Create a choropleth map showing values by geographic area.

    Useful for visualizing emissions by LSOA, MSOA, or LA with color-coded
    regions based on emission levels.

    Args:
        df: DataFrame with geographic codes and values
        geojson_data: GeoJSON dictionary or file path with boundary polygons.
            Must have feature properties matching location_col
        location_col: Column name in df with geographic codes (e.g., "lsoa_code")
        value_col: Column name in df with values to visualize
        legend_name: Legend title (e.g., "Emissions (kt CO2e)")
        center: Map center coordinates (lat, lon)
        zoom_start: Initial zoom level
        colorscale: Color scale type - "sequential" (low to high),
            "diverging" (negative to positive). Default: "sequential"
        reverse_colors: Reverse the color scale (default: False)
        bins: Number of bins for classification (default: None for continuous)
        nan_fill_color: Color for areas with no data (default: light gray)
        tiles: Base map tiles (default: CartoDB positron)
        height: Map height as CSS string

    Returns:
        Folium Map object

    Raises:
        MapError: If required columns are missing or GeoJSON is invalid

    Example:
        >>> # Emissions by LSOA
        >>> map_obj = create_choropleth_map(
        ...     df=lsoa_emissions,
        ...     geojson_data=lsoa_boundaries_geojson,
        ...     location_col="lsoa21cd",
        ...     value_col="territorial_emissions_kt_co2e",
        ...     legend_name="Emissions (kt CO2e)",
        ...     colorscale="sequential",
        ... )
    """
    # Validate columns
    required_cols = [location_col, value_col]
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        msg = f"Columns not found in DataFrame: {missing_cols}"
        raise MapError(msg, map_type="choropleth")

    # Create base map
    m = create_base_map(
        center=center, zoom_start=zoom_start, tiles=tiles, height=height
    )

    # Get ColorBrewer color code for Folium
    # Folium expects ColorBrewer codes, not RGB values
    if colorscale == "sequential":
        # Use green-based sequential scale (matches WECA branding)
        fill_color_code = "YlGn" if not reverse_colors else "GnBu"
    elif colorscale == "diverging":
        # Use red-green diverging scale
        fill_color_code = "RdYlGn" if not reverse_colors else "RdYlGn_r"
    else:
        msg = f"Invalid colorscale '{colorscale}'. Must be 'sequential' or 'diverging'"
        raise MapError(msg, map_type="choropleth")

    # Convert DataFrame to pandas for Folium
    df_pandas = df.select([location_col, value_col]).to_pandas()

    # Create choropleth
    folium.Choropleth(
        geo_data=geojson_data,
        data=df_pandas,
        columns=[location_col, value_col],
        key_on=f"feature.properties.{location_col}",
        fill_color=fill_color_code,
        fill_opacity=0.7,
        line_opacity=0.2,
        legend_name=legend_name,
        bins=bins,
        nan_fill_color=nan_fill_color,
    ).add_to(m)

    # Add layer control
    folium.LayerControl().add_to(m)

    return m


def create_point_map(
    df: pl.DataFrame,
    lat_col: str,
    lon_col: str,
    popup_cols: list[str] | None = None,
    color_col: str | None = None,
    size_col: str | None = None,
    center: tuple[float, float] | None = None,
    zoom_start: int = 10,
    marker_color: str = WEST_GREEN,
    tiles: str = "CartoDB positron",
    height: str = "600px",
    cluster: bool = True,
) -> folium.Map:
    """Create a point map showing individual locations (e.g., properties).

    Useful for showing EPC property locations, with optional clustering
    for performance with large datasets.

    Args:
        df: DataFrame with location data
        lat_col: Column name with latitude values
        lon_col: Column name with longitude values
        popup_cols: Columns to show in popup (default: None shows lat/lon)
        color_col: Column name for marker color grouping (optional)
        size_col: Column name for marker size (optional)
        center: Map center (lat, lon). If None, calculates from data
        zoom_start: Initial zoom level
        marker_color: Default marker color (default: WECA West Green)
        tiles: Base map tiles
        height: Map height as CSS string
        cluster: Use marker clustering for performance (default: True)

    Returns:
        Folium Map object

    Raises:
        MapError: If required columns are missing

    Example:
        >>> # Show EPC properties
        >>> map_obj = create_point_map(
        ...     df=epc_data,
        ...     lat_col="lat",
        ...     lon_col="long",
        ...     popup_cols=["address", "energy_rating", "property_type"],
        ...     cluster=True,
        ... )
    """
    # Validate columns
    required_cols = [lat_col, lon_col]
    if popup_cols:
        required_cols.extend(popup_cols)
    if color_col:
        required_cols.append(color_col)
    if size_col:
        required_cols.append(size_col)

    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        msg = f"Columns not found in DataFrame: {missing_cols}"
        raise MapError(msg, map_type="point_map")

    # Calculate center from data if not provided
    if center is None:
        center = (
            float(df[lat_col].mean()),
            float(df[lon_col].mean()),
        )

    # Create base map
    m = create_base_map(
        center=center, zoom_start=zoom_start, tiles=tiles, height=height
    )

    # Add marker cluster if requested
    if cluster:
        from folium.plugins import MarkerCluster

        marker_cluster = MarkerCluster().add_to(m)
        add_to = marker_cluster
    else:
        add_to = m

    # Add markers
    for row in df.iter_rows(named=True):
        lat = row[lat_col]
        lon = row[lon_col]

        # Skip if coordinates are null
        if lat is None or lon is None:
            continue

        # Create popup HTML
        if popup_cols:
            popup_html = "<br>".join(
                f"<b>{col}:</b> {row[col]}"
                for col in popup_cols
                if row[col] is not None
            )
        else:
            popup_html = f"<b>Lat:</b> {lat}<br><b>Lon:</b> {lon}"

        # Determine marker color (could map categories to colors in future)
        color = marker_color

        # Add marker
        folium.CircleMarker(
            location=[lat, lon],
            radius=5 if not size_col else row[size_col],
            popup=folium.Popup(popup_html, max_width=300),
            color=color,
            fill=True,
            fillColor=color,
            fillOpacity=0.7,
        ).add_to(add_to)

    return m


def add_boundary_layer(
    map_obj: folium.Map,
    geojson_data: dict[str, Any] | str,
    layer_name: str = "Boundaries",
    color: str = WEST_GREEN,
    weight: int = 2,
    fill: bool = False,
    tooltip_field: str | None = None,
) -> folium.Map:
    """Add a boundary layer to an existing map.

    Useful for adding LA or LSOA boundaries as overlays.

    Args:
        map_obj: Existing Folium Map object
        geojson_data: GeoJSON dictionary or file path with boundary polygons
        layer_name: Name for layer control (default: "Boundaries")
        color: Boundary line color (default: WECA West Green)
        weight: Line thickness (default: 2)
        fill: Fill polygons (default: False for outline only)
        tooltip_field: GeoJSON property field to show on hover (optional)

    Returns:
        Updated Folium Map object

    Example:
        >>> # Create base choropleth
        >>> m = create_choropleth_map(...)
        >>>
        >>> # Add LA boundaries overlay
        >>> m = add_boundary_layer(
        ...     m,
        ...     geojson_data=la_boundaries,
        ...     layer_name="Local Authorities",
        ...     color="#1D4F2B",
        ...     weight=3,
        ... )
    """
    # Create feature group for layer control
    fg = folium.FeatureGroup(name=layer_name)

    # Style function
    style_function = lambda x: {  # noqa: E731
        "color": color,
        "weight": weight,
        "fillOpacity": 0.1 if fill else 0,
    }

    # Add GeoJSON layer
    geojson_layer = folium.GeoJson(
        geojson_data,
        style_function=style_function,
    )

    # Add tooltip if field specified
    if tooltip_field:
        geojson_layer.add_child(
            folium.features.GeoJsonTooltip(fields=[tooltip_field], aliases=[""])
        )

    geojson_layer.add_to(fg)
    fg.add_to(map_obj)

    return map_obj


def create_heatmap(
    df: pl.DataFrame,
    lat_col: str,
    lon_col: str,
    weight_col: str | None = None,
    center: tuple[float, float] | None = None,
    zoom_start: int = 10,
    radius: int = 15,
    blur: int = 15,
    min_opacity: float = 0.3,
    tiles: str = "CartoDB positron",
    height: str = "600px",
) -> folium.Map:
    """Create a heatmap showing point density or weighted intensity.

    Useful for showing high-emission areas or property concentration.

    Args:
        df: DataFrame with location data
        lat_col: Column name with latitude values
        lon_col: Column name with longitude values
        weight_col: Column name for weights (optional, uses count if None)
        center: Map center (lat, lon). If None, calculates from data
        zoom_start: Initial zoom level
        radius: Heatmap radius (pixels, default: 15)
        blur: Blur amount (pixels, default: 15)
        min_opacity: Minimum opacity (0-1, default: 0.3)
        tiles: Base map tiles
        height: Map height as CSS string

    Returns:
        Folium Map object

    Raises:
        MapError: If required columns are missing

    Example:
        >>> # Show high-emission property density
        >>> map_obj = create_heatmap(
        ...     df=properties_df,
        ...     lat_col="lat",
        ...     lon_col="long",
        ...     weight_col="annual_emissions_kg_co2",
        ...     radius=20,
        ... )
    """
    from folium.plugins import HeatMap

    # Validate columns
    required_cols = [lat_col, lon_col]
    if weight_col:
        required_cols.append(weight_col)

    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        msg = f"Columns not found in DataFrame: {missing_cols}"
        raise MapError(msg, map_type="heatmap")

    # Calculate center from data if not provided
    if center is None:
        center = (
            float(df[lat_col].mean()),
            float(df[lon_col].mean()),
        )

    # Create base map
    m = create_base_map(
        center=center, zoom_start=zoom_start, tiles=tiles, height=height
    )

    # Prepare heatmap data
    if weight_col:
        # Filter out null coordinates or weights
        heat_df = df.filter(
            pl.col(lat_col).is_not_null()
            & pl.col(lon_col).is_not_null()
            & pl.col(weight_col).is_not_null()
        )
        heat_data = [
            [row[lat_col], row[lon_col], row[weight_col]]
            for row in heat_df.iter_rows(named=True)
        ]
    else:
        # Filter out null coordinates
        heat_df = df.filter(
            pl.col(lat_col).is_not_null() & pl.col(lon_col).is_not_null()
        )
        heat_data = [
            [row[lat_col], row[lon_col]] for row in heat_df.iter_rows(named=True)
        ]

    # Add heatmap layer
    HeatMap(
        heat_data,
        radius=radius,
        blur=blur,
        min_opacity=min_opacity,
        gradient={
            0.0: WHITE,
            0.4: SOFT_GREEN,
            0.6: WEST_GREEN,
            0.8: SOFT_CLARET,
            1.0: CLARET,
        },
    ).add_to(m)

    return m


def create_bubble_map(
    df: pl.DataFrame,
    lat_col: str,
    lon_col: str,
    size_col: str,
    name_col: str,
    value_col: str,
    center: tuple[float, float] | None = None,
    zoom_start: int = 10,
    max_radius: int = 30,
    color: str = WEST_GREEN,
    tiles: str = "CartoDB positron",
    height: str = "600px",
) -> folium.Map:
    """Create a bubble map with circles sized by value.

    Useful for showing emissions by LA or MSOA with circle size
    proportional to emission levels.

    Args:
        df: DataFrame with location and value data
        lat_col: Column name with latitude values (e.g., LA centroid)
        lon_col: Column name with longitude values
        size_col: Column name for bubble size (e.g., emissions)
        name_col: Column name for location name (shown in popup)
        value_col: Column name for value display in popup
        center: Map center (lat, lon). If None, calculates from data
        zoom_start: Initial zoom level
        max_radius: Maximum bubble radius in pixels (default: 30)
        color: Bubble color (default: WECA West Green)
        tiles: Base map tiles
        height: Map height as CSS string

    Returns:
        Folium Map object

    Raises:
        MapError: If required columns are missing

    Example:
        >>> # Show LA emissions as bubbles
        >>> map_obj = create_bubble_map(
        ...     df=la_emissions,
        ...     lat_col="centroid_lat",
        ...     lon_col="centroid_lon",
        ...     size_col="total_emissions",
        ...     name_col="local_authority",
        ...     value_col="total_emissions",
        ... )
    """
    # Validate columns
    required_cols = [lat_col, lon_col, size_col, name_col, value_col]
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        msg = f"Columns not found in DataFrame: {missing_cols}"
        raise MapError(msg, map_type="bubble_map")

    # Calculate center from data if not provided
    if center is None:
        center = (
            float(df[lat_col].mean()),
            float(df[lon_col].mean()),
        )

    # Create base map
    m = create_base_map(
        center=center, zoom_start=zoom_start, tiles=tiles, height=height
    )

    # Calculate radius scaling
    max_value = float(df[size_col].max())
    min_value = float(df[size_col].min())
    value_range = max_value - min_value

    # Add bubbles
    for row in df.iter_rows(named=True):
        lat = row[lat_col]
        lon = row[lon_col]
        size = row[size_col]
        name = row[name_col]
        value = row[value_col]

        # Skip if coordinates or size are null
        if lat is None or lon is None or size is None:
            continue

        # Calculate radius (scaled to max_radius)
        if value_range > 0:
            radius = ((size - min_value) / value_range) * max_radius
        else:
            radius = max_radius / 2

        # Create popup
        popup_html = f"<b>{name}</b><br>{value_col}: {value:.2f}"

        # Add circle marker
        folium.CircleMarker(
            location=[lat, lon],
            radius=radius,
            popup=folium.Popup(popup_html, max_width=200),
            color=color,
            fill=True,
            fillColor=color,
            fillOpacity=0.6,
            weight=2,
        ).add_to(m)

    return m


def add_legend(
    map_obj: folium.Map,
    title: str,
    colors: dict[str, str],
    position: str = "bottomright",
) -> folium.Map:
    """Add a custom legend to a map.

    Useful when the default Folium legend doesn't meet needs.

    Args:
        map_obj: Existing Folium Map object
        title: Legend title
        colors: Dictionary mapping labels to colors
        position: Legend position - "topleft", "topright", "bottomleft",
            "bottomright" (default: "bottomright")

    Returns:
        Updated Folium Map object

    Example:
        >>> m = create_base_map()
        >>> m = add_legend(
        ...     m,
        ...     title="Energy Rating",
        ...     colors={
        ...         "A-B": "#1D4F2B",
        ...         "C": "#40A832",
        ...         "D-E": "#ED8073",
        ...         "F-G": "#CE132D",
        ...     },
        ... )
    """
    # Create legend HTML with position styling
    vertical_pos = position.replace("top", "top: 10px;").replace(
        "bottom", "bottom: 10px;"
    )
    horizontal_pos = position.replace("left", "left: 10px;").replace(
        "right", "right: 10px;"
    )

    legend_html = f"""
    <div style="position: fixed;
                {vertical_pos}
                {horizontal_pos}
                width: 150px;
                background-color: white;
                border: 2px solid grey;
                z-index: 9999;
                font-size: 14px;
                padding: 10px;
                border-radius: 5px;
                ">
        <p style="margin: 0 0 10px 0; font-weight: bold;">{title}</p>
    """

    for label, color in colors.items():
        legend_html += f"""
        <p style="margin: 5px 0;">
            <span style="background-color: {color};
                         width: 20px;
                         height: 20px;
                         display: inline-block;
                         margin-right: 5px;
                         border: 1px solid #999;">
            </span>
            {label}
        </p>
        """

    legend_html += "</div>"

    # Add to map
    map_obj.get_root().html.add_child(folium.Element(legend_html))

    return map_obj
