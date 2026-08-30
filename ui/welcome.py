"""
ui/welcome.py
Landing screen: the five top-level section buttons (Collect Data, Manage
Database, Analyze Phonology, Develop Orthography, Analyze Phonetics).
"""

import streamlit as st

from ui.navigation import Screen, navigate_to


def screen_welcome():
    """Welcome screen: pick a top-level section."""

    # Center the welcome content
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.markdown("---")
        st.markdown("")
        st.image("assets/excelerant_banner.png", use_container_width=True)
        st.markdown("---")

        st.markdown(
            """
            ### Welcome!

            What would you like to work on?
            """
        )

        st.markdown("")

        # Style for the disabled Acoustic button (placed outside columns to avoid misalignment)
        st.markdown(
            """
            <style>
            button[data-testid="baseButton-primary"][disabled] {
                background-color: #a5d6a7 !important;
                color: rgba(255, 255, 255, 0.7) !important;
                border: none !important;
                cursor: not-allowed !important;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )

        # Analysis path buttons side by side. Each label is forced onto two
        # rows (markdown hard break) so all five buttons are the same height.
        btn_collect, btn_manage, btn_phon, btn_ortho, btn_acoustic = st.columns(5)

        with btn_collect:
            if st.button("Collect  \nData", use_container_width=True, type="primary"):
                st.session_state.analysis_mode = "collect"
                navigate_to(Screen.COLLECT_LEXICAL_DATA_HUB)

        with btn_manage:
            if st.button("Manage  \nDatabase", use_container_width=True, type="primary"):
                st.session_state.analysis_mode = "manage"
                navigate_to(Screen.UPLOAD_DATABASE)

        with btn_phon:
            st.button(
                "Analyze  \nPhonology",
                use_container_width=True,
                type="primary",
                disabled=True,
                help="Phonology analysis tools coming soon",
            )

        with btn_ortho:
            if st.button("Develop  \nOrthography", use_container_width=True, type="primary"):
                st.session_state.analysis_mode = "orthography"
                navigate_to(Screen.ORTHOGRAPHY_HUB)

        with btn_acoustic:
            st.button(
                "Analyze  \nPhonetics",
                use_container_width=True,
                type="primary",
                disabled=True,
                help="Coming soon",
            )

        st.markdown("")

        if st.button("About", use_container_width=True):
            navigate_to(Screen.ABOUT)

        st.markdown("")

        if st.button("Tutorial", use_container_width=True):
            navigate_to(Screen.TUTORIAL)
