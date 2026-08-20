"""
ui/main_menus.py
Menu/fork screens: the per-mode task menus, the Orthography hub fork, and
the not-yet-implemented task placeholder.
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
