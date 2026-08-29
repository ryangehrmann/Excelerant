"""
ui/main_menus.py
Menu/fork screens: the per-mode task menus, the Collect Lexical Data and
Orthography hub forks, and the not-yet-implemented task placeholder.
"""

import streamlit as st

from tasks import export_database
from ui.navigation import Screen, navigate_to, go_back_to_menu
from ui.tasks_registry import TASKS, ENABLED_TASKS, MENU_CATEGORIES
from ui.shared import _render_main_menu_banner, _render_task_detail


def screen_orthography_hub():
    """Fork between Orthography Development (card-sorting tasks) and Script Conversion."""

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.markdown("---")
        st.image("assets/excelerant_banner.png", use_container_width=True)
        st.markdown("---")

        st.markdown(
            """
            ### Orthography

            What kind of orthography work are you doing?
            """
        )

        st.markdown("")

        if st.button(
            "Orthography Development",
            use_container_width=True,
            type="primary",
        ):
            navigate_to(Screen.UPLOAD_DATABASE)

        st.markdown("")

        if st.button(
            "Script Conversion",
            use_container_width=True,
            type="primary",
        ):
            navigate_to(Screen.SCRIPT_CONVERTER)

        st.markdown("")

        if st.button("Back to Welcome", use_container_width=True):
            navigate_to(Screen.WELCOME)


def screen_collect_lexical_data_hub():
    """Fork between the two data-collection platforms: SpeechRecorder (PC/Mac)
    and the Prompts app (Android). Both funnel into the shared database upload
    and then their respective prompt/script builder."""

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.markdown("---")
        st.image("assets/excelerant_banner.png", use_container_width=True)
        st.markdown("---")

        st.markdown(
            """
            ### Collect Lexical Data

            Excelerant builds you a **recording script** - an ordered prompt
            list that walks a speaker through your word list one item at a
            time, saving a separate, analysis-ready audio file for each.

            Which platform will you record on?
            """
        )

        st.markdown("")

        # ── SpeechRecorder (PC / Mac / Linux) ───────────────────────────
        st.markdown("#### 🖥️ SpeechRecorder (computer)")
        st.markdown(
            "A desktop recording program for Windows, macOS, and Linux from "
            "the Bavarian Archive for Speech Signals. Best for recording at a "
            "table with a laptop and an external microphone. Excelerant "
            "generates the XML script file that SpeechRecorder loads.  \n"
            "[Download SpeechRecorder →]"
            "(https://www.bas.uni-muenchen.de/Bas/software/speechrecorder/)"
        )

        if st.button(
            "Build a SpeechRecorder script",
            use_container_width=True,
            type="primary",
        ):
            st.session_state.collection_target = "speechrecorder"
            navigate_to(Screen.UPLOAD_DATABASE)

        st.markdown("")

        # ── Prompts (Android) ───────────────────────────────────────────
        st.markdown("#### 📱 Prompts (Android phone)")
        st.markdown(
            "A small, offline Android app for recording in the field straight "
            "from a phone. It shows one prompt at a time - vernacular gloss "
            "large, with optional English gloss and IPA for the surveyor - and "
            "saves an uncompressed WAV per item. No internet permission, no "
            "account, nothing to export: pull the files off over USB. "
            "Excelerant generates the prompt-list file the app imports.  \n"
            "[Download Prompts (Android APK) →]"
            "(https://github.com/ryangehrmann/Prompts/releases/latest/download/Prompts.apk)"
            " · [source](https://github.com/ryangehrmann/Prompts)"
        )

        if st.button(
            "Build a Prompts list",
            use_container_width=True,
            type="primary",
        ):
            st.session_state.collection_target = "prompts"
            navigate_to(Screen.UPLOAD_DATABASE)

        st.markdown("")

        if st.button("Back to Welcome", use_container_width=True):
            navigate_to(Screen.WELCOME)


def screen_main_menu_phonological():
    """Main menu for Phonological Analysis - flat task list, database options at bottom."""

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

        # Show only enabled tasks belonging to this menu's categories
        allowed_categories = MENU_CATEGORIES["phonological"]
        for task in TASKS.values():
            if task.id not in ENABLED_TASKS:
                continue
            if task.category not in allowed_categories:
                continue

            is_selected = st.session_state.selected_task == task.id
            button_type = "primary" if is_selected else "secondary"

            if st.button(
                task.name,
                key=f"btn_{task.id}",
                use_container_width=True,
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
            use_container_width=True,
        )

        if st.button("Replace Database", use_container_width=True):
            navigate_to(Screen.UPLOAD_DATABASE)

        if st.button("Clear Database & Start Over", use_container_width=True):
            st.session_state.database = None
            st.session_state.database_validated = False
            st.session_state.database_filename = None
            st.session_state.database_sheet_name = None
            st.session_state.selected_task = None
            navigate_to(Screen.WELCOME)

    _render_task_detail(right_col)


def screen_main_menu_orthography():
    """Main menu for Orthography Development - flat task list, database options at bottom."""

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

        # Show only enabled tasks belonging to this menu's categories
        allowed_categories = MENU_CATEGORIES["orthography"]
        for task in TASKS.values():
            if task.id not in ENABLED_TASKS:
                continue
            if task.category not in allowed_categories:
                continue

            is_selected = st.session_state.selected_task == task.id
            button_type = "primary" if is_selected else "secondary"

            if st.button(
                task.name,
                key=f"btn_{task.id}",
                use_container_width=True,
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
            use_container_width=True,
        )

        if st.button("Replace Database", use_container_width=True):
            navigate_to(Screen.UPLOAD_DATABASE)

        if st.button("Clear Database & Start Over", use_container_width=True):
            st.session_state.database = None
            st.session_state.database_validated = False
            st.session_state.database_filename = None
            st.session_state.database_sheet_name = None
            st.session_state.selected_task = None
            navigate_to(Screen.WELCOME)

    _render_task_detail(right_col)


def screen_main_menu_collect():
    """Main menu for Collect Lexical Data - flat task list, database options at bottom."""

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

        # Show only enabled tasks belonging to this menu's categories, narrowed
        # to the builder for the platform picked on the Collect Lexical Data
        # screen (SpeechRecorder vs. Prompts).
        allowed_categories = MENU_CATEGORIES["collect"]
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
                use_container_width=True,
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
            use_container_width=True,
        )

        if st.button("Replace Database", use_container_width=True):
            navigate_to(Screen.UPLOAD_DATABASE)

        if st.button("Clear Database & Start Over", use_container_width=True):
            st.session_state.database = None
            st.session_state.database_validated = False
            st.session_state.database_filename = None
            st.session_state.database_sheet_name = None
            st.session_state.selected_task = None
            navigate_to(Screen.WELCOME)

    _render_task_detail(right_col)


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
