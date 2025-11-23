"""GHG Emissions Dashboard - Main Application Entry Point.

West of England Combined Authority (WECA) greenhouse gas emissions and
environmental data visualization dashboard.

This is a multi-page Streamlit application providing interactive analysis of:
- Sub-national GHG emissions (LA and CA level)
- Energy Performance Certificate (EPC) data
- Geographic analysis at multiple levels (LSOA, MSOA, LA, CA)
- Deprivation and housing tenure data

Usage:
    streamlit run app.py

Environment Variables:
    MOTHERDUCK_TOKEN: Authentication token for MotherDuck database access

Author: West of England Combined Authority
License: GNU AGPL v3
"""

import streamlit as st
from dotenv import load_dotenv

from src.visualization.themes import WEST_GREEN, register_weca_template

# Load environment variables
load_dotenv()

# Register WECA Plotly template
register_weca_template()


def main() -> None:
    """Main application entry point.

    Configures the Streamlit page and displays the home page content.
    """
    # Page configuration
    st.set_page_config(
        page_title="WECA GHG Emissions Dashboard",
        page_icon="🌱",
        layout="wide",
        initial_sidebar_state="expanded",
        menu_items={
            "Get Help": "https://github.com/stevecrawshaw/ghg-emissions",
            "Report a bug": "https://github.com/stevecrawshaw/ghg-emissions/issues",
            "About": """
            ### WECA GHG Emissions Dashboard

            Interactive analysis of greenhouse gas emissions and environmental data
            for the West of England Combined Authority.

            **Geographic Coverage:**
            - Bath and North East Somerset
            - Bristol
            - South Gloucestershire
            - North Somerset

            **Data Sources:**
            - UK local authority GHG emissions (BEIS)
            - Energy Performance Certificates (EPC)
            - Index of Multiple Deprivation (IMD)
            - ONS Geographic data

            **License:** GNU AGPL v3
            """,
        },
    )

    # Custom CSS for WECA branding
    st.markdown(
        f"""
        <style>
        /* WECA Brand Colors */
        :root {{
            --weca-green: {WEST_GREEN};
            --weca-forest: #1D4F2B;
            --weca-purple: #590075;
            --weca-claret: #CE132D;
            --weca-black: #1F1F1F;
        }}

        /* Header styling */
        .main-header {{
            background: linear-gradient(90deg, {WEST_GREEN} 0%, #1D4F2B 100%);
            padding: 2rem;
            border-radius: 0.5rem;
            margin-bottom: 2rem;
            color: white;
        }}

        .main-header h1 {{
            margin: 0;
            color: white;
            font-size: 2.5rem;
        }}

        .main-header p {{
            margin: 0.5rem 0 0 0;
            color: white;
            opacity: 0.9;
        }}

        /* Sidebar styling */
        section[data-testid="stSidebar"] {{
            background-color: #F8F9FA;
        }}

        /* Metric cards */
        [data-testid="stMetricValue"] {{
            font-size: 2rem;
            color: {WEST_GREEN};
        }}

        /* Links */
        a {{
            color: {WEST_GREEN};
        }}

        a:hover {{
            color: #1D4F2B;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Main header
    st.markdown(
        """
        <div class="main-header">
            <h1>🌱 WECA GHG Emissions Dashboard</h1>
            <p>Greenhouse gas emissions and environmental data for the
            West of England</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Welcome section
    st.markdown(
        """
        ## Welcome

        This dashboard provides interactive analysis of greenhouse gas (GHG)
        emissions and environmental performance data for the **West of England
        Combined Authority** (WECA) region.

        ### 🔍 What's Available

        Use the navigation sidebar to explore:

        - **📊 Emissions Overview**: Time series analysis of GHG emissions by sector
          and local authority
        - **🗺️ Geographic Analysis**: Map-based visualization at LSOA, MSOA, and
          LA levels
        - **🏘️ EPC Analysis**: Energy Performance Certificate data for domestic and
          non-domestic properties
        - **💡 Insights**: Key trends, comparisons with other regions, and
          recommendations

        ### 📍 Geographic Coverage

        **West of England Combined Authority:**
        - Bath and North East Somerset
        - Bristol
        - South Gloucestershire

        **Also included:**
        - North Somerset

        ### 📅 Data Currency

        Most datasets cover the **most recent 10 years** (currently 2014-2023).
        Note: Emissions data has an ~18-month publication lag.

        ### 📥 Open Data

        All data visualizations can be exported in multiple formats (CSV, Parquet,
        JSON, Excel) for reuse and further analysis.

        ---

        **Select a page from the sidebar to begin exploring the data** →
        """
    )

    # Footer
    st.markdown(
        """
        ---

        <div style='text-align: center; color: #6c757d; padding: 2rem 0;'>
            <p>
                <strong>West of England Combined Authority</strong><br>
                Data dashboard for greenhouse gas emissions analysis<br>
                <small>License: GNU AGPL v3 | Built with Streamlit & Plotly</small>
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Sidebar info
    with st.sidebar:
        st.markdown("## 📊 Dashboard")
        st.markdown("---")
        st.markdown("### 📚 Quick Links")
        st.markdown(
            """
            - [WECA Website](https://www.westofengland-ca.gov.uk/)
            - [Data Sources](https://github.com/stevecrawshaw/ghg-emissions#data-sources)
            - [GitHub Repository](https://github.com/stevecrawshaw/ghg-emissions)
            """
        )

        st.markdown("### 🆘 Help & Support")
        st.markdown(
            """
            For questions or issues:
            - [Report a bug](https://github.com/stevecrawshaw/ghg-emissions/issues)
            """
        )

        st.markdown("---")
        st.caption("Version 1.0.0 | Last updated: 2025-11-21")


if __name__ == "__main__":
    main()
