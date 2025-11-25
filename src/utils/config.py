"""Configuration utilities for the GHG Emissions Dashboard.

Provides shared configuration functions that can be used across all pages.
"""

import streamlit as st


def apply_home_page_label() -> None:
    """Apply CSS to change 'app' label to 'Home' in sidebar navigation.

    This function should be called in app.py and all page files to ensure
    consistent labeling across the entire application. The CSS override
    targets the first navigation item (the main app.py entry point).
    """
    st.markdown(
        """
        <style>
        /* Override "app" label with "Home" in sidebar navigation */
        [data-testid="stSidebarNav"] li:first-child a span:first-child {
            display: none;
        }
        [data-testid="stSidebarNav"] li:first-child a::before {
            content: "🏠 Home";
            font-size: 1rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
