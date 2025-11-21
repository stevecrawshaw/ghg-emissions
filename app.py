"""GHG Emissions Dashboard - Main Application Entry Point.

This is the main Streamlit application for the West of England Combined Authority
(WECA) Greenhouse Gas Emissions Dashboard. It provides interactive visualizations
and analysis of sub-national emissions and environmental data.

Features:
- Interactive emissions analysis across multiple geographic levels
- Energy Performance Certificate (EPC) analysis
- Geographic visualizations with LSOA, MSOA, LA, and CA boundaries
- Comparative analysis with other Combined Authorities
- WCAG AA accessible interface with WECA branding

Usage:
    streamlit run app.py

Environment Variables:
    MOTHERDUCK_TOKEN: Authentication token for MotherDuck database access

Author: West of England Combined Authority
License: GNU AGPL v3
"""

import streamlit as st


def main() -> None:
    """Main application entry point.

    Configures the Streamlit page and displays the home page content.
    """
    # Page configuration
    st.set_page_config(
        page_title="WECA GHG Emissions Dashboard",
        page_icon="🌍",
        layout="wide",
        initial_sidebar_state="expanded",
        menu_items={
            "Get Help": "https://github.com/stevecrawshaw/ghg-emissions",
            "Report a bug": "https://github.com/stevecrawshaw/ghg-emissions/issues",
            "About": """
            # WECA GHG Emissions Dashboard

            Interactive dashboard for analyzing greenhouse gas emissions
            and environmental data for the West of England Combined Authority.

            **License**: GNU AGPL v3
            """,
        },
    )

    # Main content
    st.title("🌍 WECA GHG Emissions Dashboard")

    st.markdown(
        """
        ## Welcome

        This dashboard provides interactive analysis of greenhouse gas (GHG) emissions
        and environmental data for the **West of England Combined Authority (WECA)**
        and its constituent local authorities.

        ### What's Included

        - 📊 **Emissions Analysis**: Time series and sector breakdowns
        - 🏘️ **EPC Data**: Energy performance of domestic and non-domestic properties
        - 🗺️ **Geographic Views**: Interactive maps at LSOA, MSOA, LA, and CA levels
        - 📈 **Comparisons**: Benchmarks against other Combined Authorities

        ### Geographic Coverage

        **West of England Combined Authority:**
        - Bath and North East Somerset
        - Bristol
        - South Gloucestershire

        **Also includes:**
        - North Somerset (not yet a WECA member)

        ### Data Sources

        - UK Government Sub-national GHG Emissions Data
        - Energy Performance Certificate (EPC) Register
        - ONS Geographic and Population Data
        - Index of Multiple Deprivation (IMD)

        ---

        **Status**: 🚧 Under Development

        _This dashboard is currently in development. More features coming soon!_
        """
    )

    # Sidebar
    with st.sidebar:
        st.markdown("## Navigation")
        st.markdown(
            """
            Use the navigation above to explore:

            - 📊 **Emissions Analysis**
            - 🏘️ **EPC Data**
            - 🗺️ **Geographic Views**
            - 📈 **Comparisons**
            """
        )

        st.markdown("---")

        st.markdown(
            """
            ### About WECA

            The West of England Combined Authority works with
            local partners to drive inclusive and sustainable
            economic growth across the region.

            [Learn more about WECA](https://www.westofengland-ca.gov.uk/)
            """
        )

        st.markdown("---")

        st.caption(
            """
            **License**: GNU AGPL v3

            **Source**: [GitHub](https://github.com/stevecrawshaw/ghg-emissions)
            """
        )


if __name__ == "__main__":
    main()
