# Technical Learnings

Patterns and solutions discovered during development. Reference this document to avoid repeating mistakes.

---

## Streamlit-Folium Map Flashing

**Problem**: Maps flash/re-render on every interaction (zoom, pan, click), causing poor UX.

**Root Cause**: By default, `st_folium()` returns all interaction data (zoom level, center, bounds, click events), which triggers Streamlit reruns.

**Solution**: Use `returned_objects=[]` to make the map display-only:

```python
from streamlit_folium import st_folium

# BAD - causes flashing on every interaction
st_folium(m, width=700, height=600)

# GOOD - display-only, no flashing
st_folium(m, width=700, height=600, returned_objects=[])

# SELECTIVE - only capture specific interactions
st_folium(m, width=700, height=600, returned_objects=["last_object_clicked"])
```

**When to Use Each**:
- `returned_objects=[]`: Static display maps (choropleth, bubble maps)
- `returned_objects=["last_object_clicked"]`: Click-to-select functionality
- Default (no parameter): Full interactivity needed (rare)

---

## Polars Excel Export with xlsxwriter

**Problem**: Using pandas for Excel export is inelegant and adds unnecessary dependency.

**Solution**: Use Polars native `write_excel()` with xlsxwriter backend:

```python
from io import BytesIO
import polars as pl
import xlsxwriter

def export_to_excel(dfs: dict[str, pl.DataFrame]) -> bytes:
    """Export DataFrames to Excel with multiple sheets."""
    buffer = BytesIO()

    # Create workbook in memory
    workbook = xlsxwriter.Workbook(buffer, {"in_memory": True})

    try:
        for sheet_name, df in dfs.items():
            # Pure Polars - no pandas conversion needed
            df.write_excel(
                workbook=workbook,
                worksheet=sheet_name,
                autofit=True,  # Auto-size columns
            )
    finally:
        workbook.close()

    buffer.seek(0)
    return buffer.getvalue()
```

**Dependency**: Add xlsxwriter via `uv add xlsxwriter`

**Benefits**:
- No pandas conversion overhead
- Automatic column width fitting with `autofit=True`
- Multiple sheets via shared workbook
- Full control over Excel formatting

---

## Polars JSON Export (Modern API)

**Problem**: `row_oriented` parameter deprecated in Polars 1.x.

**Old (Deprecated)**:
```python
# This no longer works in Polars 1.x
df.write_json(row_oriented=True)
```

**Solution**: Use `to_dicts()` or `to_dict()`:

```python
import json
import polars as pl

def export_to_json(df: pl.DataFrame, orient: str = "records", pretty: bool = False) -> bytes:
    """Export DataFrame to JSON with modern Polars API."""

    if orient == "records":
        # List of row dictionaries: [{"col1": val, "col2": val}, ...]
        data = df.to_dicts()
    elif orient == "columns":
        # Column-oriented: {"col1": [vals], "col2": [vals]}
        data = df.to_dict()
    else:
        raise ValueError(f"Invalid orient '{orient}'. Must be 'records' or 'columns'")

    indent = 2 if pretty else None
    json_str = json.dumps(data, indent=indent, ensure_ascii=False)
    return json_str.encode("utf-8")
```

---

## Numeric Display Formatting (1 Decimal Place)

**Problem**: Inconsistent decimal places across dashboard elements.

**Solution**: Apply consistent formatting at display time:

### Streamlit Metrics
```python
# Format floats with 1 decimal place
st.metric(label="Total Emissions", value=f"{total:,.1f} kt CO2e")
st.metric(label="Per Capita", value=f"{per_capita:,.1f} t/person")
st.metric(label="Change", value=f"{pct_change:+.1f}%")  # +/- sign
```

### Polars DataFrames for Display
```python
# Round numeric columns before displaying
display_df = df.select([
    pl.col("name").alias("Name"),
    pl.col("total").round(1).alias("Total (kt CO2e)"),
    pl.col("per_capita").round(1).alias("Per Capita (t/person)"),
    pl.col("density").round(1).alias("Density (t/km²)"),
])

st.dataframe(display_df, width="stretch", hide_index=True)
```

**Note**: Round at display time, not during calculations, to preserve precision.

---

## Streamlit Modern Width Syntax

**Problem**: `use_container_width=True` is deprecated.

**Solution**: Use `width` parameter:

```python
# OLD (deprecated)
st.dataframe(df, use_container_width=True)
st.plotly_chart(fig, use_container_width=True)

# NEW
st.dataframe(df, width="stretch")
st.plotly_chart(fig, width="stretch")
```

---

## Column Name Standardization

**Problem**: Database column names may differ from expected names in code.

**Solution**: Rename immediately after loading:

```python
# Load data from database
df = load_emissions_data(...)

# Rename to standard internal names
df = df.rename({
    "local_authority_code": "la_code",
    "local_authority": "la_name",
    "territorial_emissions_kt_co2e": "total_emissions",
})

# Now use standard names throughout the page
agg_df = df.group_by(["la_code", "la_name"]).agg(...)
```

**Benefits**:
- Single point of adaptation for schema changes
- Consistent naming in visualization and export code
- Easier maintenance when database schema evolves

---

## Local Authority Name Variations

**Problem**: LA names vary between data sources (e.g., "Bristol" vs "Bristol, City of").

**Solution**: Use flexible matching for defaults:

```python
# Check multiple name variations
default_las = []
for name in ["Bristol, City of", "Bristol", "Bath and North East Somerset"]:
    if name in available_las:
        default_las.append(name)

# Fallback if no matches
if not default_las:
    default_las = available_las[:4]
```

**For WECA Dashboard**: Always include:
- Bath and North East Somerset
- Bristol (or "Bristol, City of")
- South Gloucestershire
- North Somerset (candidate authority)

---

## Export Menu Component Usage

**Correct Function Signature**:
```python
from src.components.exports import create_export_menu

create_export_menu(
    df=display_df,
    base_filename=f"geographic_emissions_{year}",  # NOT filename_prefix
    formats=["csv", "parquet", "json", "excel"],
    key_prefix="geo_export",  # NOT key
)
```

---

*Last Updated: 2025-11-21*
