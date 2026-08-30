"""
Excelerant UI
=============

Each module contains the screen-rendering function(s) for one task or one
group of closely related navigation screens. app.py stays a thin entrypoint
by importing everything it needs from this package, mirroring how app.py
already consumes tasks/ for business logic.
"""

from typing import Callable

import streamlit as st

from ui.navigation import Screen, init_session_state, navigate_to, go_back_to_menu, render_scroll_to_top
from ui.welcome import screen_welcome
from ui.info_pages import screen_about, screen_tutorial
from ui.upload_database import screen_upload_database
from ui.main_menus import (
    screen_orthography_hub,
    screen_collect_lexical_data_hub,
    screen_collect_platform,
    screen_main_menu_manage,
    screen_main_menu_phonological,
    screen_main_menu_orthography,
    screen_main_menu_acoustic,
    screen_main_menu_collect,
    screen_task_placeholder,
)
from ui.create_data_collection_script import screen_create_data_collection_script
from ui.create_prompts_list import screen_create_prompts_list
from ui.standard_word_lists import screen_standard_word_lists
from ui.add_audio_links import screen_add_audio_links
from ui.update_entries_from_words import screen_update_entries_from_words
from ui.explode_entries import screen_explode_entries
from ui.segment_words import screen_segment_words
from ui.script_converter import screen_script_converter
from ui.generate_cards import screen_generate_cards
from ui.process_cards import screen_process_cards
from ui.sort_cards import screen_sort_cards

SCREEN_FUNCTIONS: dict[str, Callable] = {
    Screen.WELCOME: screen_welcome,
    Screen.UPLOAD_DATABASE: screen_upload_database,
    Screen.MAIN_MENU: screen_main_menu_phonological,  # legacy fallback
    Screen.MAIN_MENU_PHONOLOGICAL: screen_main_menu_phonological,
    Screen.MAIN_MENU_ORTHOGRAPHY: screen_main_menu_orthography,
    Screen.MAIN_MENU_ACOUSTIC: screen_main_menu_acoustic,
    Screen.MAIN_MENU_COLLECT: screen_main_menu_collect,
    Screen.MAIN_MENU_MANAGE: screen_main_menu_manage,
    Screen.ORTHOGRAPHY_HUB: screen_orthography_hub,
    Screen.COLLECT_LEXICAL_DATA_HUB: screen_collect_lexical_data_hub,
    Screen.COLLECT_PLATFORM: screen_collect_platform,
    Screen.STANDARD_WORD_LISTS: screen_standard_word_lists,
    Screen.SCRIPT_CONVERTER: screen_script_converter,
    Screen.ABOUT: screen_about,
    Screen.TUTORIAL: screen_tutorial,
    Screen.TASK_PLACEHOLDER: screen_task_placeholder,
    Screen.TASK_CREATE_DATA_COLLECTION_SCRIPT: screen_create_data_collection_script,
    Screen.TASK_CREATE_PROMPTS_LIST: screen_create_prompts_list,
    Screen.TASK_ADD_AUDIO_LINKS: screen_add_audio_links,
    Screen.TASK_UPDATE_ENTRIES_FROM_WORDS: screen_update_entries_from_words,
    Screen.TASK_EXPLODE_ENTRIES: screen_explode_entries,
    Screen.TASK_SEGMENT_WORDS: screen_segment_words,
    Screen.TASK_GENERATE_CARDS: screen_generate_cards,
    Screen.TASK_PROCESS_CARDS: screen_process_cards,
    Screen.TASK_SORT_CARDS: screen_sort_cards,
}


def render_current_screen():
    """Render the current screen based on session state."""
    current = st.session_state.current_screen

    if current in SCREEN_FUNCTIONS:
        SCREEN_FUNCTIONS[current]()
    else:
        st.error(f"Unknown screen: {current}")
        if st.button("Return to Welcome"):
            navigate_to(Screen.WELCOME)


__all__ = [
    "Screen",
    "init_session_state",
    "render_current_screen",
    "render_scroll_to_top",
    "SCREEN_FUNCTIONS",
]
