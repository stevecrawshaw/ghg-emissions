# GHG Emissions Dashboard - Implementation Plan

**Project**: West of England Combined Authority GHG Emissions Dashboard
**Stage**: Exploratory/Prototyping → Production
**Last Updated**: 2025-11-21
**Status**: 🟢 Phase 1 Complete → Phase 2 In Progress

---

## Progress Overview

```
Phase 1: Foundation & Setup          [████████████████████████] 100% ✅
Phase 2: Data Layer                  [--------------------]  0% ⏳
Phase 3: Visualization Components    [--------------------]  0% ⏳
Phase 4: Dashboard Pages             [--------------------]  0% ⏳
Phase 5: Testing & Quality           [--------------------]  0% ⏳
Phase 6: Deployment Preparation      [--------------------]  0% ⏳
```

**Overall Progress**: 17% (Phase 1 complete, Phase 2 starting)

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

## Phase 2: Data Layer ⏳ 0%

**Goal**: Implement MotherDuck connection and data access patterns

### Tasks

#### 2.1: Database Connection
- [ ] Create `src/data/connections.py`
  - [ ] Implement `get_connection()` with env token
  - [ ] Add connection error handling
  - [ ] Add connection testing function
  - [ ] Document usage patterns

#### 2.2: Data Loaders
- [ ] Create `src/data/loaders.py`
  - [ ] Implement emissions data loader (`load_emissions_data()`)
  - [ ] Implement EPC data loader (`load_epc_data()`)
  - [ ] Implement geography data loader (`load_geography_data()`)
  - [ ] Add Streamlit caching decorators
  - [ ] Add performance monitoring

#### 2.3: Data Transformations
- [ ] Create `src/data/transforms.py`
  - [ ] Per capita emissions calculation
  - [ ] Emissions per km² calculation
  - [ ] Time series aggregations
  - [ ] Geographic aggregations (LSOA→MSOA→LA→CA)
  - [ ] Sector aggregations

#### 2.4: Data Validation
- [ ] Create `src/data/validators.py`
  - [ ] Schema validation functions
  - [ ] Data quality checks (nulls, outliers, date ranges)
  - [ ] Geographic code validation

### Dependencies
- Phase 1 complete (directory structure)
- MotherDuck token available

### Acceptance Criteria
- [ ] Can connect to mca_data database
- [ ] Can load all primary datasets
- [ ] Data transformations tested and working
- [ ] Performance < 2s for typical queries

---

## Phase 3: Visualization Components ⏳ 0%

**Goal**: Build reusable chart, map, and theming components

### Tasks

#### 3.1: WECA Theming
- [ ] Create `src/visualization/themes.py`
  - [ ] Define WECA color palettes
  - [ ] Create Plotly template with WECA branding
  - [ ] Create color scale functions
  - [ ] Add accessibility-compliant color combinations

#### 3.2: Chart Components
- [ ] Create `src/visualization/charts.py`
  - [ ] Time series line chart (`create_time_series()`)
  - [ ] Stacked area chart for sector breakdown
  - [ ] Bar chart for LA comparisons
  - [ ] Heatmap for geographic patterns
  - [ ] Scatter plot for correlations
  - [ ] All charts use WECA theming

#### 3.3: Map Components
- [ ] Create `src/visualization/maps.py`
  - [ ] Choropleth map for emissions by geography
  - [ ] Point map for EPC properties
  - [ ] LA boundary layer
  - [ ] LSOA boundary layer
  - [ ] Interactive tooltips with data
  - [ ] Legend with WECA colors

#### 3.4: UI Components
- [ ] Create `src/components/filters.py`
  - [ ] Year range selector
  - [ ] Geography selector (LA, LSOA)
  - [ ] Sector filter
  - [ ] Property type filter (for EPC)
- [ ] Create `src/components/exports.py`
  - [ ] CSV export function
  - [ ] Parquet export function
  - [ ] Chart image export

### Dependencies
- Phase 2 complete (data layer working)
- Add dependencies: `streamlit`, `plotly`, `folium`, `streamlit-folium`

### Acceptance Criteria
- [ ] All chart types render with WECA branding
- [ ] Maps display correctly with GeoJSON
- [ ] Color contrast meets WCAG AA (4.5:1)
- [ ] Charts are interactive (zoom, pan, hover)

---

## Phase 4: Dashboard Pages ⏳ 0%

**Goal**: Create multi-page Streamlit application

### Tasks

#### 4.1: Main Application
- [ ] Create `app.py`
  - [ ] Set up page config with WECA branding
  - [ ] Add navigation sidebar
  - [ ] Add project header/footer
  - [ ] Configure Streamlit settings

#### 4.2: Home Page
- [ ] Create `src/pages/1_🏠_Home.py`
  - [ ] Project overview and description
  - [ ] Key metrics dashboard (current year totals)
  - [ ] Quick navigation to main sections
  - [ ] Data freshness indicator
  - [ ] About WECA information

#### 4.3: Emissions Analysis Page
- [ ] Create `src/pages/2_📊_Emissions.py`
  - [ ] Time series view (10 years)
  - [ ] Sector breakdown (stacked charts)
  - [ ] LA comparison view
  - [ ] Per capita vs absolute toggle
  - [ ] Data filters (year, LA, sector)
  - [ ] Download data button

#### 4.4: EPC Analysis Page
- [ ] Create `src/pages/3_🏘️_EPC.py`
  - [ ] Current energy ratings distribution
  - [ ] Improvement potential analysis
  - [ ] Property type breakdown
  - [ ] Tenure correlation
  - [ ] Construction age patterns
  - [ ] Filter by LA, property type, rating
  - [ ] Download data button

#### 4.5: Geographic View Page
- [ ] Create `src/pages/4_🗺️_Geography.py`
  - [ ] Interactive choropleth map
  - [ ] Geographic level selector (LSOA, MSOA, LA, CA)
  - [ ] Metric selector (emissions, per capita, EPC rating)
  - [ ] Click for detailed view
  - [ ] Deprivation overlay option
  - [ ] Download map data

#### 4.6: Comparisons Page
- [ ] Create `src/pages/5_📈_Comparisons.py`
  - [ ] WECA vs other Combined Authorities
  - [ ] WECA vs regional/national benchmarks
  - [ ] Time series comparisons
  - [ ] Per capita comparisons
  - [ ] Rank/position indicators

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
