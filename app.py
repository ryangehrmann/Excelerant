"""
Excelerant - Lexical Database Processing App
=============================================

Navigation Flow:
- Welcome Screen → Upload Database → Main Menu → Task Execution → Back to Main Menu

Layout Pattern:
- Left column: Task selection with categories
- Right column: Task information and "Begin" button
"""

import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import base64
from typing import Callable
from dataclasses import dataclass

# Import task logic
from tasks import (
    REQUIRED_COLUMNS,
    find_valid_sheets,
    load_sheet,
    validate_database,
    generate_script,
    get_windows_batch_file,
    get_mac_shell_script,
    parse_file_list,
    analyze_folder_structure,
    analyze_filenames,
    validate_delimiter_consistency,
    add_audio_links,
    export_database,
    reorder_columns,
    FORMATTING_REQUIRED_COLUMNS,
    detect_columns,
    check_database_formatting,
    ExplosionResult,
    explode_entries,
    SegmentationResult,
    segment_words,
    BLANK_SENTINEL,
    Card,
    CardBuildResult,
    get_column_filter_options,
    filter_dataframe,
    sort_dataframe,
    build_cards,
    generate_cards_html,
    build_sort_activity_filters,
    build_sort_activity_json,
    ProcessCardsResult,
    sanitize_activity_column_name,
    parse_uid_list,
    process_cards_manual,
    AI_ASSISTED_PROMPT,
    AIOutputParseResult,
    parse_ai_assisted_output,
)


# =============================================================================
# TASK DEFINITIONS
# =============================================================================

@dataclass
class TaskInfo:
    """Information about a task."""
    id: str
    name: str
    category: str
    description: str
    requirements: list[str]
    example: str
    youtube_url: str | None = None


# Define all tasks
TASKS = {
    # Configure Audio
    "create_data_collection_script": TaskInfo(
        id="create_data_collection_script",
        name="Create Data Collection Script",
        category="Configure Audio",
        description="Generate an XML script for [SpeechRecorder](https://www.bas.uni-muenchen.de/Bas/software/speechrecorder/) to collect audio recordings. Maps database columns to prompt fields (gloss, index, frame, extra info) and supports multiple token repetitions.",
        requirements=[
            "Database must have 'index' and 'gloss' columns populated",
            "Each index value must be unique",
        ],
        example="Input: Lexical database\nOutput: XML script for SpeechRecorder with prompts for each entry",
        youtube_url=None,
    ),
    "add_audio_links": TaskInfo(
        id="add_audio_links",
        name="Add Audio File Links to Database",
        category="Configure Audio",
        description="Link audio recordings to database entries by matching filenames to index values. Adds 'path' and 'link' columns for convenient audio access from Excel.",
        requirements=[
            "Audio files in .wav format",
            "Filenames must contain index numbers (e.g., '1.wav' or '1_speaker1_token1.wav')",
        ],
        example="Input: Audio folder + database\nOutput: Database with clickable 'link' and 'path' columns",
        youtube_url=None,
    ),
    
    # Configure Transcriptions
    "create_auto_transcriptions": TaskInfo(
        id="create_auto_transcriptions",
        name="Generate Draft Transcriptions with ASR",
        category="Configure Transcriptions",
        description="Generate automatic phonetic transcriptions using speech recognition models. Results can be reviewed and corrected manually.",
        requirements=[
            "Audio files must be linked to database",
            "Requires internet connection for API-based transcription",
        ],
        example="Input: Audio files\nOutput: IPA transcriptions in 'transcription' column",
        youtube_url=None,
    ),
    "convert_orthography_to_ipa": TaskInfo(
        id="convert_orthography_to_ipa",
        name="Convert Orthographic Transcription to IPA",
        category="Configure Transcriptions",
        description="Convert practical orthography to IPA using customizable conversion rules. Define your own grapheme-to-phoneme mappings.",
        requirements=[
            "Entries must use consistent orthographic conventions",
            "Conversion rules file (or create one interactively)",
        ],
        example="Input: 'káːw' → Output: '/káːw/' (with custom rules)",
        youtube_url=None,
    ),
    "explode_entries": TaskInfo(
        id="explode_entries",
        name="Explode Entries",
        category="Configure Transcriptions",
        description="Split multi-word entries into one-word-per-row. Adds 'sub_index' (word position) and 'word' columns. Cleans whitespace and punctuation from entry transcriptions before splitting.",
        requirements=[
            "Database must have 'index' and 'entry' columns",
            "Entries with multiple words separated by spaces",
        ],
        example="Input: 'big house' (1 row)\nOutput: 'big', 'house' (2 rows with sub_index 1, 2)",
        youtube_url=None,
    ),
    "segment_words": TaskInfo(
        id="segment_words",
        name="Segment Words",
        category="Configure Transcriptions",
        description="Break IPA-transcribed words into phonological columns: P (presyllable onset), R (presyllable rime), C (onset), M (medial), V (vowel), F (coda), T (tone/register). Non-IPA words are marked as errors without blocking.",
        requirements=[
            "Database must have a 'word' column with IPA transcriptions",
            "Run 'Explode Entries' first if entries contain multiple words",
        ],
        example="Input: 'kʰaːw¹'\nOutput: C='kʰ', V='aː', F='w', T='1'",
        youtube_url=None,
    ),
    "update_entries_from_words": TaskInfo(
        id="update_entries_from_words",
        name="Check Database Formatting & Update Entries",
        category="Configure Transcriptions",
        description="Validate database formatting and reconstruct entries from words. Checks for proper data types, unique index+sub_index pairs, sequential sub_indices, and rebuilds entries by joining words in order.",
        requirements=[
            "Database must have 'index', 'sub_index', 'entry', 'gloss', and 'word' columns",
            "Each index+sub_index combination must be unique",
            "Sub_indices must be sequential within each index (auto-fixed if possible)",
        ],
        example="Input: Words with sub_indices\nOutput: Validated data with reconstructed entries",
        youtube_url=None,
    ),
    
    # Phonological Analysis
    "generate_phoneme_charts": TaskInfo(
        id="generate_phoneme_charts",
        name="Generate Phoneme Charts",
        category="Phonological Analysis",
        description="Create consonant and vowel charts showing the phoneme inventory of the language based on your transcribed data.",
        requirements=[
            "IPA transcriptions in database",
            "Segmented words recommended for accuracy",
        ],
        example="Output: IPA consonant chart (place × manner) and vowel trapezoid",
        youtube_url=None,
    ),
    "generate_contrast_examples": TaskInfo(
        id="generate_contrast_examples",
        name="Generate Examples of Contrast",
        category="Phonological Analysis",
        description="Find minimal pairs and near-minimal pairs that demonstrate phonemic contrasts. Essential for phonological argumentation.",
        requirements=[
            "IPA transcriptions in database",
            "Sufficient lexical entries (100+ recommended)",
        ],
        example="Input: Phoneme pair /p/ vs /b/\nOutput: 'pat' [pat] vs 'bat' [bat]",
        youtube_url=None,
    ),
    
    # Orthography Development
    "generate_cards": TaskInfo(
        id="generate_cards",
        name="Generate Cards",
        category="Orthography Development",
        description="Generate cards for orthography-development card-sorting activities. Filter your database down to the rows you want, pick which columns appear on each card, and export either a printable Letter-size HTML deck (10 cards/page, Lao- and IPA-aware fonts) for physical sorting, or a prepared-activity JSON to hand off for digital/asynchronous sorting in Sort Cards.",
        requirements=[
            "Database must have an 'index' column (a 'sub_index' column is used automatically if present)",
            "Each index (or index + sub_index) among the rows you export must be unique",
        ],
        example="Input: Lexical database\nOutput: Printable HTML card deck and/or a Sort Cards activity JSON",
        youtube_url=None,
    ),
    "process_cards": TaskInfo(
        id="process_cards",
        name="Process Cards",
        category="Orthography Development",
        description="Record the results of a card-sorting activity back into the database. Name the activity, then create a category for each pile the cards were sorted into and supply the UID (from the bottom-right of each card) for every card in that pile -- typed in by hand or read from photos by AI. A new column is added to the database with the category label on each matching row.",
        requirements=[
            "Database must have an 'index' column (a 'sub_index' column is used automatically if present)",
            "Cards must have been generated with 'Generate Cards' using the same index/sub-index columns, so the UIDs on the cards match the database",
        ],
        example="Input: Category 'i' -> UIDs 4, 9, 22.1\nOutput: Rows 4, 9, and 22.1 get 'i' in the new activity column",
        youtube_url=None,
    ),

    # Acoustic Phonetic Analysis
    "force_align_textgrids": TaskInfo(
        id="force_align_textgrids",
        name="Generate Draft TextGrids with Forced Alignment",
        category="Acoustic Phonetic Analysis",
        description="Automatically align transcriptions to audio using forced alignment. Creates Praat TextGrids with word and phone boundaries.",
        requirements=[
            "Audio files linked to database",
            "IPA transcriptions for each entry",
            "Montreal Forced Aligner or similar tool configured",
        ],
        example="Input: Audio + transcription\nOutput: TextGrid with time-aligned segments",
        youtube_url=None,
    ),
    "extract_acoustic_measurements": TaskInfo(
        id="extract_acoustic_measurements",
        name="Extract Acoustic Data",
        category="Acoustic Phonetic Analysis",
        description="Extract acoustic features like F0, formants, duration, and intensity from aligned audio segments.",
        requirements=[
            "Force-aligned TextGrids",
            "Audio files in .wav format",
        ],
        example="Output: CSV with F1, F2, F3, duration, f0 for each segment",
        youtube_url=None,
    ),
    "generate_plots": TaskInfo(
        id="generate_plots",
        name="Generate Plots",
        category="Acoustic Phonetic Analysis",
        description="Create publication-ready visualizations: vowel plots, f0 contours, spectrograms, and more.",
        requirements=[
            "Acoustic measurements extracted",
        ],
        example="Output: Vowel space plot, f0 trajectory plots, formant tracks",
        youtube_url=None,
    ),
    "statistical_analysis": TaskInfo(
        id="statistical_analysis",
        name="Statistical Analysis",
        category="Acoustic Phonetic Analysis",
        description="Run statistical tests on acoustic data: t-tests, ANOVA, mixed-effects models for phonetic comparisons.",
        requirements=[
            "Acoustic measurements extracted",
            "Sufficient tokens per category (10+ recommended)",
        ],
        example="Output: Statistical summary, p-values, effect sizes, model outputs",
        youtube_url=None,
    ),
}

# Group tasks by category (preserving order)
TASK_CATEGORIES = [
    "Configure Audio",
    "Configure Transcriptions",
    "Phonological Analysis",
    "Orthography Development",
    "Acoustic Phonetic Analysis",
]

# Tasks that are currently implemented and enabled
ENABLED_TASKS = {
    "create_data_collection_script",
    "add_audio_links",
    "explode_entries",
    "segment_words",
    "update_entries_from_words",
    "generate_cards",
    "process_cards",
}

# Which task categories appear on each analysis mode's main menu.
# (Tasks are filtered by both ENABLED_TASKS and this mapping, so a task
# belongs on exactly the menu(s) for its category.)
MENU_CATEGORIES = {
    "phonological": ["Configure Audio", "Configure Transcriptions", "Phonological Analysis"],
    "orthography": ["Orthography Development"],
    "acoustic": ["Acoustic Phonetic Analysis"],
}


# =============================================================================
# NAVIGATION STATE
# =============================================================================

class Screen:
    """All possible screens in the app (string constants)."""
    WELCOME = "welcome"
    UPLOAD_DATABASE = "upload_database"
    MAIN_MENU = "main_menu"
    MAIN_MENU_PHONOLOGICAL = "main_menu_phonological"
    MAIN_MENU_ORTHOGRAPHY = "main_menu_orthography"
    MAIN_MENU_ACOUSTIC = "main_menu_acoustic"
    ABOUT = "about"
    TUTORIAL = "tutorial"
    # Task screens - add as needed
    TASK_PLACEHOLDER = "task_placeholder"
    TASK_CREATE_DATA_COLLECTION_SCRIPT = "task_create_data_collection_script"
    TASK_ADD_AUDIO_LINKS = "task_add_audio_links"
    TASK_UPDATE_ENTRIES_FROM_WORDS = "task_update_entries_from_words"
    TASK_EXPLODE_ENTRIES = "task_explode_entries"
    TASK_SEGMENT_WORDS = "task_segment_words"
    TASK_GENERATE_CARDS = "task_generate_cards"
    TASK_PROCESS_CARDS = "task_process_cards"


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
        # Analysis mode: "phonological" or "acoustic"
        "analysis_mode": None,
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
    else:
        navigate_to(Screen.MAIN_MENU_PHONOLOGICAL)


def has_valid_database() -> bool:
    """Check if a validated database is loaded."""
    return (
        st.session_state.database is not None 
        and st.session_state.database_validated
    )


# =============================================================================
# SCREEN DEFINITIONS
# =============================================================================

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
                navigate_to(Screen.UPLOAD_DATABASE)

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


def screen_upload_database():
    """Database upload and validation screen."""
    
    # Add vertical divider CSS for this screen
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
    
    st.title("Upload Lexical Database")
    st.markdown("---")
    
    # Two-column layout (1/3 left, 2/3 right) - matching main menu
    config_col, right_col = st.columns([1, 2])
    
    with config_col:
        st.subheader("Upload")
        
        uploaded_file = st.file_uploader(
            "Select your spreadsheet file",
            type=["xlsx", "xls", "ods"],
            help="Supported formats: .xlsx, .xls, .ods"
        )
        
        if uploaded_file is not None:
            # Find valid sheets
            valid_sheets = find_valid_sheets(uploaded_file)
            
            if len(valid_sheets) == 0:
                st.error(
                    """
                    **No valid sheets found.**
                    
                    Your spreadsheet must have at least one sheet with these columns:
                    - `index`
                    - `entry`
                    - `gloss`
                    
                    Please edit your file and re-upload.
                    """
                )
            
            elif len(valid_sheets) == 1:
                # Auto-select the only valid sheet
                sheet_name = valid_sheets[0]
                st.success(f"Found valid sheet: **{sheet_name}**")
                
                result = load_sheet(uploaded_file, sheet_name)
                
                if not result.success:
                    st.error(f"Error loading sheet: {result.error}")
                else:
                    df = result.df
                    st.session_state._temp_df = df
                    st.session_state._temp_filename = uploaded_file.name
                    st.session_state._temp_sheet = sheet_name
                    
                    st.markdown(f"**Rows:** {len(df):,} · **Columns:** {len(df.columns)}")
                    
                    # Validate the data
                    validation = validate_database(df)
                    
                    if not validation.valid:
                        st.error("**Validation errors found.**")

                        for col_name, issues in validation.errors.items():
                            with st.expander(f"Issues in '{col_name}' column ({len(issues)} errors)", expanded=True):
                                if col_name == "index":
                                    st.markdown("All values in the `index` column must be integers.")
                                else:
                                    st.markdown(f"All values in the `{col_name}` column must be non-empty strings.")

                                st.markdown("**Problematic rows:**")
                                for issue in issues[:20]:  # Show max 20
                                    st.text(f"  {issue}")
                                if len(issues) > 20:
                                    st.text(f"  ... and {len(issues) - 20} more")

                        st.markdown("---")
                        st.info("Please fix these issues in your Excel file, then upload the corrected file above.")
                    else:
                        st.success("Data validation passed")

                        st.markdown("---")

                        if st.button("Load Database", type="primary", use_container_width=True):
                            st.session_state.database = df
                            st.session_state.database_validated = True
                            st.session_state.database_filename = uploaded_file.name
                            st.session_state.database_sheet_name = sheet_name
                            
                            # Clean up temp state
                            for key in ["_temp_df", "_temp_filename", "_temp_sheet"]:
                                if key in st.session_state:
                                    del st.session_state[key]
                            
                            st.success("Database loaded!")
                            go_back_to_menu()
            
            else:
                # Multiple valid sheets - user must choose
                st.info(f"Found {len(valid_sheets)} sheets with required columns. Please select one:")

                # Add placeholder option
                sheet_options = ["- Select a sheet -"] + valid_sheets

                selected_sheet = st.selectbox(
                    "Select sheet",
                    options=sheet_options,
                    index=0,
                    help="Choose the sheet containing your lexical data"
                )

                # Only validate if user has selected a real sheet (not placeholder)
                if selected_sheet != "- Select a sheet -":
                    result = load_sheet(uploaded_file, selected_sheet)

                    if not result.success:
                        st.error(f"Error loading sheet: {result.error}")
                    else:
                        df = result.df
                        st.session_state._temp_df = df
                        st.session_state._temp_filename = uploaded_file.name
                        st.session_state._temp_sheet = selected_sheet

                        st.markdown(f"**Rows:** {len(df):,} · **Columns:** {len(df.columns)}")

                        # Validate the data
                        validation = validate_database(df)

                        if not validation.valid:
                            st.error("**Validation errors found.**")

                            for col_name, issues in validation.errors.items():
                                with st.expander(f"Issues in '{col_name}' column ({len(issues)} errors)", expanded=True):
                                    if col_name == "index":
                                        st.markdown("All values in the `index` column must be integers.")
                                    else:
                                        st.markdown(f"All values in the `{col_name}` column must be non-empty strings.")

                                    st.markdown("**Problematic rows:**")
                                    for issue in issues[:20]:  # Show max 20
                                        st.text(f"  {issue}")
                                    if len(issues) > 20:
                                        st.text(f"  ... and {len(issues) - 20} more")

                            st.markdown("---")
                            st.info("Please fix these issues in your Excel file, then upload the corrected file above.")
                        else:
                            st.success("Data validation passed")

                            st.markdown("---")

                            if st.button("Load Database", type="primary", use_container_width=True):
                                st.session_state.database = df
                                st.session_state.database_validated = True
                                st.session_state.database_filename = uploaded_file.name
                                st.session_state.database_sheet_name = selected_sheet

                                # Clean up temp state
                                for key in ["_temp_df", "_temp_filename", "_temp_sheet"]:
                                    if key in st.session_state:
                                        del st.session_state[key]

                                st.success("Database loaded!")
                                go_back_to_menu()
        
        st.markdown("---")
        
        if st.button("Back to Welcome"):
            navigate_to(Screen.WELCOME)
    
    with right_col:
        st.subheader("Information")
        
        if uploaded_file is None:
            st.info(
                """
                **Required Format:**
                
                Your spreadsheet must contain at least one sheet with these columns:
                
                | index | entry | gloss |
                |-------|-------|-------|
                | 1 | word1 | meaning1 |
                | 2 | word2 | meaning2 |
                
                Additional columns are allowed and will be preserved.
                
                **Supported file types:**
                - Excel (.xlsx, .xls)
                - OpenDocument (.ods)
                """
            )
        elif "_temp_df" in st.session_state:
            df = st.session_state._temp_df
            
            st.markdown(f"**File:** `{st.session_state._temp_filename}`")
            st.markdown(f"**Sheet:** `{st.session_state._temp_sheet}`")
            
            st.markdown("---")
            
            with st.expander("Columns", expanded=False):
                for col in df.columns:
                    marker = "*" if col in REQUIRED_COLUMNS else "-"
                    st.text(f"{marker} {col}")
            
            with st.expander("Data Preview", expanded=True):
                st.dataframe(df.head(10), use_container_width=True, height=300)


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
                    st.text(f"\u2022 {col}")

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
                        "add_audio_links": Screen.TASK_ADD_AUDIO_LINKS,
                        "update_entries_from_words": Screen.TASK_UPDATE_ENTRIES_FROM_WORDS,
                        "explode_entries": Screen.TASK_EXPLODE_ENTRIES,
                        "segment_words": Screen.TASK_SEGMENT_WORDS,
                        "generate_cards": Screen.TASK_GENERATE_CARDS,
                        "process_cards": Screen.TASK_PROCESS_CARDS,
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


def screen_create_data_collection_script():
    """Screen for creating SpeechRecorder data collection scripts."""

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

    st.title("Create Data Collection Script")
    st.markdown("---")

    # Two-column layout
    config_col, output_col = st.columns([1, 2])

    df = st.session_state.database
    columns = list(df.columns)

    # Build column options with "-none-" for optional fields
    optional_columns = ["-none-"] + columns

    with config_col:
        st.subheader("Column Mapping")

        # Required columns
        st.markdown("**Required**")

        # Index column - default to "index"
        index_default = columns.index("index") if "index" in columns else 0
        index_col = st.selectbox(
            "Index column",
            options=columns,
            index=index_default,
            help="Column containing unique index numbers for each entry",
        )

        # Primary gloss column - default to "gloss"
        gloss_default = columns.index("gloss") if "gloss" in columns else 0
        primary_gloss_col = st.selectbox(
            "Primary gloss column",
            options=columns,
            index=gloss_default,
            help="Column containing the main gloss/meaning shown in prompts",
        )

        st.markdown("")
        st.markdown("**Optional**")

        # Secondary gloss column
        secondary_gloss_col = st.selectbox(
            "Secondary gloss column",
            options=optional_columns,
            index=0,
            help="Additional gloss information (e.g., vernacular gloss)",
        )

        # Extra column
        extra_col = st.selectbox(
            "Extra information column",
            options=optional_columns,
            index=0,
            help="Any additional information to show in prompts",
        )

        st.markdown("---")
        st.subheader("Token Repetition")

        st.markdown(
            "How many times should each item be recorded? "
            "Multiple tokens allow for repetition analysis."
        )

        num_tokens = st.number_input(
            "Number of tokens",
            min_value=1,
            max_value=9,
            value=1,
            step=1,
            format="%d",
        )

        st.markdown("---")
        st.subheader("Sentence Frames")

        using_frames = st.selectbox(
            "Use sentence frames?",
            options=["No", "Yes"],
            index=0,
            help="Include a carrier sentence/frame in prompts",
        )

        frame_col = None
        tokens_in_frame = []

        if using_frames == "Yes":
            frame_col = st.selectbox(
                "Frame column",
                options=columns,
                index=0,
                help="Column containing the sentence frame",
            )

            if num_tokens > 1:
                all_in_frame = st.selectbox(
                    "Apply frame to all tokens?",
                    options=["Yes", "No"],
                    index=0,
                )

                if all_in_frame == "Yes":
                    tokens_in_frame = list(range(1, num_tokens + 1))
                else:
                    tokens_in_frame = st.multiselect(
                        "Select which tokens use the frame",
                        options=list(range(1, num_tokens + 1)),
                        default=[1],
                    )
            else:
                tokens_in_frame = [1]

        st.markdown("---")

        generate_clicked = st.button(
            "Generate Script",
            type="primary",
            use_container_width=True,
        )

        st.markdown("")

        if st.button("Back to Main Menu", use_container_width=True):
            go_back_to_menu()

    with output_col:
        st.subheader("Output")

        if generate_clicked:
            # Convert "-none-" selections to None
            sec_gloss = None if secondary_gloss_col == "-none-" else secondary_gloss_col
            extra = None if extra_col == "-none-" else extra_col
            frame = frame_col if using_frames == "Yes" else None

            with st.spinner("Generating XML script..."):
                result = generate_script(
                    df=df,
                    index_col=index_col,
                    primary_gloss_col=primary_gloss_col,
                    secondary_gloss_col=sec_gloss,
                    frame_col=frame,
                    extra_col=extra,
                    num_tokens=num_tokens,
                    tokens_in_frame=tokens_in_frame,
                )

            if not result.success:
                st.error(f"**Error:** {result.error}")

                st.markdown("---")

                if st.button("Clear Database & Start Over", type="primary", use_container_width=True):
                    if "_generated_script" in st.session_state:
                        del st.session_state._generated_script
                    st.session_state.database = None
                    st.session_state.database_validated = False
                    st.session_state.database_filename = None
                    st.session_state.database_sheet_name = None
                    st.session_state.selected_task = None
                    navigate_to(Screen.UPLOAD_DATABASE)
            else:
                # Store result in session state and rerun to scroll to top
                st.session_state._generated_script = result.script
                st.session_state._scroll_to_top = True
                st.rerun()

        # Display script if available
        if "_generated_script" in st.session_state and st.session_state._generated_script:
            st.success("Script generated successfully!")

            st.markdown(
                """
                **Instructions:**

                1. Click **Copy to Clipboard** below
                2. Open [SpeechRecorder](https://www.bas.uni-muenchen.de/Bas/software/speechrecorder/)
                3. Open your project or start a new one
                4. Go to **Script > Edit Script XML Source**
                5. Delete existing content
                6. Paste the code
                7. Press OK
                8. You're ready to record!

                *Note: Large scripts may cause SpeechRecorder to pause briefly while loading.*
                """
            )

            st.markdown("")

            # Buttons row: Copy to Clipboard (green) | Return to Main Menu
            btn_col1, btn_col2 = st.columns(2)

            with btn_col1:
                # Encode script as base64 to avoid escaping issues
                script_b64 = base64.b64encode(
                    st.session_state._generated_script.encode('utf-8')
                ).decode('utf-8')

                components.html(
                    f"""
                    <script>
                    function copyScript() {{
                        const text = atob("{script_b64}");
                        navigator.clipboard.writeText(text).then(function() {{
                            document.getElementById('copyBtn').innerText = 'Copied!';
                            document.getElementById('copyBtn').style.backgroundColor = '#1B5E20';
                            setTimeout(function() {{
                                document.getElementById('copyBtn').innerText = 'Copy XML Script to Clipboard';
                                document.getElementById('copyBtn').style.backgroundColor = '#2E7D32';
                            }}, 2000);
                        }});
                    }}
                    </script>
                    <button id="copyBtn" onclick="copyScript()" style="
                        background-color: #2E7D32;
                        color: white;
                        border: none;
                        border-radius: 0.5rem;
                        padding: 0.6rem 1rem;
                        font-size: 16px;
                        font-weight: 500;
                        cursor: pointer;
                        width: 100%;
                    ">Copy XML Script to Clipboard</button>
                    """,
                    height=45,
                )

            with btn_col2:
                if st.button("Return to Main Menu", use_container_width=True):
                    # Clear the generated script when returning
                    if "_generated_script" in st.session_state:
                        del st.session_state._generated_script
                    go_back_to_menu()

            st.markdown("---")

            st.markdown("**Generated XML:**")
            st.code(st.session_state._generated_script, language="xml")
        else:
            st.info(
                "Configure your column mappings and settings in the left panel, "
                "then click **Generate Script** to create your XML."
            )

            st.markdown("---")

            st.markdown("**About SpeechRecorder Scripts**")
            st.markdown(
                """
                This task generates XML scripts for
                [SpeechRecorder](http://www.speechrecorder.org/),
                a tool for collecting speech recordings.

                The script will contain prompts for each entry in your database,
                showing:
                - Primary gloss (the main meaning/translation)
                - Index number with optional secondary gloss
                - Sentence frame (if configured)
                - Extra information (if configured)

                Each prompt element is separated by a visual divider (`---`).
                """
            )


def screen_add_audio_links():
    """Screen for adding audio file links to database."""

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

    st.title("Add Audio File Links")
    st.markdown("---")

    # Two-column layout
    config_col, output_col = st.columns([1, 2])

    df = st.session_state.database
    columns = list(df.columns)

    with config_col:
        # === SECTION 1: Platform & Analysis Mode ===
        st.subheader("Configuration")

        st.markdown("**Required Settings**")

        platform = st.selectbox(
            "Operating system",
            options=["Windows", "Mac"],
            index=0,
            help="Determines file generator type and link format",
        )
        platform_key = platform.lower()

        analysis_mode = st.selectbox(
            "Analysis type",
            options=["Phonological Analysis", "Acoustic Phonetic Analysis"],
            index=0,
            help="Phonological: one audio per index. Acoustic: one row per audio file.",
        )
        analysis_key = "phonological" if "Phonological" in analysis_mode else "acoustic"

        # === SECTION 2: File List Generator ===
        st.markdown("---")
        st.subheader("Step 1: Get File List")

        if platform_key == "windows":
            st.markdown(
                """
                **Instructions:**
                1. Click **Download** below to get the file list generator
                2. Double-click the downloaded `.bat` file
                3. Drag your audio folder into the window and press Enter
                4. Upload the generated `filelist.txt` in Step 2
                """
            )
            st.download_button(
                label="Download File List Generator (.bat)",
                data=get_windows_batch_file(),
                file_name="File List Generator.bat",
                mime="application/octet-stream",
                use_container_width=True,
            )
        else:
            st.markdown(
                """
                **Instructions:**
                1. Click **Download** below to get the file list generator
                2. Open Terminal and navigate to your Downloads folder:
                   `cd ~/Downloads`
                3. Make the script executable:
                   `chmod +x "File List Generator.sh"`
                4. Run the script:
                   `bash "File List Generator.sh"`
                5. Drag your audio folder into Terminal and press Enter
                6. Upload the generated `filelist.txt` in Step 2
                """
            )
            st.download_button(
                label="Download File List Generator (.sh)",
                data=get_mac_shell_script(),
                file_name="File List Generator.sh",
                mime="application/x-sh",
                use_container_width=True,
            )

        # === SECTION 3: Upload File List ===
        st.markdown("---")
        st.subheader("Step 2: Upload File List")

        uploaded_file = st.file_uploader(
            "Upload filelist.txt",
            type=["txt"],
            help="The file generated by the file list generator tool",
        )

        # Process uploaded file
        file_paths = None
        folder_analysis = None
        filename_analysis = None

        if uploaded_file is not None:
            content = uploaded_file.read().decode('utf-8')
            file_paths, parse_error = parse_file_list(content, platform_key)

            if parse_error:
                st.error(parse_error)
            else:
                st.success(f"Found {len(file_paths)} .wav files")

                # Analyze structure
                folder_analysis = analyze_folder_structure(file_paths, platform_key)
                filename_analysis = analyze_filenames(file_paths, platform_key)

                # Store in session state for use in output column
                st.session_state._audio_file_paths = file_paths
                st.session_state._folder_analysis = folder_analysis
                st.session_state._filename_analysis = filename_analysis

        # === SECTION 4: Column Mapping (only if file uploaded) ===
        if file_paths and folder_analysis and filename_analysis:
            if folder_analysis.error:
                st.error(folder_analysis.error)
            else:
                st.markdown("---")
                st.subheader("Step 3: Configure Mapping")

                # Index column
                index_default = columns.index("index") if "index" in columns else 0
                index_col = st.selectbox(
                    "Index column (required)",
                    options=columns,
                    index=index_default,
                    help="Database column containing index values to match with filenames",
                )

                # Subfolder category (if subfolders detected)
                subfolder_category = None
                if folder_analysis.has_subfolders:
                    st.markdown(f"**Subfolders detected:** {', '.join(folder_analysis.subfolder_names[:5])}"
                                + (f" ... and {len(folder_analysis.subfolder_names) - 5} more" if len(folder_analysis.subfolder_names) > 5 else ""))
                    subfolder_category = st.selectbox(
                        "What do subfolders represent?",
                        options=["-none-", "speaker", "token", "other"],
                        index=0,
                        help="If subfolders represent a category (e.g., speaker names), select it here",
                    )

                # Filename structure
                section_categories = None
                delimiter = filename_analysis.delimiter

                if filename_analysis.all_integers:
                    st.info(f"Filenames are index numbers (e.g., `{filename_analysis.example_filename}`). No additional mapping needed.")
                    section_categories = ["index"]
                elif filename_analysis.delimiter:
                    # Validate delimiter consistency
                    delim_error = validate_delimiter_consistency(file_paths, delimiter, platform_key)
                    if delim_error:
                        st.error(delim_error)
                    else:
                        st.markdown(f"**Filename structure detected:** `{filename_analysis.example_filename}`")
                        st.markdown(f"Delimiter: `{delimiter}` → {filename_analysis.num_sections} sections")

                        section_categories = []
                        for i, section in enumerate(filename_analysis.example_sections):
                            # Auto-detect index section (if it's all digits)
                            default_idx = 0  # -none-
                            if section.isdigit():
                                default_idx = 1  # index

                            cat = st.selectbox(
                                f"Section {i + 1}: `{section}`",
                                options=["-none-", "index", "speaker", "token", "other"],
                                index=default_idx,
                                key=f"section_cat_{i}",
                            )
                            section_categories.append(cat if cat != "-none-" else None)

                        # Validate that index is selected
                        if "index" not in section_categories:
                            st.warning("You must identify which section contains the index.")
                else:
                    st.info(f"Filenames will be treated as index values (e.g., `{filename_analysis.example_filename}`).")
                    section_categories = ["index"]

                st.markdown("---")

                # Generate button
                can_generate = (
                    file_paths and
                    not folder_analysis.error and
                    section_categories and
                    ("index" in section_categories if section_categories else False)
                )

                generate_clicked = st.button(
                    "Add Audio Links",
                    type="primary",
                    use_container_width=True,
                    disabled=not can_generate,
                )

                # Store generation parameters in session state for processing in output column
                if generate_clicked:
                    st.session_state._audio_generate_params = {
                        'file_paths': file_paths,
                        'platform': platform_key,
                        'analysis_mode': analysis_key,
                        'index_col': index_col,
                        'delimiter': delimiter,
                        'section_categories': section_categories,
                        'subfolder_category': subfolder_category if subfolder_category != "-none-" else None,
                    }
                    st.rerun()

        st.markdown("---")
        if st.button("Back to Main Menu", use_container_width=True):
            # Clean up session state
            for key in ["_audio_file_paths", "_folder_analysis", "_filename_analysis", "_audio_link_result", "_audio_link_platform", "_audio_generate_params"]:
                if key in st.session_state:
                    del st.session_state[key]
            go_back_to_menu()

    # === OUTPUT COLUMN ===
    with output_col:
        st.subheader("Output")

        # Process if generation was triggered (params stored in session state)
        if "_audio_generate_params" in st.session_state:
            params = st.session_state._audio_generate_params
            del st.session_state._audio_generate_params  # Clear params

            with st.spinner("Adding audio links..."):
                result = add_audio_links(
                    df=df,
                    file_paths=params['file_paths'],
                    platform=params['platform'],
                    analysis_mode=params['analysis_mode'],
                    index_col=params['index_col'],
                    delimiter=params['delimiter'],
                    section_categories=params['section_categories'],
                    subfolder_category=params['subfolder_category'],
                )

            if result.success:
                st.session_state._audio_link_result = result
                st.session_state._audio_link_platform = params['platform']
                st.session_state._scroll_to_top = True
                st.session_state.database = result.df
                st.session_state.database_validated = True
                st.rerun()
            else:
                st.error(f"**Error:** {result.error}")

                st.markdown("---")

                if st.button("Clear Database & Start Over", type="primary", use_container_width=True):
                    for key in ["_audio_file_paths", "_folder_analysis", "_filename_analysis", "_audio_link_result", "_audio_link_platform", "_audio_generate_params"]:
                        if key in st.session_state:
                            del st.session_state[key]
                    st.session_state.database = None
                    st.session_state.database_validated = False
                    st.session_state.database_filename = None
                    st.session_state.database_sheet_name = None
                    st.session_state.selected_task = None
                    navigate_to(Screen.UPLOAD_DATABASE)

        # Show result if available
        if "_audio_link_result" in st.session_state:
            result = st.session_state._audio_link_result

            st.success("Audio links added successfully!")

            st.markdown(f"""
            **Summary:**
            - Files matched: {result.files_matched}
            - Indices without audio: {result.files_unmatched}
            - Rows before: {result.rows_before}
            - Rows after: {result.rows_after}
            """)

            st.markdown("---")

            # Buttons row
            btn_col1, btn_col2 = st.columns(2)

            with btn_col1:
                # Download updated database with formatting
                platform = st.session_state.get('_audio_link_platform', 'windows')
                st.download_button(
                    label="Download Updated Database",
                    data=export_database(result.df, platform=platform),
                    file_name="database_with_audio.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    type="primary",
                    use_container_width=True,
                )

            with btn_col2:
                if st.button("Return to Main Menu", use_container_width=True, key="return_after_audio"):
                    for key in ["_audio_file_paths", "_folder_analysis", "_filename_analysis", "_audio_link_result", "_audio_link_platform", "_audio_generate_params"]:
                        if key in st.session_state:
                            del st.session_state[key]
                    go_back_to_menu()

            st.markdown("---")

            st.markdown("**Updated Database Preview:**")
            # Show key columns: index, gloss, then all link columns, then all path columns
            preview_cols = []

            # Add index and gloss first
            if 'index' in result.df.columns:
                preview_cols.append('index')
            if 'gloss' in result.df.columns:
                preview_cols.append('gloss')

            # Add all link columns (link, link_*)
            link_cols = sorted([c for c in result.df.columns if c == 'link' or c.startswith('link_')])
            preview_cols.extend(link_cols)

            # Add all path columns (path, path_*)
            path_cols = sorted([c for c in result.df.columns if c == 'path' or c.startswith('path_')])
            preview_cols.extend(path_cols)

            # Filter to only columns that exist
            available_cols = [c for c in preview_cols if c in result.df.columns]

            if available_cols:
                st.dataframe(result.df[available_cols].head(15), use_container_width=True)
            else:
                st.dataframe(result.df.head(15), use_container_width=True)

        # Show analysis info if file uploaded but not yet processed
        elif "_folder_analysis" in st.session_state:
            folder_analysis = st.session_state._folder_analysis
            filename_analysis = st.session_state._filename_analysis
            file_paths = st.session_state._audio_file_paths

            st.info("File list uploaded. Configure mapping and click **Add Audio Links**.")

            st.markdown("---")

            st.markdown("**Analysis Results:**")
            st.markdown(f"- Total .wav files: {folder_analysis.total_files}")
            st.markdown(f"- Subfolders: {'Yes' if folder_analysis.has_subfolders else 'No'}")
            if folder_analysis.has_subfolders:
                st.markdown(f"  - Names: {', '.join(folder_analysis.subfolder_names[:5])}" +
                            (f" ... +{len(folder_analysis.subfolder_names) - 5} more" if len(folder_analysis.subfolder_names) > 5 else ""))

            st.markdown(f"- Delimiter: `{filename_analysis.delimiter}`" if filename_analysis.delimiter else "- Delimiter: None")
            st.markdown(f"- Example: `{filename_analysis.example_filename}`")
            if filename_analysis.all_integers:
                st.markdown("- Structure: Index numbers only")
            elif filename_analysis.num_sections > 1:
                st.markdown(f"- Sections: {filename_analysis.num_sections} ({' | '.join(filename_analysis.example_sections)})")

        else:
            # Initial state - show instructions
            st.info("Download the file list generator, run it on your audio folder, then upload the result.")

            st.markdown("---")

            st.markdown("**About Audio Links**")
            st.markdown(
                """
                This task links your audio recordings to database entries by matching
                filenames to index values.

                **Two output modes:**

                - **Phonological Analysis**: One audio file per index. The same path
                  appears on all rows sharing that index (useful for compound entries).

                - **Acoustic Phonetic Analysis**: One row per audio file. The database
                  expands to have a separate row for each recording (useful for
                  analyzing multiple speakers/tokens).

                **Output columns:**
                - `path`: Full file path to the audio file
                - `link`: Clickable link (Excel on Windows) or terminal command (Mac)
                """
            )

            st.markdown("---")

            st.markdown("**Example (before):**")
            example_before = pd.DataFrame({
                'index': [1, 2, 3],
                'gloss': ['dog', 'wolf', 'cat'],
                'entry': ['maː', 'paː', 'kaː']
            })
            st.dataframe(example_before, use_container_width=True, hide_index=True)

            st.markdown("**Example (after):**")
            example_after = pd.DataFrame({
                'index': [1, 2, 3],
                'gloss': ['dog', 'wolf', 'cat'],
                'entry': ['maː', 'paː', 'kaː'],
                'link': ['listen', 'listen', 'listen'],
                'path': ['C:\\audio\\1.wav', 'C:\\audio\\2.wav', 'C:\\audio\\3.wav']
            })
            st.dataframe(example_after, use_container_width=True, hide_index=True)


def screen_update_entries_from_words():
    """Screen for checking database formatting and updating entries from words."""

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

    st.title("Check Database Formatting & Update Entries")
    st.markdown("---")

    # Two-column layout
    config_col, output_col = st.columns([1, 2])

    df = st.session_state.database
    columns = list(df.columns)

    with config_col:
        st.subheader("Column Detection")

        # Detect columns
        detection = detect_columns(df)

        if detection.success:
            st.success("All required columns found!")

            # Show detected columns
            st.markdown("**Detected columns:**")
            for req_col, actual_col in detection.column_mapping.items():
                if req_col == actual_col:
                    st.text(f"  {req_col}")
                else:
                    st.text(f"  {req_col} (from '{actual_col}')")

            if detection.normalized_columns:
                st.info(f"Column names will be normalized to lowercase: {', '.join(detection.normalized_columns)}")

            st.markdown("---")

            # Categorical columns selection
            st.markdown("**Additional Categorical Columns (Optional)**")
            st.caption(
                "If your data has multiple speakers or multiple tokens of the same word list item, "
                "select those columns here. They will be included in uniqueness checks and grouping."
            )

            # Get available columns (excluding required ones)
            available_cat_cols = [col for col in columns if col.lower() not in
                                  [r.lower() for r in FORMATTING_REQUIRED_COLUMNS]]

            categorical_columns = st.multiselect(
                "Select categorical columns",
                options=available_cat_cols,
                default=[],
                help="Columns like 'speaker', 'token', etc.",
                key="cat_cols_detected",
            )

            st.markdown("---")

            # Process button
            process_clicked = st.button(
                "Check Formatting & Update Entries",
                type="primary",
                use_container_width=True,
            )

            if process_clicked:
                st.session_state._formatting_check_params = {
                    "column_mapping": detection.column_mapping,
                    "categorical_columns": categorical_columns if categorical_columns else None,
                }
                st.rerun()

        else:
            st.warning(f"Missing required columns: {', '.join(detection.missing_columns)}")

            st.markdown("**Please map the missing columns:**")

            # Build column mapping with user input for missing columns
            user_mapping = {}

            for req_col in FORMATTING_REQUIRED_COLUMNS:
                if req_col in detection.column_mapping:
                    # Already found
                    actual_col = detection.column_mapping[req_col]
                    if req_col == actual_col:
                        st.text(f"  {req_col} - found")
                    else:
                        st.text(f"  {req_col} - found (as '{actual_col}')")
                    user_mapping[req_col] = actual_col
                else:
                    # Need user to select
                    selected = st.selectbox(
                        f"Select column for '{req_col}'",
                        options=["-none-"] + columns,
                        key=f"col_map_{req_col}",
                    )
                    if selected != "-none-":
                        user_mapping[req_col] = selected

            # Check if all columns are now mapped
            all_mapped = len(user_mapping) == len(FORMATTING_REQUIRED_COLUMNS)

            st.markdown("---")

            # Categorical columns selection
            st.markdown("**Additional Categorical Columns (Optional)**")
            st.caption(
                "If your data has multiple speakers or multiple tokens of the same word list item, "
                "select those columns here. They will be included in uniqueness checks and grouping."
            )

            # Get available columns (excluding required ones and already mapped ones)
            mapped_cols = set(user_mapping.values())
            available_cat_cols = [col for col in columns if col not in mapped_cols and
                                  col.lower() not in [r.lower() for r in FORMATTING_REQUIRED_COLUMNS]]

            categorical_columns = st.multiselect(
                "Select categorical columns",
                options=available_cat_cols,
                default=[],
                help="Columns like 'speaker', 'token', etc.",
                key="cat_cols_manual",
            )

            st.markdown("---")

            process_clicked = st.button(
                "Check Formatting & Update Entries",
                type="primary",
                use_container_width=True,
                disabled=not all_mapped,
            )

            if not all_mapped:
                st.caption("Please select a column for each required field.")

            if process_clicked and all_mapped:
                st.session_state._formatting_check_params = {
                    "column_mapping": user_mapping,
                    "categorical_columns": categorical_columns if categorical_columns else None,
                }
                st.rerun()

        st.markdown("---")

        if st.button("Back to Main Menu", use_container_width=True):
            # Clean up session state
            for key in ["_formatting_check_params", "_formatting_check_result"]:
                if key in st.session_state:
                    del st.session_state[key]
            go_back_to_menu()

    # === OUTPUT COLUMN ===
    with output_col:
        st.subheader("Output")

        # Process if triggered
        if "_formatting_check_params" in st.session_state:
            params = st.session_state._formatting_check_params
            del st.session_state._formatting_check_params

            with st.spinner("Checking database formatting..."):
                result = check_database_formatting(
                    df=df,
                    column_mapping=params["column_mapping"],
                    categorical_columns=params.get("categorical_columns"),
                )

            if result.success:
                st.session_state._formatting_check_result = result
                st.session_state._scroll_to_top = True
                st.session_state.database = result.df
                st.session_state.database_validated = True
                st.rerun()
            else:
                # Store error result for display
                st.session_state._formatting_check_result = result
                st.rerun()

        # Display result if available
        if "_formatting_check_result" in st.session_state:
            result = st.session_state._formatting_check_result

            if result.success:
                st.success("Database formatting validated and entries updated!")

                # Show summary
                cat_cols = result.summary.get('categorical_columns', [])
                cat_cols_text = f"- Categorical columns: {', '.join(cat_cols)}" if cat_cols else ""

                summary_text = f"""
                **Summary:**
                - Total rows: {result.summary.get('total_rows', 'N/A')}
                - Unique indices: {result.summary.get('unique_indices', 'N/A')}
                - Auto-fixes applied: {result.summary.get('auto_fixes_count', 0)}
                """
                if cat_cols_text:
                    summary_text += f"\n                {cat_cols_text}"

                st.markdown(summary_text)

                # Show auto-fixes if any
                if result.auto_fixes_applied:
                    with st.expander("Auto-fixes applied", expanded=False):
                        st.markdown(
                            "The following sub_index sequences were renumbered to start at 1:"
                        )
                        for fix in result.auto_fixes_applied[:20]:
                            st.text(f"  {fix}")
                        if len(result.auto_fixes_applied) > 20:
                            st.text(f"  ... and {len(result.auto_fixes_applied) - 20} more")

                st.markdown("---")

                # Buttons row
                btn_col1, btn_col2 = st.columns(2)

                with btn_col1:
                    # Download updated database
                    st.download_button(
                        label="Download Updated Database",
                        data=export_database(result.df),
                        file_name="database_formatted.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        type="primary",
                        use_container_width=True,
                    )

                with btn_col2:
                    if st.button("Return to Main Menu", use_container_width=True, key="return_after_format"):
                        for key in ["_formatting_check_params", "_formatting_check_result"]:
                            if key in st.session_state:
                                del st.session_state[key]
                        go_back_to_menu()

                st.markdown("---")

                st.markdown("**Updated Database Preview:**")
                # Show key columns: index, sub_index, word, entry_orig, entry, gloss
                preview_cols = []
                col_priority = ['index', 'sub_index', 'word', 'entry_orig', 'entry', 'gloss']
                for col in col_priority:
                    if col in result.df.columns:
                        preview_cols.append(col)

                if preview_cols:
                    st.dataframe(result.df[preview_cols].head(20), use_container_width=True)
                else:
                    st.dataframe(result.df.head(20), use_container_width=True)

            else:
                # Show error
                error = result.error

                st.error(f"**Validation Error:** {error.message}")

                st.markdown("---")

                st.markdown("**Details:**")
                for detail in error.details:
                    st.text(f"  {detail}")

                st.markdown("---")

                st.markdown("**Recommendation:**")
                st.info(error.recommendation)

                st.markdown("---")

                if st.button("Clear Database & Start Over", type="primary", use_container_width=True):
                    # Clean up session state
                    for key in ["_formatting_check_params", "_formatting_check_result"]:
                        if key in st.session_state:
                            del st.session_state[key]
                    st.session_state.database = None
                    st.session_state.database_validated = False
                    st.session_state.database_filename = None
                    st.session_state.database_sheet_name = None
                    st.session_state.selected_task = None
                    navigate_to(Screen.UPLOAD_DATABASE)

        else:
            # Initial state - show instructions
            st.info("Click **Check Formatting & Update Entries** to validate your database and reconstruct entries from words.")

            st.markdown("---")

            st.markdown("**About This Task**")
            st.markdown(
                """
                This task validates your database formatting and reconstructs entries from individual words.

                **Validation checks:**
                - No blank values in index, sub_index, entry, or word columns
                - Index values must be integers
                - Sub_index values must be integers
                - Entry and word values must be strings
                - Each index + sub_index (+ categorical columns) combination must be unique
                - Sub_indices must be sequential (1, 2, 3...) within each group

                **Categorical columns:**
                If your data has multiple speakers or multiple tokens of the same word list item,
                select those columns. They will be included in uniqueness checks and used for
                grouping when reconstructing entries.

                **Auto-fix:**
                If sub_indices are unique but don't start at 1 or have gaps, they will be
                automatically renumbered (e.g., 3, 5, 7 becomes 1, 2, 3).

                **Output:**
                - Original 'entry' column is preserved as 'entry_orig'
                - New 'entry' column is created by joining words in sub_index order per group
                """
            )

            st.markdown("---")

            st.markdown("**Example:**")

            example_before = pd.DataFrame({
                'index': [1, 1, 1, 2, 2],
                'sub_index': [1, 2, 3, 1, 2],
                'word': ['the', 'big', 'dog', 'a', 'cat'],
                'entry': ['the big dog', 'the big dog', 'the big dog', 'a cat', 'a cat'],
                'gloss': ['animal', 'animal', 'animal', 'animal', 'animal'],
            })
            st.markdown("**Before:**")
            st.dataframe(example_before, use_container_width=True, hide_index=True)

            example_after = pd.DataFrame({
                'index': [1, 1, 1, 2, 2],
                'sub_index': [1, 2, 3, 1, 2],
                'word': ['the', 'big', 'dog', 'a', 'cat'],
                'entry_orig': ['the big dog', 'the big dog', 'the big dog', 'a cat', 'a cat'],
                'entry': ['the big dog', 'the big dog', 'the big dog', 'a cat', 'a cat'],
                'gloss': ['animal', 'animal', 'animal', 'animal', 'animal'],
            })
            st.markdown("**After (entry reconstructed from words):**")
            st.dataframe(example_after[['index', 'sub_index', 'word', 'entry_orig', 'entry']], use_container_width=True, hide_index=True)


def screen_explode_entries():
    """Screen for splitting multi-word entries into one-word-per-row."""

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

    st.title("Explode Entries")
    st.markdown("---")

    # Two-column layout
    config_col, output_col = st.columns([1, 2])

    df = st.session_state.database
    columns = list(df.columns)

    with config_col:
        st.subheader("Configuration")

        # Auto-detect entry column (case-insensitive)
        entry_col = None
        for col in columns:
            if col.lower() == 'entry':
                entry_col = col
                break

        if entry_col:
            st.success(f"Entry column detected: **{entry_col}**")
        else:
            entry_col = st.selectbox(
                "Select entry column",
                options=columns,
                help="Column containing multi-word transcriptions to split",
            )

        # Auto-detect gloss column
        gloss_col = None
        for col in columns:
            if col.lower() == 'gloss':
                gloss_col = col
                break

        if gloss_col:
            st.markdown(f"Gloss column detected: **{gloss_col}**")
        else:
            gloss_col = st.selectbox(
                "Select gloss column",
                options=["-none-"] + columns,
                help="Column containing glosses/meanings",
            )
            if gloss_col == "-none-":
                gloss_col = None

        st.markdown("---")

        # Categorical columns (optional)
        st.markdown("**Categorical Columns (Optional)**")
        st.caption(
            "If your data has multiple speakers or tokens, "
            "select those columns so grouping works correctly."
        )

        # Exclude standard columns from categorical options
        exclude_cols = {'index', 'entry', 'gloss', 'sub_index', 'word'}
        available_cat_cols = [c for c in columns if c.lower() not in exclude_cols]

        categorical_columns = st.multiselect(
            "Select categorical columns",
            options=available_cat_cols,
            default=[],
            help="Columns like 'speaker', 'token', etc.",
        )

        st.markdown("---")

        # Process button
        process_clicked = st.button(
            "Explode Entries",
            type="primary",
            use_container_width=True,
        )

        if process_clicked:
            st.session_state._explode_params = {
                "entry_col": entry_col,
                "gloss_col": gloss_col,
                "categorical_columns": categorical_columns if categorical_columns else None,
            }
            st.rerun()

        st.markdown("---")

        if st.button("Back to Main Menu", use_container_width=True):
            for key in ["_explode_params", "_explode_result"]:
                if key in st.session_state:
                    del st.session_state[key]
            go_back_to_menu()

    # === OUTPUT COLUMN ===
    with output_col:
        st.subheader("Output")

        # Process if triggered
        if "_explode_params" in st.session_state:
            params = st.session_state._explode_params
            del st.session_state._explode_params

            with st.spinner("Exploding entries..."):
                result = explode_entries(
                    df=df,
                    entry_col=params["entry_col"],
                    gloss_col=params["gloss_col"],
                    categorical_columns=params["categorical_columns"],
                )

            if result.success:
                st.session_state._explode_result = result
                st.session_state._scroll_to_top = True
                st.session_state.database = result.df
                st.session_state.database_validated = True
                st.rerun()
            else:
                st.error(f"**Error:** {result.error}")

                st.markdown("---")

                if st.button("Clear Database & Start Over", type="primary", use_container_width=True):
                    for key in ["_explode_params", "_explode_result"]:
                        if key in st.session_state:
                            del st.session_state[key]
                    st.session_state.database = None
                    st.session_state.database_validated = False
                    st.session_state.database_filename = None
                    st.session_state.database_sheet_name = None
                    st.session_state.selected_task = None
                    navigate_to(Screen.UPLOAD_DATABASE)

        # Display result if available
        if "_explode_result" in st.session_state:
            result = st.session_state._explode_result

            st.success("Entries exploded successfully!")

            st.markdown(f"""
            **Summary:**
            - Entries processed: {result.summary.get('entries_processed', 'N/A')}
            - Total words created: {result.summary.get('words_created', 'N/A')}
            - Rows before: {result.summary.get('rows_before', 'N/A')}
            - Rows after: {result.summary.get('rows_after', 'N/A')}
            """)

            # Cleaning report
            if result.cleaning_report.get("changes_made"):
                with st.expander("Cleaning report", expanded=False):
                    punct = result.cleaning_report.get("punctuation_removed", {})
                    ws = result.cleaning_report.get("whitespace_changes", 0)
                    if punct:
                        st.markdown("**Punctuation removed:**")
                        for char, count in punct.items():
                            st.text(f"  '{char}': {count}")
                    if ws:
                        st.markdown(f"**Whitespace normalized:** {ws} cells")
                    st.markdown(
                        "Original values preserved in the `entry_orig` column."
                    )

            # Note about preserved columns
            if 'word_old' in result.df.columns:
                st.info("Existing 'word' column was preserved as 'word_old'.")
            if 'sub_index_old' in result.df.columns:
                st.info("Existing 'sub_index' column was preserved as 'sub_index_old'.")

            st.markdown("---")

            # Buttons row
            btn_col1, btn_col2 = st.columns(2)

            with btn_col1:
                st.download_button(
                    label="Download Updated Database",
                    data=export_database(result.df),
                    file_name="database_exploded.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    type="primary",
                    use_container_width=True,
                )

            with btn_col2:
                if st.button("Return to Main Menu", use_container_width=True, key="return_after_explode"):
                    for key in ["_explode_params", "_explode_result"]:
                        if key in st.session_state:
                            del st.session_state[key]
                    go_back_to_menu()

            st.markdown("---")

            st.markdown("**Updated Database Preview:**")
            preview_cols = []
            for col in ['index', 'sub_index', 'entry', 'word', 'gloss']:
                if col in result.df.columns:
                    preview_cols.append(col)

            if preview_cols:
                st.dataframe(result.df[preview_cols].head(20), use_container_width=True)
            else:
                st.dataframe(result.df.head(20), use_container_width=True)

        else:
            # Initial state - show instructions
            st.info(
                "Configure your column mappings in the left panel, "
                "then click **Explode Entries** to split multi-word entries."
            )

            st.markdown("---")

            st.markdown("**About This Task**")
            st.markdown(
                """
                This task splits multi-word entries into one-word-per-row,
                adding two new columns:

                - **sub_index**: The position of each word within its entry (1, 2, 3...)
                - **word**: The individual word from the entry

                Before splitting, entry transcriptions are cleaned:
                - Unicode whitespace is normalized
                - Punctuation is removed
                - Multiple spaces are collapsed

                If your database already has `word` or `sub_index` columns,
                they will be preserved as `word_old` and `sub_index_old`.
                """
            )

            st.markdown("---")

            st.markdown("**Example (before):**")
            example_before = pd.DataFrame({
                'index': [1, 2, 3],
                'entry': ['ma pa', 'ka', 'ta na sa'],
                'gloss': ['parents', 'house', 'three words'],
            })
            st.dataframe(example_before, use_container_width=True, hide_index=True)

            st.markdown("**Example (after):**")
            example_after = pd.DataFrame({
                'index': [1, 1, 2, 3, 3, 3],
                'sub_index': [1, 2, 1, 1, 2, 3],
                'entry': ['ma pa', 'ma pa', 'ka', 'ta na sa', 'ta na sa', 'ta na sa'],
                'word': ['ma', 'pa', 'ka', 'ta', 'na', 'sa'],
                'gloss': ['parents', 'parents', 'house', 'three words', 'three words', 'three words'],
            })
            st.dataframe(example_after, use_container_width=True, hide_index=True)


def screen_segment_words():
    """Screen for segmenting words into phonological columns."""

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

    st.title("Segment Words")
    st.markdown("---")

    # Two-column layout
    config_col, output_col = st.columns([1, 2])

    df = st.session_state.database
    columns = list(df.columns)

    with config_col:
        st.subheader("Configuration")

        # Auto-detect word column
        word_col = None
        for col in columns:
            if col.lower() == 'word':
                word_col = col
                break

        if word_col:
            st.success(f"Word column detected: **{word_col}**")
        else:
            st.info(
                "No 'word' column found. Run **Explode Entries** first, "
                "or select a column containing individual words below."
            )
            word_col = st.selectbox(
                "Select word column",
                options=columns,
                help="Column containing individual IPA-transcribed words to segment",
            )

        st.markdown("---")

        # Process button
        process_clicked = st.button(
            "Segment Words",
            type="primary",
            use_container_width=True,
        )

        if process_clicked:
            st.session_state._segment_params = {
                "word_col": word_col,
            }
            st.rerun()

        st.markdown("---")

        if st.button("Back to Main Menu", use_container_width=True):
            for key in ["_segment_params", "_segment_result"]:
                if key in st.session_state:
                    del st.session_state[key]
            go_back_to_menu()

    # === OUTPUT COLUMN ===
    with output_col:
        st.subheader("Output")

        # Process if triggered
        if "_segment_params" in st.session_state:
            params = st.session_state._segment_params
            del st.session_state._segment_params

            with st.spinner("Segmenting words..."):
                result = segment_words(
                    df=df,
                    word_col=params["word_col"],
                )

            if result.success:
                st.session_state._segment_result = result
                st.session_state._scroll_to_top = True
                st.session_state.database = result.df
                st.session_state.database_validated = True
                st.rerun()
            else:
                st.error(f"**Error:** {result.error}")

                st.markdown("---")

                if st.button("Clear Database & Start Over", type="primary", use_container_width=True):
                    for key in ["_segment_params", "_segment_result"]:
                        if key in st.session_state:
                            del st.session_state[key]
                    st.session_state.database = None
                    st.session_state.database_validated = False
                    st.session_state.database_filename = None
                    st.session_state.database_sheet_name = None
                    st.session_state.selected_task = None
                    navigate_to(Screen.UPLOAD_DATABASE)

        # Display result if available
        if "_segment_result" in st.session_state:
            result = st.session_state._segment_result
            error_count = result.summary.get("error_count", 0)
            total_words = result.summary.get("total_words", 0)
            words_segmented = result.summary.get("words_segmented", 0)

            if error_count == 0:
                st.success("All words segmented successfully!")
            else:
                st.warning(
                    f"Segmentation complete with {error_count} error(s) "
                    f"out of {total_words} words."
                )

            st.markdown(f"""
            **Summary:**
            - Words segmented: {words_segmented}
            - Errors: {error_count}
            - Total words: {total_words}
            """)

            # Show errors in expander
            if error_count > 0:
                error_words = result.summary.get("error_words", {})
                with st.expander(f"Error details ({error_count} words)", expanded=False):
                    st.markdown(
                        "These words have `'error'` in their segmentation columns:"
                    )
                    for word_text, reason in list(error_words.items())[:30]:
                        st.text(f"  '{word_text}': {reason}")
                    if len(error_words) > 30:
                        st.text(f"  ... and {len(error_words) - 30} more")

            # Cleaning report
            if result.cleaning_report.get("changes_made"):
                with st.expander("Cleaning report", expanded=False):
                    punct = result.cleaning_report.get("punctuation_removed", {})
                    ws = result.cleaning_report.get("whitespace_changes", 0)
                    if punct:
                        st.markdown("**Punctuation removed:**")
                        for char, count in punct.items():
                            st.text(f"  '{char}': {count}")
                    if ws:
                        st.markdown(f"**Whitespace normalized:** {ws} cells")

            st.markdown("---")

            # Buttons row
            btn_col1, btn_col2 = st.columns(2)

            with btn_col1:
                st.download_button(
                    label="Download Updated Database",
                    data=export_database(result.df),
                    file_name="database_segmented.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    type="primary",
                    use_container_width=True,
                )

            with btn_col2:
                if st.button("Return to Main Menu", use_container_width=True, key="return_after_segment"):
                    for key in ["_segment_params", "_segment_result"]:
                        if key in st.session_state:
                            del st.session_state[key]
                    go_back_to_menu()

            st.markdown("---")

            st.markdown("**Updated Database Preview:**")
            preview_cols = []
            for col in ['index', 'sub_index', 'word', 'P', 'R', 'C', 'M', 'V', 'F', 'T']:
                if col in result.df.columns:
                    preview_cols.append(col)

            if preview_cols:
                st.dataframe(result.df[preview_cols].head(20), use_container_width=True)
            else:
                st.dataframe(result.df.head(20), use_container_width=True)

        else:
            # Initial state - show instructions
            st.info(
                "Click **Segment Words** to break words into phonological columns."
            )

            st.markdown("---")

            st.markdown("**About This Task**")
            st.markdown(
                """
                This task breaks IPA-transcribed words into phonological columns:

                | Column | Description |
                |--------|-------------|
                | **P** | Presyllable onset |
                | **R** | Presyllable rime |
                | **C** | Main syllable onset (consonant) |
                | **M** | Medial (glide between onset and vowel) |
                | **V** | Vowel (nucleus) |
                | **F** | Final (coda) |
                | **T** | Tone / register |

                Words containing non-IPA characters, invalid tone sequences,
                or no detectable vowels will have `'error'` in their segmentation
                columns. These do not block processing of other words.
                """
            )

            st.markdown("---")

            st.markdown("**Example (before):**")
            example_before = pd.DataFrame({
                'index': [1, 1, 2],
                'sub_index': [1, 2, 1],
                'word': ['kʰaːw', 'maː', 'pa'],
            })
            st.dataframe(example_before, use_container_width=True, hide_index=True)

            st.markdown("**Example (after):**")
            example_after = pd.DataFrame({
                'index': [1, 1, 2],
                'sub_index': [1, 2, 1],
                'word': ['kʰaːw', 'maː', 'pa'],
                'P': ['', '', ''],
                'R': ['', '', ''],
                'C': ['kʰ', 'm', 'p'],
                'M': ['', '', ''],
                'V': ['aː', 'aː', 'a'],
                'F': ['w', '∅', '∅'],
                'T': ['', '', ''],
            })
            st.dataframe(example_after, use_container_width=True, hide_index=True)


def screen_generate_cards():
    """Screen for exporting a printable card-sorting activity (Orthography Development)."""

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

    st.title("Generate Cards")
    st.markdown("---")

    # Two-column layout
    config_col, output_col = st.columns([1, 2])

    df = st.session_state.database
    columns = list(df.columns)

    with config_col:
        # === STEP 1: FILTER DATABASE (OPTIONAL) ===
        st.subheader("Step 1: Filter Database (Optional)")
        st.caption("Narrow down which rows are available before choosing card content. Leave blank to include everything.")

        if "_generate_cards_filter_epoch" not in st.session_state:
            st.session_state._generate_cards_filter_epoch = 0
        epoch = st.session_state._generate_cards_filter_epoch

        filter_columns = st.multiselect(
            "Filter by columns",
            options=columns,
            default=[],
            key=f"_sort_filter_cols_{epoch}",
        )

        selected_filters = {}
        for col in filter_columns:
            col_options = get_column_filter_options(df, col)
            selected_filters[col] = st.multiselect(
                f"Values to include — '{col}'",
                options=col_options,
                default=col_options,
                key=f"_sort_filter_val_{epoch}_{col}",
            )

        if st.button("Clear Filters", use_container_width=True, disabled=not filter_columns):
            st.session_state._generate_cards_filter_epoch = epoch + 1
            st.rerun()

        filtered_df = filter_dataframe(df, selected_filters)

        st.markdown(f"**{len(filtered_df):,}** of **{len(df):,}** rows match your filters.")

        st.markdown("---")

        # === STEP 2: CARD CONTENT ===
        st.subheader("Step 2: Card Content")

        index_default = columns.index("index") if "index" in columns else 0
        index_col = st.selectbox(
            "Index column",
            options=columns,
            index=index_default,
            key="_sort_index_col",
        )

        sub_index_options = ["-none-"] + columns
        sub_index_default = sub_index_options.index("sub_index") if "sub_index" in columns else 0
        sub_index_choice = st.selectbox(
            "Sub-index column (optional)",
            options=sub_index_options,
            index=sub_index_default,
            key="_sort_sub_index_col",
            help="If your entries have been exploded into words, select 'sub_index' so each card gets an 'index.sub_index' label.",
        )
        sub_index_col = None if sub_index_choice == "-none-" else sub_index_choice

        st.markdown("**Card lines** (top to bottom)")

        line_options = ["-none-"] + columns
        line_1 = st.selectbox("Line 1 (large)", options=line_options, index=0, key="_sort_line_1")
        line_2 = st.selectbox("Line 2", options=line_options, index=0, key="_sort_line_2")
        line_3 = st.selectbox("Line 3", options=line_options, index=0, key="_sort_line_3")

        line_columns = [c for c in [line_1, line_2, line_3] if c != "-none-"]

        st.markdown("")

        sort_options = ["-none-"] + columns
        sort_key = "_sort_sort_by"
        if sort_key in st.session_state and st.session_state[sort_key] not in sort_options:
            st.session_state[sort_key] = "-none-"
        sort_choice = st.selectbox(
            "Sort by",
            options=sort_options,
            index=0,
            key=sort_key,
            help="Sort cards by any database column before export -- handy for spotting near-duplicate entries during a workshop, since they'll land next to each other in the printed grid. Doesn't need to be one of the card lines above.",
        )
        sort_by_col = None if sort_choice == "-none-" else sort_choice

        st.markdown("---")

        # === STEP 3: EXPORT ===
        st.subheader("Step 3: Export")

        file_name = st.text_input(
            "Export name",
            value="sorting_activity",
            key="_sort_file_name",
            help="Used as the HTML deck's filename, and (for the JSON) as the resulting sorting activity's name.",
        )

        can_generate = len(filtered_df) > 0 and len(line_columns) > 0

        generate_clicked = st.button(
            "Generate Cards",
            type="primary",
            use_container_width=True,
            disabled=not can_generate,
        )

        if not can_generate:
            if len(filtered_df) == 0:
                st.caption("No rows match your current filters.")
            else:
                st.caption("Select at least one card line above.")

        if generate_clicked:
            st.session_state._generate_cards_generate_params = {
                "filtered_df": filtered_df,
                "index_col": index_col,
                "sub_index_col": sub_index_col,
                "line_columns": line_columns,
                "sort_by_col": sort_by_col,
                "file_name": file_name,
                "selected_filters": selected_filters,
            }
            st.rerun()

        st.markdown("")

        if st.button("Back to Main Menu", use_container_width=True):
            for key in ["_generate_cards_generate_params", "_generate_cards_export_result"]:
                if key in st.session_state:
                    del st.session_state[key]
            go_back_to_menu()

    # === OUTPUT COLUMN ===
    with output_col:
        st.subheader("Output")

        # Process generation if triggered
        if "_generate_cards_generate_params" in st.session_state:
            params = st.session_state._generate_cards_generate_params
            del st.session_state._generate_cards_generate_params

            with st.spinner("Building cards..."):
                build_result = build_cards(
                    df=params["filtered_df"],
                    index_col=params["index_col"],
                    sub_index_col=params["sub_index_col"],
                    line_columns=params["line_columns"],
                    sort_by_col=params["sort_by_col"],
                )

                if build_result.success:
                    html = generate_cards_html(build_result.cards)
                    narrowing_filters = build_sort_activity_filters(
                        df=df,
                        selected_filters=params["selected_filters"],
                    )
                    json_bytes = build_sort_activity_json(
                        activity_name=params["file_name"],
                        index_col=params["index_col"],
                        sub_index_col=params["sub_index_col"],
                        filters=narrowing_filters,
                        line_columns=params["line_columns"],
                    )
                else:
                    html = None
                    json_bytes = None

            st.session_state._generate_cards_export_result = {
                "build_result": build_result,
                "html": html,
                "json_bytes": json_bytes,
                "file_name": params["file_name"],
            }
            st.session_state._scroll_to_top = True
            st.rerun()

        if "_generate_cards_export_result" in st.session_state:
            export = st.session_state._generate_cards_export_result
            build_result: CardBuildResult = export["build_result"]

            if build_result.success:
                st.success(
                    f"Cards generated: {build_result.included_rows:,} card(s) "
                    f"from {build_result.total_rows:,} row(s)."
                )

                st.markdown("---")

                base_name = export["file_name"].strip() or "sorting_activity"
                html_name = base_name if base_name.endswith(".html") else base_name + ".html"
                json_name = base_name if base_name.endswith(".json") else base_name + ".json"

                btn_col1, btn_col2 = st.columns(2)

                with btn_col1:
                    st.download_button(
                        label=f"Download {html_name}",
                        data=export["html"].encode("utf-8"),
                        file_name=html_name,
                        mime="text/html",
                        type="primary",
                        use_container_width=True,
                        help="Printable HTML card deck for physical sorting.",
                    )

                with btn_col2:
                    st.download_button(
                        label=f"Download {json_name}",
                        data=export["json_bytes"],
                        file_name=json_name,
                        mime="application/json",
                        type="primary",
                        use_container_width=True,
                        help="Prepared activity file for digital/asynchronous sorting in Sort Cards.",
                    )

                if st.button("Return to Main Menu", use_container_width=True, key="return_after_sorting"):
                    del st.session_state._generate_cards_export_result
                    go_back_to_menu()

                st.markdown("---")

                st.markdown("**Preview (HTML deck):**")
                components.html(export["html"], height=500, scrolling=True)

            else:
                st.error(f"**Error:** {build_result.error}")

                if build_result.duplicate_indices:
                    st.markdown("**Duplicate values:**")
                    for dup in build_result.duplicate_indices[:20]:
                        st.text(f"  {dup}")
                    if len(build_result.duplicate_indices) > 20:
                        st.text(f"  ... and {len(build_result.duplicate_indices) - 20} more")

                st.markdown("---")

                if st.button("Back to Configuration", use_container_width=True):
                    del st.session_state._generate_cards_export_result
                    st.rerun()

        else:
            # Not yet generated - show live filtered (and sorted) preview + instructions
            preview_df = sort_dataframe(filtered_df, sort_by_col)

            st.markdown("**Filtered Database Preview**")
            st.markdown(f"**{len(filtered_df):,}** of **{len(df):,}** rows match your current filters.")
            if sort_by_col:
                st.caption(f"Sorted by '{sort_by_col}'.")
            st.dataframe(preview_df.head(15), use_container_width=True)

            st.markdown("---")

            st.markdown("**About Generating Cards**")
            st.markdown(
                """
                This task generates cards for orthography-development card-sorting activities
                with speakers, for either physical or digital sorting.

                1. **Filter** (optional) narrows down which rows are eligible.
                2. **Card lines** pick up to 3 columns to display on each card (e.g. a native
                   script gloss, an English gloss, and a phonetic transcription).
                3. **Export** generates a Letter-size HTML deck (10 cards per page, with
                   automatic Lao-script and IPA font handling) for physical sorting, and a
                   prepared-activity JSON file to hand off for digital/asynchronous sorting in
                   Sort Cards.
                """
            )

            st.markdown("---")

            st.markdown("**Example card content:**")
            example_card = pd.DataFrame({
                "index": [1],
                "gloss_lao": ["ສຸຂ"],
                "gloss_eng": ["happiness"],
                "phonetic": ["/suk/"],
            })
            st.dataframe(example_card, use_container_width=True, hide_index=True)


def _clear_process_cards_state():
    """Remove all Process Cards session-state, including per-category widget keys."""
    for cat_id in st.session_state.get("_process_cards_categories", []):
        for prefix in ("_pc_label_", "_pc_uids_"):
            key = f"{prefix}{cat_id}"
            if key in st.session_state:
                del st.session_state[key]

    for key in [
        "_process_cards_categories",
        "_process_cards_next_id",
        "_process_cards_generate_params",
        "_process_cards_result",
        "_process_cards_method",
        "_pc_ai_paste",
        "_process_cards_ai_parse_feedback",
    ]:
        if key in st.session_state:
            del st.session_state[key]


def screen_process_cards():
    """Screen for recording card-sorting activity results back into the database."""

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

    st.title("Process Cards")
    st.markdown("---")

    config_col, output_col = st.columns([1, 2])

    df = st.session_state.database
    columns = list(df.columns)

    with config_col:
        # === METHOD ===
        st.subheader("Method")

        if "_process_cards_method" not in st.session_state:
            st.session_state._process_cards_method = "manual"

        def _method_pill(label: str):
            st.markdown(
                f'<div style="padding:0.5rem 1rem;border-radius:0.5rem;'
                f'background-color:#2E7D32;color:white;text-align:center;'
                f'font-weight:600;">{label}</div>',
                unsafe_allow_html=True,
            )

        method_col1, method_col2 = st.columns(2)
        with method_col1:
            if st.session_state._process_cards_method == "manual":
                _method_pill("Manual Input")
            elif st.button("Manual Input", use_container_width=True):
                st.session_state._process_cards_method = "manual"
                st.rerun()
        with method_col2:
            if st.session_state._process_cards_method == "ai":
                _method_pill("AI-Assisted Input")
            elif st.button("AI-Assisted Input", use_container_width=True):
                st.session_state._process_cards_method = "ai"
                st.rerun()

        st.markdown("---")

        # === STEP 1: INDEX COLUMNS ===
        st.subheader("Step 1: Index Columns")
        st.caption("Must match the index/sub-index columns used to print the cards, so UIDs line up.")

        index_default = columns.index("index") if "index" in columns else 0
        index_col = st.selectbox(
            "Index column",
            options=columns,
            index=index_default,
            key="_pc_index_col",
        )

        sub_index_options = ["-none-"] + columns
        sub_index_default = sub_index_options.index("sub_index") if "sub_index" in columns else 0
        sub_index_choice = st.selectbox(
            "Sub-index column (optional)",
            options=sub_index_options,
            index=sub_index_default,
            key="_pc_sub_index_col",
            help="Select this if the cards were printed with 'index.sub_index' UIDs.",
        )
        sub_index_col = None if sub_index_choice == "-none-" else sub_index_choice

        st.markdown("---")

        # === STEP 2: ACTIVITY NAME ===
        st.subheader("Step 2: Sorting Activity Name")

        activity_name = st.text_input(
            "Activity name",
            key="_pc_activity_name",
            placeholder="e.g. front p",
            help="Becomes the new database column name. Spaces are replaced with underscores.",
        )

        sanitized_column_name = sanitize_activity_column_name(activity_name)
        if sanitized_column_name:
            if sanitized_column_name in df.columns:
                st.caption(f"Column name: `{sanitized_column_name}` -- already exists, choose another name.")
            else:
                st.caption(f"Column name: `{sanitized_column_name}`")

        st.markdown("---")

        # === AI-ASSISTED INPUT (photo-based pre-fill for Step 3) ===
        if st.session_state._process_cards_method == "ai":
            st.subheader("AI-Assisted Photo Reading")

            with st.expander("How AI-Assisted Input works -- read before your workshop", expanded=True):
                st.markdown(
                    """
                    This method uses an AI chat tool you already have access to (Claude, ChatGPT,
                    or similar) to read the UID codes off photographed cards, instead of you typing
                    them in by hand. Plan the photo side of this **before** your workshop:

                    **1. During the workshop -- spread and photograph each pile**

                    For each sorted pile, spread the cards out so every card's UID (bottom-right
                    corner) is visible in the photo -- a stacked deck only shows the top card.
                    Take one photo per pile; if a pile is too big to fit in one frame, take
                    several photos of it.

                    **2. Name your photos by category**

                    Rename each photo to match the category it shows, e.g. `i.jpg`. If a pile
                    needed more than one photo, add a number: `i_2.jpg`, `i_3.jpg` -- these get
                    combined back into a single "i" category automatically. The name becomes the
                    value written into the database for every card in that pile, so spell it
                    exactly as you want it to appear.

                    **3. Get the codes read by AI**

                    Copy the prompt below, start a new conversation in Claude, ChatGPT, or a
                    similar tool, paste the prompt in, and attach all of your category-labeled
                    photos to that same message. If you're shooting on an iPhone, note that AI
                    chat tools don't reliably accept its default `.HEIC` photos -- switch to
                    "Most Compatible" mode first (Settings > Camera > Formats) so photos save as
                    `.jpg`, or convert existing ones before uploading.

                    **4. Bring the results back here**

                    Copy the AI's full reply, paste it into the box below, and click
                    **Parse & Fill Categories** to fill in Step 3. Review what gets filled in
                    before processing -- a misread code will usually show up as a UID "not found"
                    error below, which is your cue to check the original photo.
                    """
                )

            st.markdown("**Prompt to copy into your AI chat tool:**")
            st.code(AI_ASSISTED_PROMPT, language=None)

            ai_paste_text = st.text_area(
                "Paste the AI's reply here",
                key="_pc_ai_paste",
                height=150,
                placeholder="i.jpg: 4, 9, 22.1\ni_2.jpg: 15, 30.2\ne.jpg: 3, 7, 12.1",
            )

            if st.button(
                "Parse & Fill Categories",
                use_container_width=True,
                disabled=not ai_paste_text.strip(),
            ):
                parse_result = parse_ai_assisted_output(ai_paste_text)
                st.session_state._process_cards_ai_parse_feedback = parse_result

                if parse_result.success:
                    for cat_id in st.session_state.get("_process_cards_categories", []):
                        for prefix in ("_pc_label_", "_pc_uids_"):
                            key = f"{prefix}{cat_id}"
                            if key in st.session_state:
                                del st.session_state[key]

                    next_id = st.session_state.get("_process_cards_next_id", 0)
                    new_ids = []
                    for label, uid_text in parse_result.categories:
                        st.session_state[f"_pc_label_{next_id}"] = label
                        st.session_state[f"_pc_uids_{next_id}"] = uid_text
                        new_ids.append(next_id)
                        next_id += 1

                    st.session_state._process_cards_categories = new_ids
                    st.session_state._process_cards_next_id = next_id

                st.rerun()

            ai_feedback: AIOutputParseResult | None = st.session_state.get("_process_cards_ai_parse_feedback")
            if ai_feedback is not None:
                if ai_feedback.success:
                    n = len(ai_feedback.categories)
                    st.success(f"Filled in {n} categor{'y' if n == 1 else 'ies'} below -- review before processing.")
                else:
                    st.error(ai_feedback.error)
                if ai_feedback.unparsed_lines:
                    st.warning(
                        "Some lines didn't match the expected format and were skipped:\n\n"
                        + "\n".join(f"- {ln}" for ln in ai_feedback.unparsed_lines)
                    )

            st.markdown("---")

        # === STEP 3: CATEGORIES ===
        st.subheader("Step 3: Categories")
        st.caption(
            "One category per pile the cards were sorted into. Enter the UID from the "
            "bottom-right of each card, separated by commas, spaces, or newlines."
        )

        if "_process_cards_categories" not in st.session_state:
            st.session_state._process_cards_categories = [0, 1]
            st.session_state._process_cards_next_id = 2

        categories: list[tuple[str, str]] = []
        for cat_id in list(st.session_state._process_cards_categories):
            label_key = f"_pc_label_{cat_id}"
            uids_key = f"_pc_uids_{cat_id}"

            cat_label_col, cat_remove_col = st.columns([5, 1])
            with cat_label_col:
                label = st.text_input(
                    "Category label",
                    key=label_key,
                    placeholder="e.g. i",
                    label_visibility="collapsed",
                )
            with cat_remove_col:
                if st.button("✕", key=f"_pc_remove_{cat_id}", use_container_width=True, help="Remove this category"):
                    st.session_state._process_cards_categories.remove(cat_id)
                    for key in (label_key, uids_key):
                        if key in st.session_state:
                            del st.session_state[key]
                    st.rerun()

            uid_text = st.text_area(
                "UIDs",
                key=uids_key,
                placeholder="e.g. 4, 9, 22.1",
                label_visibility="collapsed",
                height=80,
            )

            if uid_text.strip():
                st.caption(f"{len(parse_uid_list(uid_text))} UID(s)")

            categories.append((label, uid_text))

            st.markdown("")

        if st.button("+ Add Category", use_container_width=True):
            new_id = st.session_state._process_cards_next_id
            st.session_state._process_cards_categories.append(new_id)
            st.session_state._process_cards_next_id = new_id + 1
            st.rerun()

        st.markdown("---")

        # === STEP 4: PROCESS ===
        st.subheader("Step 4: Process")

        can_process = bool(sanitized_column_name) and any(
            label.strip() and text.strip() for label, text in categories
        )

        process_clicked = st.button(
            "Process Cards",
            type="primary",
            use_container_width=True,
            disabled=not can_process,
        )

        if not can_process:
            if not sanitized_column_name:
                st.caption("Enter a sorting activity name.")
            else:
                st.caption("Add at least one category with a label and UIDs.")

        if process_clicked:
            st.session_state._process_cards_generate_params = {
                "index_col": index_col,
                "sub_index_col": sub_index_col,
                "activity_name": activity_name,
                "categories": categories,
            }
            st.rerun()

        st.markdown("")

        if st.button("Back to Main Menu", use_container_width=True):
            _clear_process_cards_state()
            go_back_to_menu()

    # === OUTPUT COLUMN ===
    with output_col:
        st.subheader("Output")

        # Process if triggered
        if "_process_cards_generate_params" in st.session_state:
            params = st.session_state._process_cards_generate_params
            del st.session_state._process_cards_generate_params

            with st.spinner("Processing cards..."):
                result = process_cards_manual(
                    df=df,
                    index_col=params["index_col"],
                    sub_index_col=params["sub_index_col"],
                    activity_name=params["activity_name"],
                    categories=params["categories"],
                )

            st.session_state._process_cards_result = result
            if result.success:
                st.session_state.database = result.df
                st.session_state.database_validated = True
                st.session_state._scroll_to_top = True
            st.rerun()

        # Display result if available
        if "_process_cards_result" in st.session_state:
            result: ProcessCardsResult = st.session_state._process_cards_result

            if result.success:
                categories_n = result.summary["categories"]
                st.success(
                    f"Column '{result.column_name}' added: {result.summary['rows_labeled']:,} row(s) labeled "
                    f"across {categories_n} categor{'y' if categories_n == 1 else 'ies'}, "
                    f"{result.summary['rows_blank']:,} row(s) left blank."
                )

                st.markdown("---")

                btn_col1, btn_col2 = st.columns(2)

                with btn_col1:
                    st.download_button(
                        label="Download Updated Database",
                        data=export_database(result.df),
                        file_name="database_processed.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        type="primary",
                        use_container_width=True,
                    )

                with btn_col2:
                    if st.button("Return to Main Menu", use_container_width=True, key="return_after_process_cards"):
                        del st.session_state._process_cards_result
                        _clear_process_cards_state()
                        go_back_to_menu()

                st.markdown("---")

                st.markdown("**Updated Database Preview:**")
                preview_cols = [c for c in [index_col, sub_index_col, result.column_name] if c]
                st.dataframe(result.df[preview_cols].head(20), use_container_width=True)

            else:
                st.error(f"**Error:** {result.error}")

                if result.duplicate_uids:
                    st.markdown("**Duplicate UIDs:**")
                    for uid in result.duplicate_uids[:20]:
                        st.text(f"  {uid}")
                    if len(result.duplicate_uids) > 20:
                        st.text(f"  ... and {len(result.duplicate_uids) - 20} more")

                if result.unmatched_uids:
                    st.markdown("**UIDs not found in database:**")
                    for uid in result.unmatched_uids[:20]:
                        st.text(f"  {uid}")
                    if len(result.unmatched_uids) > 20:
                        st.text(f"  ... and {len(result.unmatched_uids) - 20} more")

                st.markdown("---")

                if st.button("Back to Configuration", use_container_width=True):
                    del st.session_state._process_cards_result
                    st.rerun()

        else:
            # Not yet processed - show instructions
            st.info(
                "Configure the index columns, name your sorting activity, add categories with "
                "their UIDs, then click **Process Cards** in the left panel."
            )

            st.markdown("---")

            st.markdown("**About Processing Cards**")
            st.markdown(
                """
                This task records the results of a card-sorting activity back into the database.

                1. **Index Columns** must match what was used to print the cards, so UIDs line up.
                2. **Activity Name** becomes a new database column (spaces become underscores).
                3. **Categories** -- one per pile the cards were sorted into. Each category has a
                   label (the value written into the database) and a list of UIDs (from the
                   bottom-right of each card) sorted into that pile.
                4. **Process** writes the category label onto each matching row's new column.
                   Rows not covered by any category are left blank.
                """
            )

            st.markdown("---")

            st.markdown("**Example:**")
            example_df = pd.DataFrame({
                "index": [4, 9, 15, 22],
                "sub_index": [1, 1, 1, 1],
                "front_p": ["i", "i", "e", None],
            })
            st.dataframe(example_df, use_container_width=True, hide_index=True)


# =============================================================================
# SCREEN ROUTER
# =============================================================================

SCREEN_FUNCTIONS: dict[str, Callable] = {
    Screen.WELCOME: screen_welcome,
    Screen.UPLOAD_DATABASE: screen_upload_database,
    Screen.MAIN_MENU: screen_main_menu_phonological,  # legacy fallback
    Screen.MAIN_MENU_PHONOLOGICAL: screen_main_menu_phonological,
    Screen.MAIN_MENU_ORTHOGRAPHY: screen_main_menu_orthography,
    Screen.MAIN_MENU_ACOUSTIC: screen_main_menu_acoustic,
    Screen.ABOUT: screen_about,
    Screen.TUTORIAL: screen_tutorial,
    Screen.TASK_PLACEHOLDER: screen_task_placeholder,
    Screen.TASK_CREATE_DATA_COLLECTION_SCRIPT: screen_create_data_collection_script,
    Screen.TASK_ADD_AUDIO_LINKS: screen_add_audio_links,
    Screen.TASK_UPDATE_ENTRIES_FROM_WORDS: screen_update_entries_from_words,
    Screen.TASK_EXPLODE_ENTRIES: screen_explode_entries,
    Screen.TASK_SEGMENT_WORDS: screen_segment_words,
    Screen.TASK_GENERATE_CARDS: screen_generate_cards,
    Screen.TASK_PROCESS_CARDS: screen_process_cards,
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


# =============================================================================
# MAIN APP
# =============================================================================

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


def main():
    """Main application entry point."""
    st.set_page_config(
        page_title="Excelerant",
        page_icon="assets/excelerant_favicon.png",
        layout="wide",
        initial_sidebar_state="collapsed",
    )

    st.markdown(
        """
        <style>
        .block-container {
            padding-top: 2rem;
        }
        .stButton > button {
            min-height: 2.5rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    init_session_state()
    render_current_screen()

    # Handle scroll-to-top at the very end (to avoid creating space at top)
    render_scroll_to_top()


if __name__ == "__main__":
    main()
