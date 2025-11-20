# Greenhouse Gas Emissions Dashboard

A project to create a full - featured interactive, web based dashboard showing sub - national (local Authority and Combined Authority) emissions and environmental data broken down in a variety of ways.

## Audience

- Energy planning professionals
- Local government environment officers
- Data analysts
- Citizens (public access)

## Requirements

- Interactive. 
- Spatial.
- Responsive. Rendering on commonly used devices
- Complying with visual identity criteria
- Clean, professional corporate interface
- Focused on the West of England Combined Authority (WECA) and its constituent authorities - including North Somerset (which is not YET a member of the Combined Authority)
- Open data to be downloaded in a range of formats
- Clear labelling of visualisations and explanation for non - experts

## Technology stack guidance

- Using a modern interactive charting library like D3, echarts, or highcharts
- Interactive spatial representation using e.g. leaflet or similar
- Remote data source: Motherduck instance for the main data sources
- Motherduck is an OLAP database which uses duckDB SQL syntax
- A modern dashboarding library with tabs
- Python frameworks preferred for ease of maintenance
- Support compact modern data formats like parquet

## Constraints

- Free or cheap to host
- Developed and maintained by a single data analyst with intermediate python skills
