"""
Excelerant - Lexical Database Processing App
=============================================

Navigation Flow:
- Welcome Screen → Upload Database → Main Menu → Task Execution → Back to Main Menu

Screen-rendering code lives in ui/ (one module per task/screen group);
this file is just the composition root: page config/CSS and the run loop.
"""

import streamlit as st

from ui import init_session_state, render_current_screen, render_scroll_to_top


def main():
    """Main application entry point."""
    st.set_page_config(
        page_title="Excelerant",
        page_icon="assets/excelerant_favicon.png",
        layout="wide",
        initial_sidebar_state="collapsed",
    )

    st.markdown(
        """
        <style>
        .block-container {
            padding-top: 2rem;
        }
        .stButton > button {
            min-height: 2.5rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    init_session_state()
    render_current_screen()

    # Handle scroll-to-top at the very end (to avoid creating space at top)
    render_scroll_to_top()


if __name__ == "__main__":
    main()
