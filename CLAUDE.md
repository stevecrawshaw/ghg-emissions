# GHG Emissions Dashboard - AI Agent Guide

## Project Overview

An interactive web-based dashboard for analyzing and visualizing greenhouse gas (GHG) emissions and environmental data for the West of England Combined Authority (WECA) and constituent local authorities.

**Current Stage**: Exploratory/prototyping → Production migration
**Primary Maintainer**: Single data analyst (intermediate Python skills)
**Target Audience**: Energy planners, local government officers, data analysts, citizens
**License**: GNU AGPL v3

### Key Features
- Sub-national emissions analysis (Local Authority & Combined Authority level)
- Multi-level geographic visualization (LSOA, MSOA, LA, CA)
- Energy Performance Certificate (EPC) data analysis (domestic & non-domestic)
- Deprivation and tenure data integration
- Time series analysis (most recent 10 years)
- Open data download capabilities
- WCAG accessibility compliance

## Technology Stack

### Core Technologies
- **Python**: 3.13+ (see `.python-version`)
- **Package Manager**: `uv` (strict requirement - NEVER edit pyproject.toml directly)
- **Linter/Formatter**: `ruff` (see `ruff.toml`)
- **Database**: MotherDuck (cloud DuckDB) - read-only access
- **Hosting**: Streamlit Cloud

### Recommended Dashboard Stack

After evaluating options for Python-based, easy-to-maintain, performant dashboards:

#### Primary Framework: **Streamlit**
**Rationale**:
- Native Streamlit Cloud hosting (free/cheap)
- Minimal boilerplate, rapid development
- Excellent Python data ecosystem integration
- Single developer friendly
- Built-in responsive layouts
- Easy to test and iterate

**Alternatives Considered**:
- Plotly Dash: More complex, better for large teams
- Panel: More flexible but steeper learning curve
- Gradio: Too limited for this use case

#### Visualization Libraries

**For Charts**: **Plotly**
- Highly interactive (zoom, pan, hover, filter)
- Comprehensive chart types (time series, bar, scatter, heatmaps)
- Excellent Streamlit integration
- Good performance with large datasets
- Built-in export capabilities

**For Maps**: **Folium** (primary) or **Pydeck** (advanced use cases)
- Folium: Leaflet-based, easy GeoJSON support, good for choropleth maps
- Pydeck: More performant for large point datasets, 3D capabilities
- Both integrate well with Streamlit

**Alternative/Supplementary**: **Altair**
- Declarative syntax (good for quick exploratory viz)
- Vega-Lite based (good browser performance)
- Use for simpler statistical plots

### Web App vs API Strategy

**Recommendation: Start Web App Only**

**Phase 1 (Current)**: Pure Streamlit web application
- Simpler architecture
- Faster development
- Meets stated requirements
- User interaction is primary goal

**Phase 2 (Future - If Needed)**: Add API Endpoints
- Use FastAPI alongside Streamlit
- Expose data endpoints for external integrations
- Enable programmatic access for power users
- Allow other services to consume the data

**Benefits of API (when needed)**:
- External system integrations
- Automated data pulls by partners
- Mobile app development
- Third-party visualizations

**Current Assessment**: Not needed initially. Focus on dashboard UX first.

## Project Structure

```
ghg-emissions/
├── .claude/
│   └── settings.json          # SessionStart hook for tool installation
├── agent-docs/                # AI agent instructions and memory
│   ├── cli-tools-memory.md
│   ├── python-code-guidelines.md
│   └── responses-to-claude-init-questions.md
├── data/                      # Local data files (gitignored except .gitkeep)
├── schema/                    # Database schemas
│   ├── schema.sql            # DuckDB schema
│   └── enriched-schema.xml   # Annotated schema
├── scripts/                   # Utility scripts
│   └── install_pkgs.sh       # CLI tools installation
├── src/                       # Application source code (to be created)
│   ├── data/                 # Data access and processing
│   │   ├── __init__.py
│   │   ├── connections.py    # MotherDuck connection management
│   │   ├── loaders.py        # Data loading utilities
│   │   └── transforms.py     # Data transformation pipelines
│   ├── visualization/         # Chart and map components
│   │   ├── __init__.py
│   │   ├── charts.py         # Plotly chart functions
│   │   ├── maps.py           # Folium/Pydeck map functions
│   │   └── themes.py         # WECA branding/theming
│   ├── pages/                # Streamlit pages (multi-page app)
│   │   ├── 1_🏠_Home.py
│   │   ├── 2_📊_Emissions.py
│   │   ├── 3_🏘️_EPC.py
│   │   └── 4_🗺️_Geography.py
│   ├── components/           # Reusable UI components
│   │   ├── __init__.py
│   │   ├── filters.py       # Filter widgets
│   │   └── exports.py       # Data export utilities
│   └── utils/               # General utilities
│       ├── __init__.py
│       ├── config.py        # Configuration management
│       └── validators.py    # Data validation
├── tests/                    # Test suite
│   ├── unit/
│   ├── integration/
│   └── conftest.py          # Pytest fixtures
├── docs/                     # User-facing documentation (minimal)
├── app.py                    # Main Streamlit application entry point
├── .env.example             # Environment variables template
├── .gitignore
├── .python-version          # Python 3.13
├── pyproject.toml           # Project dependencies (managed by uv)
├── uv.lock                  # Lock file (gitignored but tracked)
├── ruff.toml                # Linting configuration
├── weca-brand.json          # WECA visual identity guidelines
├── README.md                # Public project README
└── CLAUDE.md                # This file
```

## Development Workflow

### Code Development Style

**Interactive Python Scripts** (not Jupyter notebooks):
- Use `.py` files with IPython code fences: `# %%`
- Execute interactively with VS Code's Python Interactive window
- Benefits: Version control friendly, modular, testable

**Reusable Modules First**:
- Write functions and classes in `src/`
- Import and test in interactive scripts
- Keep business logic separate from exploratory analysis

### Data Processing Philosophy

**Preference Order**:
1. **DuckDB Relational API** (Python): Most performant with MotherDuck
2. **DuckDB SQL API**: For complex queries, use `conn.sql("SELECT ...")`
3. **Polars**: Only when operation can't be done efficiently in DuckDB

**Rationale**: MotherDuck's cloud DuckDB is highly optimized; push computation to the database.

### Dependency Management

**CRITICAL**: Always use `uv` for dependencies:

```bash
# Add production dependency
uv add package-name

# Add development dependency
uv add package-name --group dev

# Sync environment after changes
uv sync
```

**NEVER**:
- Manually edit `pyproject.toml`
- Use `pip install` directly
- Forget to commit `uv.lock` changes

### Code Quality Standards

Follow `agent-docs/python-code-guidelines.md` strictly:

#### Modern Python Syntax (3.10+)
```python
# Type hints (mandatory)
def process_emissions(year: int, authority: str) -> dict[str, float]:
    """Process emissions data for a specific year and authority.

    Args:
        year: Calendar year for emissions data
        authority: Local authority code (e.g., 'E06000023')

    Returns:
        Dictionary mapping sector names to emission values in kt CO2e
    """
    pass

# Use | for unions (not Optional)
def get_data(conn: duckdb.DuckDBPyConnection | None = None) -> list[dict]:
    pass

# Use built-in generics
sectors: list[str] = ["transport", "domestic", "industry"]
lookup: dict[str, int] = {"Bath": 2005, "Bristol": 2001}

# Pathlib for file paths
from pathlib import Path
data_dir = Path(__file__).parent / "data"
schema_file = data_dir / "schema.sql"
```

#### Google-Style Docstrings
```python
def calculate_per_capita_emissions(
    total_emissions: float,
    population: int
) -> float:
    """Calculate per capita emissions for a geographic area.

    Args:
        total_emissions: Total emissions in kt CO2e
        population: Population count (mid-year estimate)

    Returns:
        Per capita emissions in t CO2e per person

    Raises:
        ValueError: If population is zero or negative
    """
    if population <= 0:
        raise ValueError("Population must be positive")
    return (total_emissions * 1000) / population
```

#### Ruff Compliance
- Line length: 88 characters
- Selected rules: E, W, F, UP, S, B, SIM, I
- Auto-fix enabled: Run `ruff check --fix .`
- Format: Run `ruff format .`

#### Error Handling
```python
# Catch specific exceptions
try:
    conn = duckdb.connect("md:?motherduck_token={token}")
except duckdb.ConnectionException as e:
    logger.error(f"Failed to connect to MotherDuck: {e}")
    raise

# Use context managers for resources
with Path("data.csv").open() as f:
    data = f.read()
```

## Data Access & MotherDuck

### Connection Management

**Credentials**: Environment variables only
```bash
# .env file (never commit)
MOTHERDUCK_TOKEN=your_token_here
```

```python
import os
import duckdb

def get_connection() -> duckdb.DuckDBPyConnection:
    """Get MotherDuck connection using environment token.

    Connects to the 'mca_data' database on MotherDuck which contains
    all GHG emissions, EPC, geographic, and socio-economic data.
    """
    token = os.getenv("MOTHERDUCK_TOKEN")
    if not token:
        raise ValueError("MOTHERDUCK_TOKEN not set")
    return duckdb.connect(f"md:?motherduck_token={token}")
```

**Database**: `mca_data` on MotherDuck
- Contains all tables described in `schema/schema.sql`
- See `schema/enriched-schema.xml` for detailed table/column descriptions

**Access Pattern**: Read-only
- No writes to MotherDuck
- Local caching for development (optional)
- Use Streamlit's `@st.cache_data` for query results

### Schema Updates

**Schema Changes**: EPC and other schemas can change
- Store schema in `schema/` directory
- Version schema files: `schema_v1.sql`, `schema_v2.sql`
- Include schema validation in tests
- Document schema changes in git commits

### Schema Introspection

**Enriched Schema Documentation**: `schema/enriched-schema.xml`
- Contains `<description>` tags for all tables and columns in the `mca_data` database
- Use this file to understand table purposes and column meanings
- More detailed than the raw SQL schema
- Helpful for data exploration and query planning

**Example Usage**:
```python
from pathlib import Path
import xml.etree.ElementTree as ET

# Parse enriched schema for documentation
schema_path = Path("schema/enriched-schema.xml")
tree = ET.parse(schema_path)
root = tree.getroot()

# Extract table descriptions programmatically
for table in root.findall(".//table"):
    name = table.get("name")
    desc = table.find("description")
    if desc is not None:
        print(f"{name}: {desc.text}")
```

### Data Tables Overview

**Key Tables** (from `schema/schema.sql`):

**Emissions**:
- `ghg_emissions_tbl`: **Primary emissions dataset** - most comprehensive GHG data
  - Contains detailed greenhouse gas emissions by sector and sub-sector
  - Territorial emissions and emissions within scope of LA influence
  - This is the source dataset - use this for new analysis
- `emissions_tbl`: LA-level emissions by sector (2005-2023)
  - Derived from `ghg_emissions_tbl`, reshaped and aggregated
  - Useful for sector-based analysis at LA level
- `ca_emissions_evidence_long_tbl`: CA-level long format
  - Derived and augmented from primary emissions data
  - Optimized for Combined Authority comparisons and time series

**Note**: When starting new emissions analysis, prefer `ghg_emissions_tbl` as the source of truth

**Energy Performance Certificates**:
- `epc_domestic_tbl`: Domestic properties (~80+ columns)
- `epc_nondom_tbl`: Non-domestic properties
- `epc_domestic_vw`, `epc_domestic_ods_vw`: Enriched views

**Geography**:
- `postcodes_tbl`: Full UK postcode lookup
- `lsoa_poly_2011_tbl`, `lsoa_poly_2021_tbl`: LSOA boundaries (with geometry)
- `ca_boundaries_bgc_tbl`: Combined authority boundaries
- `ca_la_tbl`: CA to LA lookup

**Socio-economic**:
- `imd_lsoa_tbl`: Index of Multiple Deprivation
- `tenure_tbl`: Housing tenure by LSOA

**Views**: Use `*_ods_vw` views for Opendatasoft-ready formats

## Testing Strategy

**Comprehensive Testing**: Unit, integration, and data validation

### Test Structure
```
tests/
├── unit/
│   ├── test_connections.py
│   ├── test_transforms.py
│   └── test_charts.py
├── integration/
│   ├── test_data_pipelines.py
│   └── test_dashboard_pages.py
├── fixtures/
│   └── sample_data.parquet
└── conftest.py
```

### Testing Data Pipelines

**Required Tests**:
1. **Schema Validation**: Ensure query results match expected schema
2. **Data Quality**: Check for nulls, outliers, date ranges
3. **Transformation Logic**: Unit test calculations (e.g., per capita emissions)
4. **Integration**: Test full pipeline from MotherDuck to visualization

**Example**:
```python
# tests/unit/test_transforms.py
import pytest
from src.data.transforms import calculate_per_capita_emissions

def test_per_capita_emissions():
    """Test per capita emission calculation."""
    result = calculate_per_capita_emissions(
        total_emissions=1000.0,  # kt CO2e
        population=500_000
    )
    assert result == pytest.approx(2.0, rel=0.01)  # 2 t CO2e per person

def test_per_capita_emissions_invalid():
    """Test error handling for invalid population."""
    with pytest.raises(ValueError):
        calculate_per_capita_emissions(1000.0, 0)
```

### Running Tests
```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=src --cov-report=html

# Run specific test file
uv run pytest tests/unit/test_transforms.py

# Run with verbose output
uv run pytest -v
```

## Visual Identity & Branding

**Source**: `weca-brand.json` - WECA Brand Guidelines

### Color Palette

**Primary Colors**:
- West Green: `#40A832` (primary brand color)
- Forest Green: `#1D4F2B` (dark accent)
- Rich Purple: `#590075`
- Claret: `#CE132D`
- Black: `#1F1F1F`

**Secondary Colors**:
- Soft Green: `#8FCC87` (charts)
- Soft Purple: `#9C66AB` (charts)
- Soft Claret: `#ED8073` (charts)
- Warm Grey: `#A6A6A5`
- Grey: `#3C3C3C`
- White: `#FFFFFF`

### Typography

**Brand Fonts** (preferred):
- Headlines: Avenir Black
- Introduction: Avenir Medium
- Subheadings: Open Sans Bold
- Body: Open Sans Regular

**System Fonts** (fallback):
- Headlines: Trebuchet MS Bold
- Body: Trebuchet MS Regular

### Streamlit Theming

Create `.streamlit/config.toml`:
```toml
[theme]
primaryColor = "#40A832"      # West Green
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F0F2F6"
textColor = "#1F1F1F"         # WECA Black
font = "sans serif"           # Use Open Sans via @font-face if possible

[server]
enableCORS = false
enableXsrfProtection = true
maxUploadSize = 200
```

### Chart Styling
```python
# src/visualization/themes.py
WECA_COLORS = {
    "primary": ["#40A832", "#1D4F2B", "#590075", "#CE132D"],
    "secondary": ["#8FCC87", "#9C66AB", "#ED8073"],
    "sequential": ["#F0F2F6", "#8FCC87", "#40A832", "#1D4F2B"],
}

def get_plotly_template() -> dict:
    """Get Plotly template with WECA branding."""
    return {
        "layout": {
            "colorway": WECA_COLORS["primary"],
            "font": {"family": "Open Sans, sans-serif", "color": "#1F1F1F"},
            "paper_bgcolor": "#FFFFFF",
            "plot_bgcolor": "#F0F2F6",
        }
    }
```

## Geographic Scope

**Primary Focus**:
- **West of England Combined Authority (WECA)**:
  - Bath and North East Somerset
  - Bristol
  - South Gloucestershire
- **North Somerset** (not yet WECA member, but included)

**Comparison Geographies**:
- Other UK Combined Authorities (headline indicators)
- Regional benchmarks (South West England)
- National benchmarks (England)

**Geographic Levels**:
- **LSOA** (Lower Super Output Area): Smallest unit (~1,500 people)
- **MSOA** (Middle Super Output Area): ~7,500 people
- **LA** (Local Authority): District/Unitary authority
- **CA** (Combined Authority): WECA

**Time Coverage**: Most recent 10 years (currently 2014-2023)
- Note: Emissions data has ~18-month lag (2023 data released July 2025)

## Performance Requirements

**Critical Thresholds**:
- Initial page load: < 3 seconds
- Chart interactions: < 500ms
- Map rendering: < 2 seconds
- Data export: < 10 seconds (up to 100k rows)

**Optimization Strategies**:
1. **Query Optimization**: Push filters to MotherDuck (don't fetch then filter)
2. **Caching**: Use `@st.cache_data` for expensive queries
3. **Aggregation**: Pre-aggregate where possible (use database views)
4. **Lazy Loading**: Load map data on demand, not on page load
5. **Pagination**: For large tables, use pagination (25-100 rows per page)

**Monitoring**:
```python
import streamlit as st
import time

@st.cache_data(ttl=3600)
def load_emissions_data(year: int) -> pl.DataFrame:
    """Load emissions data with performance monitoring."""
    start = time.time()
    data = conn.sql("SELECT * FROM emissions_tbl WHERE calendar_year = ?", [year])
    elapsed = time.time() - start

    if elapsed > 2.0:
        st.warning(f"Slow query: {elapsed:.2f}s")

    return data.pl()
```

## Accessibility (WCAG Compliance)

**Target**: WCAG 2.1 Level AA where possible

**Key Requirements**:
1. **Color Contrast**: 4.5:1 for text, 3:1 for large text/UI components
2. **Keyboard Navigation**: All interactive elements accessible via keyboard
3. **Screen Reader Support**: Proper ARIA labels, alt text
4. **Focus Indicators**: Clear visual focus states
5. **Semantic HTML**: Proper heading hierarchy

**Streamlit-Specific**:
```python
# Use descriptive labels
st.selectbox("Select Local Authority", options=authorities, key="la_select")

# Add alt text to images
st.image("chart.png", caption="Emissions by sector 2023")

# Use markdown for semantic headings
st.markdown("## Time Series Analysis")  # H2
st.markdown("### By Sector")             # H3

# Provide text alternatives for charts
st.plotly_chart(fig, use_container_width=True)
st.caption("Chart shows emissions declining from 2005 to 2023...")
```

**Testing**: Use browser dev tools Lighthouse audits

## Development Tools

### CLI Tools (Installed via SessionStart Hook)

**Available Tools** (see `agent-docs/cli-tools-memory.md`):
- `rg` (ripgrep): Fast pattern search
- `fdfind` (fd-find): Fast file finder
- `batcat` (bat): Syntax-highlighted file preview
- `tree`: Directory structure visualization
- `jq`: JSON parsing
- `sed`: Text transformation

**Usage Examples**:
```bash
# Find all TODO comments
rg "TODO|FIXME" --glob '*.py'

# Find all Streamlit page files
fdfind "*.py" src/pages/

# Preview with syntax highlighting
batcat -n src/data/connections.py

# View project structure
tree src/ -L 2

# Parse JSON config
jq '.colors.primary_colors' weca-brand.json
```

### Recommended VS Code Extensions

See `.vscode/extensions.json`:
- `ms-python.python`: Python support
- `ms-python.vscode-pylance`: Type checking
- `ms-toolsai.jupyter`: Interactive Python
- `tamasfe.even-better-toml`: TOML support
- `aaron-bond.better-comments`: Enhanced comments
- `christian-kohler.path-intellisense`: Path autocomplete

## Common Tasks

### Starting Development

```bash
# Clone repository
git clone <repo-url>
cd ghg-emissions

# Install dependencies
uv sync

# Set up environment
cp .env.example .env
# Edit .env with MOTHERDUCK_TOKEN

# Run tests
uv run pytest

# Start Streamlit app
uv run streamlit run app.py
```

### Adding a New Dashboard Page

```bash
# Create page file (numbered for order)
touch src/pages/5_📈_New_Page.py
```

```python
# src/pages/5_📈_New_Page.py
import streamlit as st
from src.data.connections import get_connection
from src.visualization.charts import create_time_series

st.set_page_config(page_title="New Page", page_icon="📈")

st.title("New Analysis Page")

# Load data
conn = get_connection()
data = conn.sql("SELECT * FROM ...").pl()

# Create visualization
fig = create_time_series(data, x="year", y="emissions")
st.plotly_chart(fig, use_container_width=True)
```

### Adding a New Dependency

```bash
# Production dependency
uv add streamlit-folium

# Development dependency
uv add pytest-mock --group dev

# Sync environment
uv sync
```

### Running Code Quality Checks

```bash
# Format code
uv run ruff format .

# Lint and auto-fix
uv run ruff check --fix .

# Type checking (if using mypy)
uv run mypy src/

# Run all checks before commit
uv run ruff format . && uv run ruff check --fix . && uv run pytest
```

### Creating a Data Schema Documentation

```bash
# Generate schema documentation from database
uv run python scripts/generate_schema_docs.py

# This should create docs/data_dictionary.md
```

### Deploying to Streamlit Cloud

1. Push to GitHub
2. Connect repository in Streamlit Cloud dashboard
3. Set environment secrets: `MOTHERDUCK_TOKEN`
4. Deploy from `app.py`

## AI Agent Instructions

### When to Consult This File

**Always consult CLAUDE.md for**:
- Project architecture decisions
- Technology choices
- Code style questions
- Data access patterns
- Testing strategies
- Brand/styling guidelines

### Project Context Awareness

**Understand**:
- This is a single-developer project (intermediate Python skills)
- Performance matters (3s load time target)
- Accessibility is required (WCAG AA)
- Data schema can change (defensive programming)
- Focus on WECA region (but support comparisons)

### Code Generation Guidelines

**When writing code**:
1. Always follow `agent-docs/python-code-guidelines.md`
2. Use type hints comprehensively
3. Write Google-style docstrings
4. Include error handling
5. Add tests for new functionality
6. Use DuckDB for data operations (not Pandas/Polars unless necessary)
7. Apply WECA branding (colors, fonts)
8. Consider accessibility (ARIA labels, contrast)

**When suggesting dependencies**:
1. Prefer lightweight libraries
2. Check if functionality exists in current stack
3. Provide `uv add` command (never edit pyproject.toml)
4. Explain rationale for new dependency

**When refactoring**:
1. Ensure backward compatibility
2. Update tests
3. Update docstrings
4. Check performance impact
5. Maintain code style consistency

### Research Tasks

If asked to research:
- Dashboard frameworks → Recommend Streamlit + Plotly (as documented)
- Map libraries → Recommend Folium (primary) or Pydeck (advanced)
- Data processing → Recommend DuckDB relational API
- Hosting → Recommend Streamlit Cloud (already decided)

### Prohibited Actions

**Never**:
- Manually edit `pyproject.toml` (use `uv add`)
- Commit secrets or tokens
- Use `pip install` directly (use `uv`)
- Write code without type hints
- Skip tests for new features
- Ignore WECA branding
- Assume write access to MotherDuck
- Generate dummy data for production code

## Questions & Clarifications

For questions not covered in this document, consult:
1. `agent-docs/responses-to-claude-init-questions.md` - Original Q&A
2. `agent-docs/python-code-guidelines.md` - Code standards
3. `README.md` - Public-facing project description
4. Ask the maintainer directly

---

**Document Version**: 1.0
**Last Updated**: 2025-11-21
**Maintained By**: Project maintainer + AI agents
