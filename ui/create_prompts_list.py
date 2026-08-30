"""
ui/create_prompts_list.py
Screen for building a prompt-list file for the Prompts Android app.
"""

import streamlit as st

from tasks import generate_prompts_list
from ui.navigation import Screen, navigate_to, go_back_to_menu


# Where users get the Prompts app. Prompts is not on an app store; it's
# distributed as a signed APK from GitHub Releases (the /latest/ URL always
# points at the newest release).
PROMPTS_DOWNLOAD_URL = "https://github.com/ryangehrmann/Prompts/releases/latest/download/Prompts.apk"
PROMPTS_REPO_URL = "https://github.com/ryangehrmann/Prompts"


def _default_col(columns, candidates, fallback_index=0):
    """Pick the first column whose lowercased name matches a candidate, else a
    positional fallback."""
    lower = {c.lower(): c for c in columns}
    for cand in candidates:
        if cand in lower:
            return columns.index(lower[cand])
    return fallback_index


def screen_create_prompts_list():
    """Screen for building a Prompts-app prompt list from the database."""

    # Add vertical divider CSS
    st.markdown(
        """
        <style>
        div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"]:first-child {
            border-right: 1px solid #ccc;
            padding-right: 1.5rem !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.title("Create Prompts List (Android)")
    st.markdown("---")

    config_col, output_col = st.columns([1, 2])

    df = st.session_state.database
    columns = list(df.columns)
    optional_columns = ["-none-"] + columns

    with config_col:
        st.subheader("Column Mapping")

        st.markdown("**Required**")

        index_col = st.selectbox(
            "Index column",
            options=columns,
            index=_default_col(columns, ["index", "id", "no", "number"]),
            help="Unique value per item. The app saves each recording as <index>.wav.",
        )

        vernacular_col = st.selectbox(
            "Vernacular / prompt column (shown large)",
            options=columns,
            index=_default_col(
                columns,
                ["gloss_v", "vernacular", "word", "entry_ortho", "national", "entry"],
            ),
            help=(
                "The text the speaker reads on screen - usually your "
                "national-language / orthographic column."
            ),
        )

        st.markdown("")
        st.markdown("**Optional**")

        english_col = st.selectbox(
            "English gloss column (shown small, below)",
            options=optional_columns,
            index=(optional_columns.index("gloss") if "gloss" in optional_columns else 0),
            help="A second gloss shown under the vernacular text.",
        )

        ipa_col = st.selectbox(
            "IPA column (shown small, bottom-right)",
            options=optional_columns,
            index=0,
            help="An IPA transcription shown for the surveyor's reference.",
        )

        st.markdown("---")

        generate_clicked = st.button(
            "Generate Prompts List",
            type="primary",
            use_container_width=True,
        )

        st.markdown("")

        if st.button("Back to Main Menu", use_container_width=True):
            for key in ("_prompts_list_csv", "_prompts_list_xlsx", "_prompts_list_preview"):
                st.session_state.pop(key, None)
            go_back_to_menu()

    with output_col:
        st.subheader("Output")

        if generate_clicked:
            english = None if english_col == "-none-" else english_col
            ipa = None if ipa_col == "-none-" else ipa_col

            with st.spinner("Building prompt list..."):
                result = generate_prompts_list(
                    df=df,
                    index_col=index_col,
                    vernacular_col=vernacular_col,
                    english_col=english,
                    ipa_col=ipa,
                )

            if not result.success:
                st.error(f"**Error:** {result.error}")
            else:
                st.session_state._prompts_list_csv = result.csv_text
                st.session_state._prompts_list_xlsx = result.xlsx_bytes
                st.session_state._prompts_list_preview = result.dataframe
                st.session_state._scroll_to_top = True
                st.rerun()

        if st.session_state.get("_prompts_list_csv"):
            preview = st.session_state._prompts_list_preview
            st.success(f"Prompt list generated - {len(preview):,} prompts.")

            dl_col1, dl_col2 = st.columns(2)
            with dl_col1:
                st.download_button(
                    "Download prompts.csv",
                    data=st.session_state._prompts_list_csv.encode("utf-8"),
                    file_name="prompts.csv",
                    mime="text/csv",
                    type="primary",
                    use_container_width=True,
                )
            with dl_col2:
                st.download_button(
                    "Download prompts.xlsx",
                    data=st.session_state._prompts_list_xlsx,
                    file_name="prompts.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                )

            st.markdown("---")

            st.markdown("**Preview**")
            st.dataframe(preview, use_container_width=True, height=320)

            st.markdown("---")

            st.markdown(
                """
                **Using the file in Prompts:**

                1. Copy `prompts.csv` (or `.xlsx`) onto the Android device.
                2. Open **Prompts**, tap **Import Prompt List…**, pick the file.
                3. Enter a respondent / session ID, tap **Start Session**.
                4. Record each prompt in turn. Recordings land in
                   `Music/VoiceNotes/<list name>/<respondent id>/<index>.wav`.
                5. Connect the phone over USB and copy the `VoiceNotes` folder
                   off - then bring the audio into your database with
                   **Add Audio File Links to Database**.
                """
            )

            _render_get_prompts_app()
        else:
            st.info(
                "Map your columns in the left panel, then click "
                "**Generate Prompts List**."
            )

            st.markdown("---")

            st.markdown("**About the Prompts app**")
            st.markdown(
                "**Prompts** is an offline Android app for prompt-driven audio "
                "elicitation. One prompt at a time, a big Record / Stop button, "
                "Play to review, Previous / Next to move. It records uncompressed "
                "16-bit / 44.1 kHz mono WAV — the same analysis-ready format "
                "SpeechRecorder produces.\n\n"
                "The file it imports is a plain table with a header row: "
                "`index`, `gloss_v` (required), `gloss_e`, `ipa`.\n\n"
                f"Source and build instructions: {PROMPTS_REPO_URL}"
            )

            _render_get_prompts_app()


def _render_get_prompts_app():
    """Explain how to obtain the Prompts APK."""
    st.markdown("---")
    if PROMPTS_DOWNLOAD_URL:
        st.markdown(f"**[Download Prompts (Android APK)]({PROMPTS_DOWNLOAD_URL})**")
        st.caption(
            "Sideload: on the device, allow installs from your browser / files "
            "app, open the APK, and confirm. Play Protect may warn about an app "
            "installed outside the Play Store — that is expected."
        )
    else:
        st.warning(
            "**Getting the app:** Prompts is not on the Play Store yet and a "
            "download link is still being set up. For now, contact the "
            "Excelerant maintainer for a signed APK, or build it from source "
            "with Android Studio."
        )
