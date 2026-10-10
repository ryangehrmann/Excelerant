"""
ui/main_menus.py
Menu/fork screens: the shared per-mode task menu (_render_mode_menu and its
thin per-mode wrappers), the Collect Data forks (standard-vs-custom, then
recording platform), the Manage Database landing page, the Phonology and
Orthography hub forks, the Acoustic
placeholder, and the not-yet-implemented task placeholder.
"""

import streamlit as st

from tasks import export_database
from ui.navigation import Screen, navigate_to, go_back_to_menu
from ui.tasks_registry import TASKS, ENABLED_TASKS, MENU_CATEGORIES
from ui.shared import _render_main_menu_banner, _render_task_detail


def _start_participatory_card_sorting():
    """Entry point for Participatory Card Sorting, shared by the Phonology and
    Orthography hubs: upload a database, then the card-sorting task menu."""
    st.session_state.analysis_mode = "card_sorting"
    navigate_to(Screen.UPLOAD_DATABASE)


def screen_phonology_hub():
    """Analyze Phonology landing: currently just Participatory Card Sorting."""

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.markdown("---")
        st.image("assets/excelerant_banner.png", width="stretch")
        st.markdown("---")

        st.markdown(
            """
            ### Phonology

            What kind of phonology work are you doing?
            """
        )

        st.markdown("")

        if st.button(
            "Participatory Card Sorting",
            width="stretch",
            type="primary",
        ):
            _start_participatory_card_sorting()

        st.markdown("")

        if st.button("Back to Welcome", width="stretch"):
            navigate_to(Screen.WELCOME)


def screen_orthography_hub():
    """Fork between Participatory Card Sorting and Script Conversion."""

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.markdown("---")
        st.image("assets/excelerant_banner.png", width="stretch")
        st.markdown("---")

        st.markdown(
            """
            ### Orthography

            What kind of orthography work are you doing?
            """
        )

        st.markdown("")

        if st.button(
            "Participatory Card Sorting",
            width="stretch",
            type="primary",
        ):
            _start_participatory_card_sorting()

        st.markdown("")

        if st.button(
            "Script Conversion",
            width="stretch",
            type="primary",
        ):
            navigate_to(Screen.SCRIPT_CONVERTER)

        st.markdown("")

        if st.button("Back to Welcome", width="stretch"):
            navigate_to(Screen.WELCOME)


def screen_collect_lexical_data_hub():
    """Collect Data landing: start from a bundled standard word list tool, or
    upload a custom word list."""

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.markdown("---")
        st.image("assets/excelerant_banner.png", width="stretch")
        st.markdown("---")

        st.markdown(
            """
            ### Collect Data

            Excelerant builds you a **recording script** - an ordered prompt
            list that walks a speaker through a word list one item at a time,
            saving a separate, analysis-ready audio file for each.

            Start from a ready-made word list, or bring your own.
            """
        )

        st.markdown("")

        st.markdown("#### Standard word list tool")
        st.markdown(
            "A curated, pre-prepared word list with glosses in more than one "
            "language - currently the **Big Excelerant Word List (BEWL)**: "
            "1,886 items for Mainland Southeast Asia, English and Lao."
        )
        if st.button("Use a standard word list", width="stretch", type="primary"):
            st.session_state.collect_source = "standard"
            st.session_state.selected_word_list_tool = None
            st.session_state.collection_target = None
            navigate_to(Screen.STANDARD_WORD_LISTS)

        st.markdown("")

        st.markdown("#### Your own word list")
        st.markdown(
            "Upload your own spreadsheet - an `index` column and at least one "
            "column of glosses to prompt with."
        )
        if st.button("Upload my own word list", width="stretch", type="primary"):
            st.session_state.collect_source = "custom"
            navigate_to(Screen.UPLOAD_DATABASE)

        st.markdown("")

        if st.button("Back to Welcome", width="stretch"):
            navigate_to(Screen.WELCOME)


def screen_manage_database_hub():
    """Manage Database landing: explains what the section is for (keeping an
    existing Excelerant database in step with the analysis), then uploads."""

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.markdown("---")
        st.image("assets/excelerant_banner.png", width="stretch")
        st.markdown("---")

        st.markdown(
            """
            ### Manage Database

            Use this section once you have an Excelerant lexical database. It
            keeps the database in step with your analysis as your
            transcriptions develop.
            """
        )

        st.markdown("")

        st.markdown("#### Update entries from revised transcriptions")
        st.markdown(
            """
            In an Excelerant database, each entry is split into words (one
            row per word, numbered by `sub_index`), and each word is split
            into segment columns: `P` `R` `C` `M` `V` `F` `T`. In the
            spreadsheet Excelerant exports, the `word` column is a formula
            built from those segments, so when you revise a segment (say,
            after deciding an onset is phonemically /ʔb/ rather than [b]),
            the word updates automatically.

            The `entry` column doesn't. **Check Database Formatting & Update
            Entries** rebuilds every entry from its current words, so entries
            reflect your latest phonemic transcription. Whenever an entry
            changes, the previous entries are saved in a dated column (for
            example `entry_before_2026-10-10`), so the database keeps a record
            of each revision.

            A typical cycle:
            1. Download your database from Excelerant.
            2. Revise segments or words in Excel as your analysis progresses.
            3. Upload the spreadsheet here and run **Check Database
               Formatting & Update Entries**.
            4. Download the updated database.
            """
        )

        st.markdown("")

        st.markdown("#### Setting up and extending the database")
        st.markdown(
            """
            - **Explode Entries** splits multi-word entries into one word per
              row, adding the `word` and `sub_index` columns.
            - **Segment Words** breaks each word into the `P`-`T` segment
              columns.
            - **Add Audio File Links to Database** matches your recordings
              to entries by index and adds clickable links to them.

            Rows that aren't transcribed yet can stay blank; they're carried
            through every step and filled in later.
            """
        )

        st.markdown("")

        if st.button("Upload my database", width="stretch", type="primary"):
            navigate_to(Screen.UPLOAD_DATABASE)

        st.markdown("")

        if st.button("Back to Welcome", width="stretch"):
            navigate_to(Screen.WELCOME)


def screen_collect_platform():
    """Choose the recording platform (SpeechRecorder / Prompts). Reached after
    picking a standard word list tool, or after uploading a custom database."""

    source = st.session_state.get("collect_source")

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.markdown("---")
        st.image("assets/excelerant_banner.png", width="stretch")
        st.markdown("---")

        st.markdown(
            """
            ### Where will you record?

            Pick the tool you'll use to run the recording session. Excelerant
            builds the file it imports.
            """
        )

        st.markdown("")

        # ── SpeechRecorder (PC / Mac / Linux) ───────────────────────────
        st.markdown("#### SpeechRecorder (computer)")
        st.markdown(
            "A desktop recording program for Windows, macOS, and Linux from "
            "the Bavarian Archive for Speech Signals. Best for recording at a "
            "table with a laptop and an external microphone.  \n"
            "[Download SpeechRecorder]"
            "(https://www.bas.uni-muenchen.de/Bas/software/speechrecorder/)"
        )
        if st.button("SpeechRecorder", width="stretch", type="primary"):
            _choose_platform("speechrecorder", source)

        st.markdown("")

        # ── Prompts (Android) ───────────────────────────────────────────
        st.markdown("#### Prompts (Android phone)")
        st.markdown(
            "A small, offline Android app for recording in the field straight "
            "from a phone. One prompt at a time, an uncompressed WAV per item, "
            "no internet permission, no account - pull the files off over USB.  \n"
            "[Download Prompts (Android APK)]"
            "(https://github.com/ryangehrmann/Prompts/releases/latest/download/Prompts.apk)"
            " · [source](https://github.com/ryangehrmann/Prompts)"
        )
        if st.button("Prompts", width="stretch", type="primary"):
            _choose_platform("prompts", source)

        st.markdown("")

        if source == "standard":
            if st.button("← Back to word lists", width="stretch"):
                st.session_state.selected_word_list_tool = None
                navigate_to(Screen.STANDARD_WORD_LISTS)
        else:
            if st.button("← Back to upload", width="stretch"):
                navigate_to(Screen.UPLOAD_DATABASE)


def _choose_platform(target: str, source: str | None):
    st.session_state.collection_target = target
    # Any generated output belonged to the previous platform.
    for key in (
        "_swl_script", "_swl_script_tool_id",
        "_swl_prompts", "_swl_prompts_tool_id",
    ):
        st.session_state.pop(key, None)
    if source == "standard":
        navigate_to(Screen.STANDARD_WORD_LISTS)
    else:
        go_back_to_menu()


def _render_mode_menu(mode: str):
    """Shared task-list main menu used by every database-backed mode.

    Left column: the mode's enabled tasks (filtered by MENU_CATEGORIES[mode])
    plus the download / replace / clear database controls. Right column: the
    selected task's detail, or the database preview.

    For "collect" mode the task list is narrowed further to the single builder
    for the platform picked on the Collect Data screen.
    """

    # Add vertical divider CSS just for this screen
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

    _render_main_menu_banner()

    st.markdown("---")

    # Two-column layout (1/3 left, 2/3 right)
    left_col, right_col = st.columns([1, 2])

    with left_col:
        st.markdown("**Tasks**")

        allowed_categories = MENU_CATEGORIES[mode]
        target_task = None
        if mode == "collect":
            target_task = {
                "speechrecorder": "create_data_collection_script",
                "prompts": "create_prompts_list",
            }.get(st.session_state.get("collection_target"))

        for task in TASKS.values():
            if task.id not in ENABLED_TASKS:
                continue
            if task.category not in allowed_categories:
                continue
            if target_task and task.id != target_task:
                continue

            is_selected = st.session_state.selected_task == task.id
            button_type = "primary" if is_selected else "secondary"

            if st.button(
                task.name,
                key=f"btn_{task.id}",
                width="stretch",
                type=button_type,
            ):
                st.session_state.selected_task = task.id
                st.rerun()

        # Database options at the bottom of the left column
        st.markdown("---")
        st.markdown("**Database**")

        st.download_button(
            label="Download Database",
            data=export_database(st.session_state.database),
            file_name="database.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            width="stretch",
        )

        if st.button("Replace Database", width="stretch"):
            navigate_to(Screen.UPLOAD_DATABASE)

        if st.button("Clear Database & Start Over", width="stretch"):
            st.session_state.database = None
            st.session_state.database_validated = False
            st.session_state.database_filename = None
            st.session_state.database_sheet_name = None
            st.session_state.selected_task = None
            navigate_to(Screen.WELCOME)

    _render_task_detail(right_col)


def screen_main_menu_manage():
    """Main menu for Manage Lexical Data (audio linking + transcription prep)."""
    _render_mode_menu("manage")


def screen_main_menu_phonological():
    """Main menu for Analyze Phonology."""
    _render_mode_menu("phonological")


def screen_main_menu_card_sorting():
    """Main menu for Participatory Card Sorting (reached from the Phonology
    and Orthography hubs)."""
    _render_mode_menu("card_sorting")


def screen_main_menu_collect():
    """Main menu for Collect Data (task list narrowed to the chosen platform)."""
    _render_mode_menu("collect")


def screen_main_menu_acoustic():
    """Placeholder main menu for Acoustic Phonetic Analysis (not yet implemented)."""
    st.title("Acoustic Phonetic Analysis")
    st.markdown("---")
    st.info("This section is not yet implemented.")

    if st.button("Back to Welcome", type="primary"):
        navigate_to(Screen.WELCOME)


def screen_task_placeholder():
    """Placeholder for task screens."""
    task_id = st.session_state.selected_task

    if task_id and task_id in TASKS:
        task = TASKS[task_id]
        st.title(task.name)
    else:
        st.title("Task")

    st.markdown("---")

    st.info("This task is not yet implemented.")

    st.markdown("This is where the task-specific interface will go.")

    st.markdown("---")

    if st.button("Back to Main Menu", type="primary"):
        go_back_to_menu()
