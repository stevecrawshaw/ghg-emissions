# GHG Emissions Dashboard

An interactive web-based dashboard for analyzing and visualizing greenhouse gas (GHG) emissions and environmental data for the West of England Combined Authority (WECA) and constituent local authorities.

## Features

- **Emissions Analysis**: Time series trends, sector breakdowns, and local authority comparisons for territorial GHG emissions (2014-2023)
- **Geographic Visualization**: Interactive choropleth and bubble maps showing emissions at LA and Combined Authority levels
- **EPC Analysis**: Domestic Energy Performance Certificate data including energy ratings, property types, and improvement potential
- **Benchmarking**: Compare WECA against other UK Combined Authorities and national averages
- **Data Export**: Download data in CSV, Parquet, JSON, and Excel formats

## Target Audience

- Energy planning professionals
- Local government environment officers
- Data analysts
- Citizens (public access)

## Technology Stack

- **Framework**: [Streamlit](https://streamlit.io/) - Python web application framework
- **Charts**: [Plotly](https://plotly.com/python/) - Interactive visualizations with zoom, pan, and hover
- **Maps**: [Folium](https://python-visualization.github.io/folium/) - Leaflet-based choropleth and point maps
- **Database**: [MotherDuck](https://motherduck.com/) - Cloud DuckDB for data storage
- **Data Processing**: [Polars](https://pola.rs/) - Fast DataFrame operations

## Geographic Scope

**Primary Focus - West of England Combined Authority**:

- Bath and North East Somerset
- Bristol
- South Gloucestershire
- North Somerset (included for regional context)

**Comparisons**:

- Other UK Combined Authorities (Greater Manchester, West Midlands, etc.)
- England national averages

## Installation

### Prerequisites

- Python 3.13+
- [uv](https://docs.astral.sh/uv/) package manager

### Setup

```bash
# Clone the repository
git clone https://github.com/stevecrawshaw/ghg-emissions.git
cd ghg-emissions

# Install dependencies
uv sync

# Create environment file
cp .env.example .env
# Edit .env and add your MOTHERDUCK_TOKEN

# Run the application
uv run streamlit run app.py
```

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=src
```

## Project Structure

```
ghg-emissions/
├── app.py                    # Main Streamlit application entry point
├── pages/                    # Multi-page dashboard
│   ├── 1_📊_Emissions_Overview.py
│   ├── 2_🗺️_Geographic_Analysis.py
│   ├── 3_🏘️_EPC_Analysis.py
│   └── 4_💡_Insights.py
├── src/
│   ├── data/                 # Data access and processing
│   │   ├── connections.py    # MotherDuck connection management
│   │   ├── loaders.py        # Data loading with caching
│   │   ├── transforms.py     # Data transformations
│   │   └── validators.py     # Data quality validation
│   ├── visualization/        # Chart and map components
│   │   ├── charts.py         # Plotly chart functions
│   │   ├── maps.py           # Folium map functions
│   │   └── themes.py         # WECA branding and theming
│   └── components/           # Reusable UI components
│       ├── filters.py        # Filter widgets
│       └── exports.py        # Data export utilities
├── tests/                    # Test suite (105+ unit tests)
├── schema/                   # Database schema documentation
└── .streamlit/               # Streamlit configuration
```

## Data Sources

- **Emissions Data**: [UK Government sub-national GHG emissions statistics](https://www.gov.uk/government/statistics/uk-local-authority-and-regional-greenhouse-gas-emissions-statistics-2005-to-2023)
- **EPC Data**: [Energy Performance Certificate register (domestic properties)](https://epc.opendatacommunities.org/)
- **Geographic Data**: [ONS boundary data for LSOAs, MSOAs, LAs, and Combined Authorities](https://geoportal.statistics.gov.uk/)
- **Socio-economic Data**: [Index of Multiple Deprivation, housing tenure](https://www.nomisweb.co.uk/)

All data is accessed via read-only connection to MotherDuck cloud database.

## Configuration

### Environment Variables

| Variable | Description |
|----------|-------------|
| `MOTHERDUCK_TOKEN` | Authentication token for MotherDuck database |

### Streamlit Configuration

Theming and settings are in `.streamlit/config.toml` using WECA brand colors.

## Development

### Code Quality

```bash
# Format code
uv run ruff format .

# Lint and auto-fix
uv run ruff check --fix .
```

### Adding Dependencies

Always use `uv` for dependency management:

```bash
uv add package-name           # Production dependency
uv add package-name --group dev  # Development dependency
```

## Accessibility

The dashboard is designed to meet WCAG 2.1 Level AA guidelines:

- Color contrast ratios meet minimum requirements
- Interactive elements are keyboard accessible
- Charts include descriptive captions

## License

This project is licensed under the GNU Affero General Public License v3.0 (AGPL-3.0).

See [LICENSE](LICENSE) for details.

## Acknowledgments

- West of England Combined Authority for brand guidelines and data access
- UK Government for open emissions and EPC data
- [Streamlit](https://streamlit.io/) for the dashboard framework
