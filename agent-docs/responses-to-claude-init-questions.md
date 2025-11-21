1. Project Stage & Code Organization
Q. What's the current development stage? 
A. exploratory/prototyping - but need to move to production in a planned and tested way
Q. Do you plan to create a src/ directory structure for Python modules, or keep notebooks for analysis?
A. Follow python best practice use src/ - I don't think we need notebooks
Q. What should the typical module structure look like? (e.g., src/data/, src/visualization/, src/api/?)
A. yes i think src/ as you've suggested
2. Dashboard Framework
Q. Have you decided on the dashboarding framework? (options mentioned: D3, echarts, highcharts)
A. No, please research options and recommend
Q. Do you need both a web app AND API endpoints, or just interactive dashboard?
A. please explain benefits of each and recommend strategy
3. Data Access & MotherDuck
Q. How should connection credentials be managed? (environment variables, config file?)
A. environment variables
Q. Are there any data refresh/update patterns I should know about?
A. Data updates infrequently, but schemas can change, e.g. EPC schema
Q. Should I assume read-only access to MotherDuck, or write capabilities too?
A. read only
4. Development Workflow
Q. Do you develop primarily in Jupyter notebooks, scripts, or both?
A. Interactive ipykernel (.py) scripts with code fences like `# %%`
Q. Should I create reusable Python modules or focus on notebook-based analysis?
A. reusable Python modules
Q. Any preference for data processing: DuckDB SQL, Polars, or combination?
A. Where possible use DuckDB's relational API for python, or duckDB's SQL API, polars if the operation can't be done in duckDB - using Motherduck (cloud DuckDB) will be more performant I think.
5. Testing & Quality
Q. What level of testing do you want? (unit tests, integration tests, data validation?)
A. Comprehensive test suite. I will leave it to you to follow best practice
Q. Should I write tests for data processing pipelines?
A. Yes
6. Deployment & Hosting
Q. Hosting platform preference? (Streamlit Cloud, Render, Railway, Heroku free tier, GitHub Pages + static site?)
A. Streamlit cloud seems to work well
Q. Do you need Docker containerization?
A. no
Q. Any CI/CD pipeline preferences? (GitHub Actions?)
A. No
7. Geographic & Data Scope
Q. Primary focus: WECA + constituent authorities + North Somerset?
A. Yes, but would be good to compare headline indicators \ metrics with other combined authorities
Q. Should visualizations support different geographic levels (LSOA, MSOA, LA, CA)?
A. Yes
Q. Any specific time periods to focus on?
A. most recent 10 years - there is a delay between publication of the emissions data so July 2025 the 2023 data was released
8. Visualizations & Interactivity
Q. Key visualization types needed? (time series, spatial maps, breakdowns by sector, comparisons?)
A. yes all of these
Q. Interactive filtering requirements? (year, geography, sector, building type?)
A. Yes identify key likely criteria for filtering and grouping from the data
Q. Should maps use Leaflet with GeoJSON, or other mapping libraries?
A. research the most robust and performant approach
9. Documentation
Q. Should I document data transformation logic inline, in separate docs, or both?
A. use good docstrings and document separately
Q. Need data dictionaries or schema documentation auto-generated?
A. yes
Q. User-facing documentation needs?
A. minimal
10. Special Considerations
Q. Any accessibility requirements (WCAG compliance)?
A. yes WCAG where possible
Q. Performance constraints (e.g., dashboard must load in < 3s)?
A. that seems reasonable
Q. Mobile responsiveness critical?
A. no
Q. Any specific visual identity guidelines I should follow?
A. Follow @weca-brand.json in @CLAUDE_PROJECT_FOLDER