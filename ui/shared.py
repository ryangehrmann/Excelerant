"""
ui/shared.py
Helpers shared across the main-menu screens.
"""

import streamlit as st

from tasks import reorder_columns
from ui.navigation import Screen, navigate_to
from ui.tasks_registry import TASKS


def _render_main_menu_banner():
    """Render the centered banner used on main menu screens."""
    import base64

    with open("assets/excelerant_banner.png", "rb") as f:
        banner_data = base64.b64encode(f.read()).decode()

    st.markdown(
        f'<div style="display: flex; justify-content: center; margin-bottom: 1rem;"><img src="data:image/png;base64,{banner_data}" width="600"></div>',
        unsafe_allow_html=True,
    )


def _render_task_detail(right_col):
    """Render the right-column task detail view (shared by all main menus)."""
    with right_col:
        if st.session_state.selected_task is None:
            # No task selected - show hint, then preview
            st.info("Select a task from the left panel to see details and begin.")

            st.markdown("---")

            st.subheader("Database Preview")

            df = reorder_columns(st.session_state.database)
            st.markdown(f"**Rows:** {len(df):,} · **Columns:** {len(df.columns)}")

            with st.expander("Columns", expanded=False):
                for col in df.columns:
                    st.text(f"• {col}")

            with st.expander("Data Preview", expanded=True):
                st.dataframe(df.head(10), use_container_width=True, height=300)

        else:
            # Show selected task info
            task = TASKS[st.session_state.selected_task]

            # Navigation buttons at top
            col1, col2 = st.columns([1, 1])

            with col1:
                if st.button("Back to Preview", use_container_width=True):
                    st.session_state.selected_task = None
                    st.rerun()

            with col2:
                if st.button("Begin", type="primary", use_container_width=True):
                    # Navigate to task screen based on selected task
                    task_screens = {
                        "create_data_collection_script": Screen.TASK_CREATE_DATA_COLLECTION_SCRIPT,
                        "create_prompts_list": Screen.TASK_CREATE_PROMPTS_LIST,
                        "add_audio_links": Screen.TASK_ADD_AUDIO_LINKS,
                        "update_entries_from_words": Screen.TASK_UPDATE_ENTRIES_FROM_WORDS,
                        "explode_entries": Screen.TASK_EXPLODE_ENTRIES,
                        "segment_words": Screen.TASK_SEGMENT_WORDS,
                        "generate_cards": Screen.TASK_GENERATE_CARDS,
                        "process_cards": Screen.TASK_PROCESS_CARDS,
                        "sort_cards": Screen.TASK_SORT_CARDS,
                    }
                    target_screen = task_screens.get(task.id, Screen.TASK_PLACEHOLDER)
                    navigate_to(target_screen)

            st.subheader(task.name)

            st.markdown("---")

            st.markdown("**Description:**")
            st.markdown(task.description)

            st.markdown("---")

            st.markdown("**Requirements:**")
            for req in task.requirements:
                st.markdown(f"- {req}")

            st.markdown("---")

            st.markdown("**Example:**")
            st.code(task.example, language=None)

            st.markdown("---")

            # Tutorial link
            if task.youtube_url:
                st.markdown(f"[Watch Tutorial]({task.youtube_url})")
            else:
                st.markdown("*Tutorial video coming soon*")
