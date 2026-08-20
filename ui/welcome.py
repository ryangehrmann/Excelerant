"""
ui/welcome.py
Landing screen: the three top-level analysis-path buttons.
"""

import streamlit as st

from ui.navigation import Screen, navigate_to


def screen_welcome():
    """Welcome screen with three options."""

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

            Excelerant helps you create and process lexical databases for
            phonological / phonetic analysis and participatory work in
            orthography development.

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

        # Three analysis path buttons side by side
        btn_left, btn_mid, btn_right = st.columns(3)

        with btn_left:
            if st.button("Phonology", use_container_width=True, type="primary"):
                st.session_state.analysis_mode = "phonological"
                navigate_to(Screen.UPLOAD_DATABASE)

        with btn_mid:
            if st.button("Orthography", use_container_width=True, type="primary"):
                st.session_state.analysis_mode = "orthography"
                navigate_to(Screen.ORTHOGRAPHY_HUB)

        with btn_right:
            st.button(
                "Acoustic Phonetics",
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
