"""
ui/navigation.py
Screen routing constants and the session-state primitives every screen
uses to move around the app.
"""

import streamlit as st
import streamlit.components.v1 as components


class Screen:
    """All possible screens in the app (string constants)."""
    WELCOME = "welcome"
    UPLOAD_DATABASE = "upload_database"
    MAIN_MENU = "main_menu"
    MAIN_MENU_PHONOLOGICAL = "main_menu_phonological"
    MAIN_MENU_ORTHOGRAPHY = "main_menu_orthography"
    MAIN_MENU_ACOUSTIC = "main_menu_acoustic"
    MAIN_MENU_COLLECT = "main_menu_collect"
    ORTHOGRAPHY_HUB = "orthography_hub"
    COLLECT_LEXICAL_DATA_HUB = "collect_lexical_data_hub"
    SCRIPT_CONVERTER = "script_converter"
    ABOUT = "about"
    TUTORIAL = "tutorial"
    # Task screens - add as needed
    TASK_PLACEHOLDER = "task_placeholder"
    TASK_CREATE_DATA_COLLECTION_SCRIPT = "task_create_data_collection_script"
    TASK_CREATE_PROMPTS_LIST = "task_create_prompts_list"
    TASK_ADD_AUDIO_LINKS = "task_add_audio_links"
    TASK_UPDATE_ENTRIES_FROM_WORDS = "task_update_entries_from_words"
    TASK_EXPLODE_ENTRIES = "task_explode_entries"
    TASK_SEGMENT_WORDS = "task_segment_words"
    TASK_GENERATE_CARDS = "task_generate_cards"
    TASK_PROCESS_CARDS = "task_process_cards"
    TASK_SORT_CARDS = "task_sort_cards"


def init_session_state():
    """Initialize all session state variables."""
    defaults = {
        "current_screen": Screen.WELCOME,
        "results": {},
        "task_history": [],
        # Database state
        "database": None,
        "database_validated": False,
        "database_filename": None,
        "database_sheet_name": None,
        # Main menu state
        "selected_task": None,
        # Analysis mode: "collect", "phonological", "orthography", or "acoustic"
        "analysis_mode": None,
        # Collection platform chosen on the Collect Lexical Data screen:
        # "speechrecorder" (PC/Mac) or "prompts" (Android)
        "collection_target": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def navigate_to(screen: str):
    """Navigate to a different screen."""
    st.session_state.current_screen = screen
    st.session_state._scroll_to_top = True
    st.rerun()


def go_back_to_menu():
    """Convenience function for returning to main menu."""
    mode = st.session_state.get("analysis_mode", "phonological")
    if mode == "acoustic":
        navigate_to(Screen.MAIN_MENU_ACOUSTIC)
    elif mode == "orthography":
        navigate_to(Screen.MAIN_MENU_ORTHOGRAPHY)
    elif mode == "collect":
        navigate_to(Screen.MAIN_MENU_COLLECT)
    else:
        navigate_to(Screen.MAIN_MENU_PHONOLOGICAL)


def render_scroll_to_top():
    """Render scroll-to-top script if flag is set."""
    if st.session_state.get("_scroll_to_top"):
        del st.session_state._scroll_to_top
        components.html(
            """
            <script>
            setTimeout(function() {
                window.parent.document.querySelector('[data-testid="stMain"]').scrollTo(0, 0);
            }, 100);
            </script>
            """,
            height=0,
        )
