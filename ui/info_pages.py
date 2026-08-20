"""
ui/info_pages.py
Static informational screens reachable from the welcome screen.
"""

import streamlit as st

from ui.navigation import Screen, navigate_to


def screen_about():
    """About page with app information."""
    st.title("About Excelerant")
    st.markdown("---")

    st.markdown(
        """
        ### Version

        v0.5

        ### GitHub

        [github.com/ryangehrmann/Excelerant](https://github.com/ryangehrmann/Excelerant)

        ### Contact

        For questions or feedback, contact excelerant.linguistics@gmail.com.
        """
    )

    st.markdown("---")

    if st.button("Back", type="primary"):
        navigate_to(Screen.WELCOME)


def screen_tutorial():
    """Tutorial page with learning resources."""
    st.title("Tutorial")
    st.markdown("---")

    st.markdown(
        """
        ### Getting Started

        Watch our video tutorials to learn how to use Excelerant effectively.

        #### Video 1: Uploading Your Database
        """
    )

    st.info("YouTube video will be embedded here")

    st.markdown("#### Video 2: Configuring Transcriptions")

    st.info("YouTube video will be embedded here")

    st.markdown("#### Video 3: Phonological Analysis")

    st.info("YouTube video will be embedded here")

    st.markdown("---")

    if st.button("Back", type="primary"):
        navigate_to(Screen.WELCOME)
