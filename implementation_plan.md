# GHG Emissions Dashboard - Implementation Plan

**Project**: West of England Combined Authority GHG Emissions Dashboard
**Stage**: Exploratory/Prototyping → Production
**Last Updated**: 2025-11-22
**Status**: 🟢 Phase 4.5 Complete → Phase 5 Ready to Start

---

## Progress Overview

```
Phase 1: Foundation & Setup          [████████████████████████] 100% ✅
Phase 2: Data Layer                  [████████████████████████] 100% ✅
Phase 3: Visualization Components    [████████████████████████] 100% ✅
Phase 4: Dashboard Pages             [████████████████████████] 100% ✅
Phase 5: Testing & Quality           [────────────────────────]  0% ⏳
Phase 6: Deployment Preparation      [────────────────────────]  0% ⏳
```

**Overall Progress**: 75% (Phases 1-4 complete)

---

## Phase 1: Foundation & Setup ✅ 100% COMPLETE

**Goal**: Establish project structure, documentation, and development environment

### All Tasks Completed ✅

- [x] Create project repository structure
- [x] Set up Python 3.13 environment with `uv`
- [x] Configure `ruff` for linting/formatting
- [x] Install CLI tools (rg, fdfind, batcat, tree, jq, sed)
- [x] Create comprehensive CLAUDE.md guide
- [x] Document WECA brand guidelines (weca-brand.json)
- [x] Document database schema (schema.sql, enriched-schema.xml)
- [x] Answer initialization questions
- [x] Document Python code guidelines
- [x] Configure VS Code extensions
- [x] Create `src/` directory structure
  - [x] `src/data/` (connections, loaders, transforms)
  - [x] `src/visualization/` (charts, maps, themes)
  - [x] `src/pages/` (Streamlit pages)
  - [x] `src/components/` (UI components)
  - [x] `src/utils/` (config, validators)
- [x] Create `.env.example` template with MOTHERDUCK_TOKEN
- [x] Create `.streamlit/config.toml` with WECA branding
- [x] Set up `tests/` directory structure (unit, integration, data, fixtures)
- [x] Create `tests/conftest.py` with pytest fixtures
- [x] Create `app.py` main entry point with home page

**Phase 1 Complete**: All foundation and setup tasks finished. Ready for Phase 2.

---

## Phase 2: Data Layer ✅ 100% COMPLETE

**Goal**: Implement MotherDuck connection and data access patterns

### Tasks

#### 2.1: Database Connection ✅ COMPLETE
- [x] Create `src/data/connections.py`
  - [x] Implement `get_connection()` with env token
  - [x] Add connection error handling
  - [x] Add connection testing function
  - [x] Document usage patterns
  - [x] Implement `get_table_list()` and `get_table_info()`
  - [x] Add SQL injection prevention
  - [x] Create 19 comprehensive unit tests (all passing)

#### 2.2: Data Loaders ✅ COMPLETE
- [x] Create `src/data/loaders.py`
  - [x] Implement emissions data loader (`load_emissions_data()`)
  - [x] Implement EPC data loader (`load_epc_domestic_data()`)
  - [x] Implement geography data loaders:
    - [x] `load_local_authorities()` - LA/CA mappings
    - [x] `load_postcodes()` - Postcode lookup
    - [x] `load_lsoa_boundaries()` - LSOA polygons
  - [x] Add Streamlit caching decorators (1-2 hour TTL)
  - [x] Add performance monitoring (timing, slow query warnings)
  - [x] Implement `get_data_freshness()` utility
  - [x] Create 17 comprehensive unit tests (all passing)

#### 2.3: Data Transformations ✅ COMPLETE
- [x] Create `src/data/transforms.py`
  - [x] Per capita emissions calculation
  - [x] Emissions per km² calculation
  - [x] Time series aggregations
  - [x] Geographic aggregations (LSOA→MSOA→LA→CA)
  - [x] Sector aggregations
  - [x] Custom TransformationError exception
  - [x] Comprehensive input validation
  - [x] Support for custom column names
  - [x] Create 28 comprehensive unit tests (all passing)

#### 2.4: Data Validation ✅ COMPLETE
- [x] Create `src/data/validators.py`
  - [x] Schema validation functions (validate_schema)
  - [x] Data quality checks:
    - [x] Null value checking (check_nulls)
    - [x] Outlier detection (check_outliers - IQR method)
    - [x] Date range validation (check_date_range)
  - [x] Geographic code validation:
    - [x] LA code validation (validate_la_code)
    - [x] LSOA code validation (validate_lsoa_code)
    - [x] Postcode validation (validate_postcode)
    - [x] Batch geographic code checking (check_geographic_codes)
  - [x] ValidationResult dataclass for consistent returns
  - [x] Custom ValidationError exception
  - [x] Batch validation runner (run_all_validations)
  - [x] Create 42 comprehensive unit tests (all passing)

### Dependencies
- Phase 1 complete (directory structure)
- MotherDuck token available

### Acceptance Criteria
- [x] Can connect to mca_data database
- [x] Can load all primary datasets
- [x] Data transformations tested and working
- [ ] Performance < 2s for typical queries (to be verified with integration tests)

**Phase 2 Complete**: Full data layer implementation with connections, loaders, transformations, and validators.
- 4 modules: connections.py, loaders.py, transforms.py, validators.py
- 106 unit tests passing (19 + 17 + 28 + 42)
- All code linted and formatted (ruff compliant)
- Comprehensive error handling and type hints
- Ready for Phase 3 (Visualization Components)

---

## Phase 3: Visualization Components ✅ 100% COMPLETE

**Goal**: Build reusable chart, map, and theming components

### Tasks

#### 3.1: WECA Theming ✅
- [x] Create `src/visualization/themes.py` (352 lines)
  - [x] Define WECA color palettes (primary, secondary, sequential, diverging, categorical)
  - [x] Create Plotly template with WECA branding (`get_plotly_template()`)
  - [x] Create color scale functions (sequential, diverging, categorical)
  - [x] Add WCAG color contrast checker (`check_color_contrast()`)
  - [x] Auto-register "weca" Plotly template on import

#### 3.2: Chart Components ✅
- [x] Create `src/visualization/charts.py` (745 lines)
  - [x] Time series line chart (`create_time_series()`) - supports multi-line, markers, color grouping
  - [x] Stacked area chart (`create_stacked_area()`) - for sector breakdown over time
  - [x] Bar chart comparisons (`create_bar_comparison()`, `create_grouped_bar()`) - vertical/horizontal, grouped/stacked
  - [x] Heatmap (`create_heatmap()`) - for geographic/temporal patterns
  - [x] Scatter plot (`create_scatter()`) - with trendlines, size/color encoding
  - [x] Donut chart (`create_donut_chart()`) - for proportions
  - [x] Reference line utility (`add_reference_line()`) - for targets/baselines
  - [x] All charts use WECA template by default
  - [x] Custom ChartError exception

#### 3.3: Map Components ✅
- [x] Create `src/visualization/maps.py` (677 lines)
  - [x] Base map creator (`create_base_map()`) - centered on WECA region
  - [x] Choropleth map (`create_choropleth_map()`) - emissions by LSOA/MSOA/LA
  - [x] Point map (`create_point_map()`) - EPC properties with clustering
  - [x] Heatmap (`create_heatmap()`) - density visualization
  - [x] Bubble map (`create_bubble_map()`) - sized by emission values
  - [x] Boundary layer adder (`add_boundary_layer()`) - LA/LSOA overlays
  - [x] Custom legend (`add_legend()`) - WECA colors
  - [x] Interactive tooltips with data
  - [x] Custom MapError exception

#### 3.4: UI Components ✅
- [x] Create `src/components/filters.py` (536 lines)
  - [x] Year range slider (`year_range_filter()`)
  - [x] Single year selector (`single_year_filter()`)
  - [x] LA selector (`la_selector()`) - multi or single select
  - [x] Geography level selector (`geography_level_selector()`) - LSOA/MSOA/LA/CA
  - [x] Sector filter (`sector_filter()`) - with "Select All" option
  - [x] Property type filter (`property_type_filter()`)
  - [x] Energy rating filter (`energy_rating_filter()`)
  - [x] Comparison selector (`comparison_selector()`) - for benchmarking
  - [x] Metric selector (`metric_selector()`) - choose visualization metric
  - [x] Filter summary display (`create_filter_summary()`)
  - [x] Data freshness indicator (`data_freshness_indicator()`)
  - [x] Advanced filter expander (`advanced_filter_expander()`)
  - [x] Filter reset button (`filter_reset_button()`)
- [x] Create `src/components/exports.py` (565 lines)
  - [x] CSV export (`export_to_csv()`)
  - [x] Parquet export (`export_to_parquet()`)
  - [x] JSON export (`export_to_json()`)
  - [x] Excel export (`export_to_excel()`) - multi-sheet support
  - [x] Chart HTML export (`export_chart_to_html()`)
  - [x] Chart image export (`export_chart_to_image()`) - PNG/SVG/PDF
  - [x] Map HTML export (`export_map_to_html()`)
  - [x] Download button creator (`create_download_button()`) - auto MIME detection
  - [x] Export menus (`create_export_menu()`, `create_chart_export_menu()`)
  - [x] Data summary card (`create_data_summary_card()`)
  - [x] Custom ExportError exception

### Dependencies ✅
- [x] Phase 2 complete (data layer working)
- [x] Added dependencies: `plotly` (6.5.0), `folium` (0.20.0), `streamlit-folium` (0.25.3)
- [x] Note: `streamlit` and `altair` already installed

### Acceptance Criteria ✅
- [x] All chart types render with WECA branding
- [x] Maps support GeoJSON with WECA color scales
- [x] Color contrast checker included (`check_color_contrast()`) - WCAG AA compliance
- [x] Charts are fully interactive (zoom, pan, hover)
- [x] Export functions support multiple formats

**Phase 3 Complete**: Full visualization layer implementation
- 4 modules: themes.py (352 lines), charts.py (745 lines), maps.py (677 lines), filters.py (536 lines), exports.py (565 lines)
- All code linted and formatted (ruff compliant)
- Comprehensive error handling and type hints
- Ready for Phase 4 (Dashboard Pages) and Phase 5 (Unit Tests)

---

## Phase 4: Dashboard Pages ✅ 100% COMPLETE

**Goal**: Create multi-page Streamlit application

### Tasks

#### 4.1: Main Application ✅ COMPLETE & TESTED
- [x] Create `app.py`
  - [x] Set up page config with WECA branding
  - [x] Add navigation sidebar with quick links
  - [x] Add project header with WECA gradient
  - [x] Add footer with license info
  - [x] Configure Streamlit settings (.streamlit/config.toml)
  - [x] Load environment variables with python-dotenv
  - [x] Register WECA Plotly template
  - [x] Add custom CSS for WECA styling
- [x] Create mock data fallback system (`src/data/mock_data.py`)
- [x] Test with real MotherDuck data
- [x] Fix all data integration issues:
  - [x] LA name variations (Bristol vs Bristol, City of)
  - [x] Include North Somerset alongside WECA authorities
  - [x] LA name-to-code conversion for database queries
  - [x] Column name standardization (territorial_emissions → total_emissions)
  - [x] Metric calculations (per_capita, per_km2)
  - [x] Chart parameter corrections (x_label, y_label)
  - [x] Time series sorting for correct plotting order

**Deliverables**:
- `app.py` (228 lines) - Main entry point with WECA branding
- `pages/1_📊_Emissions_Overview.py` (347 lines) - First dashboard page
- `src/data/mock_data.py` (307 lines) - Automatic fallback for MotherDuck outages
- Enhanced `.streamlit/config.toml` with WECA theme
- Added python-dotenv dependency

**Features**:
- WECA-branded home page with comprehensive navigation
- Interactive Emissions Overview page with:
  - Year range, LA (including North Somerset), sector, and metric filters
  - Time series chart by LA (properly sorted)
  - Stacked area chart by sector
  - Bar chart for LA comparison
  - Key insights metrics (total, average, % change)
  - Data export (CSV, Parquet, JSON, Excel)
- Comprehensive error handling for database connectivity
- Automatic fallback to mock data when MotherDuck unavailable
- All code passes ruff linting
- **Verified working with real MotherDuck data**

#### 4.2: Emissions Analysis Page ⏳ READY TO START
- [ ] Create additional emissions visualizations (optional enhancement)
  - [ ] Per capita vs absolute toggle
  - [ ] Multi-year comparison charts
  - [ ] Sector deep-dive analysis
  - [ ] Trend analysis with projections

#### 4.3: EPC Analysis Page ✅ COMPLETE
- [x] Create `pages/3_🏘️_EPC_Analysis.py` (565 lines)
  - [x] Current energy ratings distribution (bar chart by rating)
  - [x] Energy ratings by LA (grouped bar chart)
  - [x] Property type breakdown (donut chart)
  - [x] Tenure distribution (donut chart)
  - [x] Construction age patterns (bar chart + heatmap)
  - [x] Heating fuel analysis (bar + donut charts)
  - [x] Improvement potential analysis (current vs potential heatmap)
  - [x] CO2 savings potential by rating
  - [x] Key metrics (total properties, avg SAP, avg CO2, % rated C+)
  - [x] Filter by LA, property type, rating, tenure
  - [x] Data export (CSV, Parquet, JSON, Excel)
  - [x] Mock data fallback system for offline development

**Key Features**:
- Comprehensive EPC data visualization for domestic properties
- Mock data generator with realistic UK distributions
- Automatic fallback when MotherDuck unavailable

#### 4.4: Geographic View Page ✅ COMPLETE
- [x] Create `pages/2_🗺️_Geographic_Analysis.py` (269 lines)
  - [x] Interactive bubble map showing LA emissions
  - [x] Year selector (single year, 2019-2023)
  - [x] Sector filter with select all option
  - [x] Metric selector (total emissions, per capita, per km²)
  - [x] Summary statistics cards (total, average, min, max)
  - [x] Sortable data table with 1 decimal place formatting
  - [x] Export functionality (CSV, Parquet, JSON, Excel)
  - [x] Map performance optimized (no flashing on interaction)

**Key Fixes Applied**:
- Used `returned_objects=[]` in st_folium to prevent map flashing
- Pure Polars Excel export via xlsxwriter (no pandas conversion)
- Modern Polars JSON export via to_dicts() method
- Consistent 1 decimal place formatting throughout

#### 4.5: Insights & Comparisons Page ✅ COMPLETE
- [x] Create `pages/4_💡_Insights.py` (640 lines)
  - [x] WECA vs other Combined Authorities comparison
  - [x] WECA vs England average benchmarks
  - [x] Time series comparisons (WECA vs England, top CAs)
  - [x] Per capita and total emissions comparisons
  - [x] Rank/position indicators with conditional highlighting
  - [x] Key metrics cards (WECA value, rank, vs England, YoY change)
  - [x] Interactive bar chart with WECA highlighting
  - [x] Full rankings table with export functionality
  - [x] Mock data fallback for offline development

**Key Features**:
- Compares WECA against 10 major Combined Authorities
- Shows England average as benchmark line on charts
- Calculates and displays WECA's rank position
- Color-coded performance indicators (green for WECA, grey for others)
- Year selector (2014-2023) with per capita/total metric toggle

### Dependencies
- Phase 3 complete (visualization components)
- Streamlit installed and configured

### Acceptance Criteria
- [ ] All pages load in < 3 seconds
- [ ] Navigation between pages works smoothly
- [ ] Filters update visualizations correctly
- [ ] Data exports work correctly
- [ ] Mobile responsiveness adequate
- [ ] WCAG AA compliance verified

---

## Phase 5: Testing & Quality ⏳ 0%

**Goal**: Comprehensive test coverage and quality assurance

### Tasks

#### 5.1: Unit Tests
- [ ] Create `tests/unit/test_connections.py`
  - [ ] Test connection with valid token
  - [ ] Test connection error handling
  - [ ] Test connection string formatting
- [ ] Create `tests/unit/test_loaders.py`
  - [ ] Test each loader function
  - [ ] Test caching behavior
  - [ ] Test error handling for missing data
- [ ] Create `tests/unit/test_transforms.py`
  - [ ] Test per capita calculations
  - [ ] Test aggregation logic
  - [ ] Test edge cases (zero population, null values)
- [ ] Create `tests/unit/test_charts.py`
  - [ ] Test chart creation functions
  - [ ] Test WECA theming application
  - [ ] Test data input validation

#### 5.2: Integration Tests
- [ ] Create `tests/integration/test_data_pipeline.py`
  - [ ] Test full data load → transform → output pipeline
  - [ ] Test cross-table joins
  - [ ] Test geographic aggregations
- [ ] Create `tests/integration/test_pages.py`
  - [ ] Test page rendering (if possible)
  - [ ] Test filter interactions
  - [ ] Test data exports

#### 5.3: Data Quality Tests
- [ ] Create `tests/data/test_schema_validation.py`
  - [ ] Validate schema matches expectations
  - [ ] Check for required columns
  - [ ] Validate data types
- [ ] Create `tests/data/test_data_quality.py`
  - [ ] Check for unexpected nulls
  - [ ] Check date ranges
  - [ ] Check geographic code validity
  - [ ] Check for outliers

#### 5.4: Test Configuration
- [ ] Create `tests/conftest.py`
  - [ ] Mock MotherDuck connection fixture
  - [ ] Sample data fixtures
  - [ ] Common test utilities
- [ ] Configure pytest settings
- [ ] Set up coverage reporting (target: 80%+)

### Dependencies
- Phase 2, 3, 4 complete (code to test)
- `pytest` and `pytest-cov` installed

### Acceptance Criteria
- [ ] Unit test coverage > 80%
- [ ] All integration tests pass
- [ ] Data quality checks pass
- [ ] No critical Ruff warnings
- [ ] All type hints verified

---

## Phase 6: Deployment Preparation ⏳ 0%

**Goal**: Prepare for Streamlit Cloud deployment

### Tasks

#### 6.1: Configuration
- [ ] Create `requirements.txt` from `uv.lock`
- [ ] Verify all dependencies compatible with Streamlit Cloud
- [ ] Create deployment documentation
- [ ] Document environment variable setup

#### 6.2: Documentation
- [ ] Create minimal user guide (`docs/user_guide.md`)
  - [ ] How to use the dashboard
  - [ ] How to interpret visualizations
  - [ ] Data definitions and caveats
- [ ] Update README.md for public view
  - [ ] Project description
  - [ ] Screenshot/demo
  - [ ] Link to deployed app
  - [ ] License and attribution

#### 6.3: Performance Optimization
- [ ] Audit query performance
- [ ] Optimize caching strategies
- [ ] Reduce initial page load data
- [ ] Implement lazy loading for maps
- [ ] Add loading indicators

#### 6.4: Accessibility Audit
- [ ] Run Lighthouse accessibility audit
- [ ] Verify color contrast ratios (WCAG AA)
- [ ] Test keyboard navigation
- [ ] Add ARIA labels where needed
- [ ] Add alt text for visualizations

#### 6.5: Deployment
- [ ] Create Streamlit Cloud account/project
- [ ] Connect GitHub repository
- [ ] Configure secrets (MOTHERDUCK_TOKEN)
- [ ] Test deployment
- [ ] Monitor performance after launch

### Dependencies
- Phase 1-5 complete
- Streamlit Cloud account

### Acceptance Criteria
- [ ] App deploys successfully
- [ ] All environment variables configured
- [ ] Performance meets requirements (< 3s load)
- [ ] No console errors
- [ ] Accessibility score > 90

---

## Dependencies to Add

### Phase 2 (Data Layer)
```bash
# Already installed
# duckdb
# polars
# pyarrow
```

### Phase 3 (Visualization)
```bash
uv add streamlit
uv add plotly
uv add folium
uv add streamlit-folium
uv add altair  # optional
```

### Phase 4 (Dashboard)
```bash
# streamlit already added in Phase 3
uv add python-dotenv  # for .env file handling
```

### Phase 5 (Testing)
```bash
# pytest already in dev group
uv add pytest-mock --group dev
uv add pytest-cov --group dev
```

---

## Risk Register

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| MotherDuck schema changes break queries | High | Medium | Store schema versions, add validation tests |
| Performance issues with large EPC dataset | High | Medium | Implement aggressive caching, pagination |
| WCAG compliance issues | Medium | Low | Regular Lighthouse audits, contrast checker |
| Streamlit Cloud resource limits | Medium | Low | Monitor usage, optimize queries |
| Data lag issues (18-month emissions delay) | Low | High | Document clearly in UI, add data freshness indicator |

---

## Known Issues

| Issue | Page | Status | Notes |
|-------|------|--------|-------|
| EPC construction dates incorrect in source data | EPC Analysis | 🔴 Open | Need to resolve construction date mapping in MotherDuck source data |

---

## Notes & Decisions

### Architecture Decisions
- **Framework**: Streamlit (decided) - Best for single developer, rapid iteration
- **Charts**: Plotly (decided) - Interactive, comprehensive, good Streamlit integration
- **Maps**: Folium (decided) - Easy GeoJSON, good for choropleth maps
- **Data Processing**: DuckDB → Polars (decided) - Push computation to database
- **Hosting**: Streamlit Cloud (decided) - Free tier, easy deployment

### Key Constraints
- Single developer (intermediate Python skills)
- Free/cheap hosting required
- < 3 second page load requirement
- WCAG AA compliance required
- Read-only database access

### Success Metrics
- Dashboard loads in < 3 seconds
- All visualizations render correctly
- Data exports work for 100k+ rows
- Accessibility score > 90
- User can complete key tasks without documentation

---

## Next Actions

**Immediate (Today/This Week)**:
1. ✅ Complete Phase 1 remaining tasks (directory structure, config files)
2. Start Phase 2.1: Database connection implementation
3. Test MotherDuck connection with sample queries

**Short Term (This Month)**:
1. Complete Phase 2: Full data layer working
2. Complete Phase 3: Core visualization components
3. Start Phase 4: Build first dashboard page (Home)

**Medium Term (Next 2 Months)**:
1. Complete all dashboard pages
2. Complete testing suite
3. Internal review and iteration

**Long Term (3+ Months)**:
1. Deployment to Streamlit Cloud
2. Public beta launch
3. User feedback and iteration

---

**Status Legend**:
- ✅ Complete
- ⏳ In Progress
- 🔴 Blocked
- ⚠️ At Risk
- 📝 Planned
