"""Data and visualization export utilities for the dashboard.

This module provides functions for exporting data and visualizations
in various formats suitable for download and reuse.

Export Formats:
- CSV: Tabular data export
- Parquet: Efficient columnar format for large datasets
- Excel: Multi-sheet workbooks with formatting
- JSON: Structured data export
- PNG/SVG: Chart image exports
- HTML: Interactive map and chart exports

All export functions are compatible with Streamlit download buttons.

Example:
    >>> import streamlit as st
    >>> from src.components.exports import export_to_csv, create_download_button
    >>>
    >>> # Export data to CSV
    >>> csv_data = export_to_csv(df, filename="emissions_2023")
    >>> create_download_button(
    ...     csv_data, filename="emissions_2023.csv", label="Download CSV"
    ... )
"""

from io import BytesIO, StringIO
from typing import Any

import plotly.graph_objects as go
import polars as pl
import streamlit as st


class ExportError(Exception):
    """Exception raised for export operation errors.

    Attributes:
        message: Explanation of the error
        export_format: Format that failed
    """

    def __init__(self, message: str, export_format: str | None = None) -> None:
        """Initialize ExportError.

        Args:
            message: Explanation of the error
            export_format: Format that failed (optional)
        """
        self.message = message
        self.export_format = export_format
        super().__init__(self.message)


def export_to_csv(
    df: pl.DataFrame,
    filename: str | None = None,
    include_header: bool = True,
) -> bytes:
    """Export DataFrame to CSV format.

    Args:
        df: DataFrame to export
        filename: Optional filename (without extension) for default download name
        include_header: Include column headers (default: True)

    Returns:
        CSV data as bytes

    Raises:
        ExportError: If CSV export fails

    Example:
        >>> csv_data = export_to_csv(df, filename="emissions")
        >>> st.download_button("Download CSV", csv_data, "emissions.csv")
    """
    try:
        # Use StringIO to write CSV, then encode to bytes
        buffer = StringIO()
        df.write_csv(buffer, include_header=include_header)
        csv_str = buffer.getvalue()
        return csv_str.encode("utf-8")
    except Exception as e:
        msg = f"Failed to export to CSV: {e}"
        raise ExportError(msg, export_format="csv") from e


def export_to_parquet(
    df: pl.DataFrame,
    filename: str | None = None,
    compression: str = "snappy",
) -> bytes:
    """Export DataFrame to Parquet format.

    Parquet is efficient for large datasets and preserves data types.

    Args:
        df: DataFrame to export
        filename: Optional filename (without extension)
        compression: Compression codec - "snappy", "gzip", "brotli", "lz4",
            "zstd", or "uncompressed" (default: "snappy")

    Returns:
        Parquet data as bytes

    Raises:
        ExportError: If Parquet export fails

    Example:
        >>> parquet_data = export_to_parquet(df, compression="gzip")
        >>> st.download_button("Download Parquet", parquet_data, "data.parquet")
    """
    try:
        buffer = BytesIO()
        df.write_parquet(buffer, compression=compression)
        return buffer.getvalue()
    except Exception as e:
        msg = f"Failed to export to Parquet: {e}"
        raise ExportError(msg, export_format="parquet") from e


def export_to_json(
    df: pl.DataFrame,
    filename: str | None = None,
    orient: str = "records",
    pretty: bool = False,
) -> bytes:
    """Export DataFrame to JSON format.

    Args:
        df: DataFrame to export
        filename: Optional filename (without extension)
        orient: JSON orientation - "records" (array of objects) or "columns"
            (object with column names as keys) (default: "records")
        pretty: Pretty-print with indentation (default: False)

    Returns:
        JSON data as bytes

    Raises:
        ExportError: If JSON export fails

    Example:
        >>> json_data = export_to_json(df, pretty=True)
        >>> st.download_button("Download JSON", json_data, "data.json")
    """
    try:
        if orient == "records":
            # Array of objects: [{"col1": val, "col2": val}, ...]
            json_str = df.write_json(row_oriented=True)
        elif orient == "columns":
            # Object with columns: {"col1": [vals], "col2": [vals]}
            json_str = df.write_json(row_oriented=False)
        else:
            msg = f"Invalid orient '{orient}'. Must be 'records' or 'columns'"
            raise ExportError(msg, export_format="json")

        # Polars doesn't have built-in pretty printing, so we'll use json module
        if pretty:
            import json

            json_obj = json.loads(json_str)
            json_str = json.dumps(json_obj, indent=2)

        return json_str.encode("utf-8")
    except ExportError:
        raise
    except Exception as e:
        msg = f"Failed to export to JSON: {e}"
        raise ExportError(msg, export_format="json") from e


def export_to_excel(
    dfs: dict[str, pl.DataFrame] | pl.DataFrame,
    filename: str | None = None,
) -> bytes:
    """Export DataFrame(s) to Excel format.

    Supports multiple sheets when a dictionary of DataFrames is provided.

    Args:
        dfs: Single DataFrame or dictionary mapping sheet names to DataFrames
        filename: Optional filename (without extension)

    Returns:
        Excel data as bytes

    Raises:
        ExportError: If Excel export fails

    Example:
        >>> # Single sheet
        >>> excel_data = export_to_excel(df)
        >>>
        >>> # Multiple sheets
        >>> sheets = {
        ...     "Emissions": emissions_df,
        ...     "Population": population_df,
        ...     "Summary": summary_df,
        ... }
        >>> excel_data = export_to_excel(sheets)
        >>> st.download_button("Download Excel", excel_data, "report.xlsx")
    """
    try:
        buffer = BytesIO()

        # Handle single DataFrame or dict
        if isinstance(dfs, pl.DataFrame):
            dfs = {"Data": dfs}

        # Use xlsxwriter.Workbook for multiple sheets with Polars native write_excel
        import xlsxwriter

        workbook = xlsxwriter.Workbook(buffer, {"in_memory": True})

        try:
            for sheet_name, df in dfs.items():
                # Use Polars native write_excel with xlsxwriter workbook
                df.write_excel(
                    workbook=workbook,
                    worksheet=sheet_name,
                    autofit=True,
                )
        finally:
            workbook.close()

        buffer.seek(0)
        return buffer.getvalue()
    except Exception as e:
        msg = f"Failed to export to Excel: {e}"
        raise ExportError(msg, export_format="excel") from e


def export_chart_to_html(
    fig: go.Figure,
    filename: str | None = None,
    include_plotlyjs: str = "cdn",
) -> bytes:
    """Export Plotly figure to standalone HTML.

    Args:
        fig: Plotly Figure object
        filename: Optional filename (without extension)
        include_plotlyjs: How to include Plotly.js - "cdn" (link to CDN),
            True (embed full library), or False (don't include)
            (default: "cdn")

    Returns:
        HTML data as bytes

    Raises:
        ExportError: If HTML export fails

    Example:
        >>> html_data = export_chart_to_html(fig)
        >>> st.download_button("Download Chart", html_data, "chart.html")
    """
    try:
        html_str = fig.to_html(include_plotlyjs=include_plotlyjs)
        return html_str.encode("utf-8")
    except Exception as e:
        msg = f"Failed to export chart to HTML: {e}"
        raise ExportError(msg, export_format="html") from e


def export_chart_to_image(
    fig: go.Figure,
    filename: str | None = None,
    format: str = "png",
    width: int = 1200,
    height: int = 800,
    scale: int = 2,
) -> bytes:
    """Export Plotly figure to static image (PNG, JPG, SVG, PDF).

    Requires kaleido package: uv add kaleido

    Args:
        fig: Plotly Figure object
        filename: Optional filename (without extension)
        format: Image format - "png", "jpg", "jpeg", "webp", "svg", "pdf"
            (default: "png")
        width: Image width in pixels (default: 1200)
        height: Image height in pixels (default: 800)
        scale: Scaling factor for resolution (default: 2 for retina displays)

    Returns:
        Image data as bytes

    Raises:
        ExportError: If image export fails or kaleido not installed

    Example:
        >>> png_data = export_chart_to_image(fig, format="png")
        >>> st.download_button("Download PNG", png_data, "chart.png")
    """
    try:
        img_bytes = fig.to_image(
            format=format,
            width=width,
            height=height,
            scale=scale,
        )
        return img_bytes
    except Exception as e:
        if "kaleido" in str(e).lower():
            msg = "Kaleido package required for image export. Install: uv add kaleido"
        else:
            msg = f"Failed to export chart to {format}: {e}"
        raise ExportError(msg, export_format=format) from e


def export_map_to_html(
    map_obj: Any,
    filename: str | None = None,
) -> bytes:
    """Export Folium map to standalone HTML.

    Args:
        map_obj: Folium Map object
        filename: Optional filename (without extension)

    Returns:
        HTML data as bytes

    Raises:
        ExportError: If HTML export fails

    Example:
        >>> html_data = export_map_to_html(folium_map)
        >>> st.download_button("Download Map", html_data, "map.html")
    """
    try:
        # Folium maps can be saved to HTML string
        from io import StringIO

        buffer = StringIO()
        map_obj.save(buffer, close_file=False)
        html_str = buffer.getvalue()
        return html_str.encode("utf-8")
    except Exception as e:
        msg = f"Failed to export map to HTML: {e}"
        raise ExportError(msg, export_format="html") from e


def create_download_button(
    data: bytes,
    filename: str,
    label: str = "Download",
    mime_type: str | None = None,
    key: str | None = None,
    help_text: str | None = None,
) -> bool:
    """Create a Streamlit download button with automatic MIME type detection.

    Args:
        data: Data to download as bytes
        filename: Filename for download (with extension)
        label: Button label text (default: "Download")
        mime_type: MIME type (optional, auto-detected from extension)
        key: Streamlit widget key
        help_text: Help text to display

    Returns:
        True if button was clicked, False otherwise

    Example:
        >>> csv_data = export_to_csv(df)
        >>> create_download_button(csv_data, "emissions.csv", label="📥 Download Data")
    """
    # Auto-detect MIME type if not provided
    if mime_type is None:
        mime_type = _get_mime_type(filename)

    return st.download_button(
        label=label,
        data=data,
        file_name=filename,
        mime=mime_type,
        key=key,
        help=help_text,
    )


def create_export_menu(
    df: pl.DataFrame,
    base_filename: str,
    formats: list[str] | None = None,
    key_prefix: str = "export",
) -> None:
    """Create a download menu with multiple export format options.

    Args:
        df: DataFrame to export
        base_filename: Base filename (without extension)
        formats: List of formats to offer - ["csv", "parquet", "json", "excel"]
            (default: all formats)
        key_prefix: Prefix for widget keys to avoid conflicts

    Example:
        >>> create_export_menu(df, base_filename="emissions_2023")
    """
    if formats is None:
        formats = ["csv", "parquet", "json", "excel"]

    st.markdown("### 📥 Download Data")

    col_count = len(formats)
    cols = st.columns(col_count)

    for idx, format in enumerate(formats):
        with cols[idx]:
            try:
                if format == "csv":
                    data = export_to_csv(df)
                    filename = f"{base_filename}.csv"
                    label = "CSV"
                elif format == "parquet":
                    data = export_to_parquet(df)
                    filename = f"{base_filename}.parquet"
                    label = "Parquet"
                elif format == "json":
                    data = export_to_json(df)
                    filename = f"{base_filename}.json"
                    label = "JSON"
                elif format == "excel":
                    data = export_to_excel(df)
                    filename = f"{base_filename}.xlsx"
                    label = "Excel"
                else:
                    continue

                create_download_button(
                    data,
                    filename,
                    label=label,
                    key=f"{key_prefix}_{format}",
                )
            except ExportError as e:
                st.error(f"Export failed: {e.message}")


def create_chart_export_menu(
    fig: go.Figure,
    base_filename: str,
    formats: list[str] | None = None,
    key_prefix: str = "chart_export",
) -> None:
    """Create a download menu for exporting charts in multiple formats.

    Args:
        fig: Plotly Figure to export
        base_filename: Base filename (without extension)
        formats: List of formats - ["html", "png", "svg", "pdf"]
            (default: ["html", "png"])
        key_prefix: Prefix for widget keys

    Example:
        >>> create_chart_export_menu(
        ...     fig, base_filename="emissions_chart", formats=["html", "png"]
        ... )
    """
    if formats is None:
        formats = ["html", "png"]

    st.markdown("### 📊 Download Chart")

    col_count = len(formats)
    cols = st.columns(col_count)

    for idx, format in enumerate(formats):
        with cols[idx]:
            try:
                if format == "html":
                    data = export_chart_to_html(fig)
                    filename = f"{base_filename}.html"
                    label = "HTML"
                elif format in ["png", "jpg", "jpeg", "svg", "pdf"]:
                    data = export_chart_to_image(fig, format=format)
                    filename = f"{base_filename}.{format}"
                    label = format.upper()
                else:
                    continue

                create_download_button(
                    data,
                    filename,
                    label=label,
                    key=f"{key_prefix}_{format}",
                )
            except ExportError as e:
                st.error(f"Export failed: {e.message}")


def _get_mime_type(filename: str) -> str:
    """Get MIME type from filename extension.

    Args:
        filename: Filename with extension

    Returns:
        MIME type string
    """
    extension = filename.lower().split(".")[-1]

    mime_types = {
        "csv": "text/csv",
        "json": "application/json",
        "parquet": "application/octet-stream",
        "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "xls": "application/vnd.ms-excel",
        "html": "text/html",
        "htm": "text/html",
        "png": "image/png",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "svg": "image/svg+xml",
        "pdf": "application/pdf",
        "txt": "text/plain",
    }

    return mime_types.get(extension, "application/octet-stream")


def create_data_summary_card(
    df: pl.DataFrame,
    title: str = "Data Summary",
) -> None:
    """Display a summary card with dataset statistics.

    Shows row count, column count, memory usage, and date range (if applicable).

    Args:
        df: DataFrame to summarize
        title: Card title

    Example:
        >>> create_data_summary_card(df, title="Emissions Dataset")
    """
    st.markdown(f"### {title}")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Rows", f"{len(df):,}")

    with col2:
        st.metric("Columns", len(df.columns))

    with col3:
        # Estimate memory usage (bytes)
        memory_bytes = df.estimated_size("mb") * 1024 * 1024
        if memory_bytes < 1024:
            memory_str = f"{memory_bytes:.0f} B"
        elif memory_bytes < 1024 * 1024:
            memory_str = f"{memory_bytes / 1024:.1f} KB"
        else:
            memory_str = f"{memory_bytes / (1024 * 1024):.1f} MB"
        st.metric("Memory", memory_str)

    # Show column types
    with st.expander("Column Details"):
        col_info = []
        for col in df.columns:
            dtype = str(df[col].dtype)
            null_count = df[col].null_count()
            null_pct = (null_count / len(df) * 100) if len(df) > 0 else 0
            col_info.append(
                {
                    "Column": col,
                    "Type": dtype,
                    "Nulls": f"{null_count} ({null_pct:.1f}%)",
                }
            )

        st.dataframe(
            pl.DataFrame(col_info),
            width="stretch",
            hide_index=True,
        )
