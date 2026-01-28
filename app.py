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
    prepare_and_export,
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
        description="Generate an XML script for SpeechRecorder to collect audio recordings. Maps database columns to prompt fields (gloss, index, frame, extra info) and supports multiple token repetitions.",
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
        description="Split multi-word entries into separate rows while preserving the original entry reference. Useful for analyzing individual words in phrases.",
        requirements=[
            "Entries with multiple words separated by spaces",
        ],
        example="Input: 'big house' (1 row)\nOutput: 'big', 'house' (2 rows, linked to original)",
        youtube_url=None,
    ),
    "segment_words": TaskInfo(
        id="segment_words",
        name="Segment Words",
        category="Configure Transcriptions",
        description="Break words into individual segments (phonemes) for detailed phonological analysis. Each segment gets its own column or row.",
        requirements=[
            "IPA transcriptions in database",
            "Syllable boundary markers (optional)",
        ],
        example="Input: '/káːw/'\nOutput: ['k', 'áː', 'w']",
        youtube_url=None,
    ),
    "update_entries_from_words": TaskInfo(
        id="update_entries_from_words",
        name="Check Database Formatting & Update Entries",
        category="Configure Transcriptions",
        description="Propagate changes made at the word level back to the original entries. Sync edits after working with exploded data.",
        requirements=[
            "Previously exploded entries",
            "Edits made to word-level data",
        ],
        example="Input: Edited words\nOutput: Updated original entries",
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
    "Acoustic Phonetic Analysis",
]

# Tasks that are currently implemented and enabled
ENABLED_TASKS = {
    "create_data_collection_script",
    "add_audio_links",
    "explode_entries",
    "segment_words",
    "update_entries_from_words",
}


# =============================================================================
# NAVIGATION STATE
# =============================================================================

class Screen:
    """All possible screens in the app (string constants)."""
    WELCOME = "welcome"
    UPLOAD_DATABASE = "upload_database"
    MAIN_MENU = "main_menu"
    ABOUT = "about"
    TUTORIAL = "tutorial"
    # Task screens - add as needed
    TASK_PLACEHOLDER = "task_placeholder"
    TASK_CREATE_DATA_COLLECTION_SCRIPT = "task_create_data_collection_script"
    TASK_ADD_AUDIO_LINKS = "task_add_audio_links"


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
    navigate_to(Screen.MAIN_MENU)


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
            
            Excelerant helps you process lexical databases for phonological 
            and phonetic analysis. Upload your data, configure transcriptions, 
            and generate publication-ready outputs.
            """
        )
        
        st.markdown("")
        
        if st.button("🚀 Let's Begin", use_container_width=True, type="primary"):
            navigate_to(Screen.UPLOAD_DATABASE)
        
        st.markdown("")
        
        if st.button("ℹ️ About", use_container_width=True):
            navigate_to(Screen.ABOUT)
        
        st.markdown("")
        
        if st.button("📖 Tutorial", use_container_width=True):
            navigate_to(Screen.TUTORIAL)


def screen_about():
    """About page with app information."""
    st.title("About Excelerant")
    st.markdown("---")
    
    st.markdown(
        """
        ### Purpose
        
        Excelerant is a tool for linguists working with lexical databases. 
        It streamlines the workflow from raw data collection through 
        phonological analysis and acoustic phonetic measurements.
        
        ### Version
        
        Version 1.0.0
        
        ### Contact
        
        For questions or feedback, contact [your email here].
        """
    )
    
    st.markdown("---")
    
    if st.button("← Back", type="primary"):
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
    
    st.info("🎬 YouTube video will be embedded here")
    
    st.markdown("#### Video 2: Configuring Transcriptions")
    
    st.info("🎬 YouTube video will be embedded here")
    
    st.markdown("#### Video 3: Phonological Analysis")
    
    st.info("🎬 YouTube video will be embedded here")
    
    st.markdown("---")
    
    if st.button("← Back", type="primary"):
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
    
    st.title("📂 Upload Lexical Database")
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
                    ❌ **No valid sheets found.**
                    
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
                st.success(f"✅ Found valid sheet: **{sheet_name}**")
                
                result = load_sheet(uploaded_file, sheet_name)
                
                if not result.success:
                    st.error(f"❌ Error loading sheet: {result.error}")
                else:
                    df = result.df
                    st.session_state._temp_df = df
                    st.session_state._temp_filename = uploaded_file.name
                    st.session_state._temp_sheet = sheet_name
                    
                    st.markdown(f"**Rows:** {len(df):,} · **Columns:** {len(df.columns)}")
                    
                    # Validate the data
                    validation = validate_database(df)
                    
                    if not validation.valid:
                        st.error("❌ **Validation errors found. Please fix and re-upload.**")
                        
                        for col_name, issues in validation.errors.items():
                            with st.expander(f"⚠️ Issues in '{col_name}' column ({len(issues)} errors)", expanded=True):
                                if col_name == "index":
                                    st.markdown("All values in the `index` column must be integers.")
                                else:
                                    st.markdown(f"All values in the `{col_name}` column must be non-empty strings.")
                                
                                st.markdown("**Problematic rows:**")
                                for issue in issues[:20]:  # Show max 20
                                    st.text(f"  • {issue}")
                                if len(issues) > 20:
                                    st.text(f"  ... and {len(issues) - 20} more")
                    else:
                        st.success("✅ Data validation passed")
                        
                        st.markdown("---")
                        
                        if st.button("✓ Load Database", type="primary", use_container_width=True):
                            st.session_state.database = df
                            st.session_state.database_validated = True
                            st.session_state.database_filename = uploaded_file.name
                            st.session_state.database_sheet_name = sheet_name
                            
                            # Clean up temp state
                            for key in ["_temp_df", "_temp_filename", "_temp_sheet"]:
                                if key in st.session_state:
                                    del st.session_state[key]
                            
                            st.success("✅ Database loaded!")
                            navigate_to(Screen.MAIN_MENU)
            
            else:
                # Multiple valid sheets - user must choose
                st.warning(f"⚠️ Found {len(valid_sheets)} sheets with required columns. Please select one:")
                
                selected_sheet = st.selectbox(
                    "Select sheet",
                    options=valid_sheets,
                    help="Choose the sheet containing your lexical data"
                )
                
                if selected_sheet:
                    result = load_sheet(uploaded_file, selected_sheet)
                    
                    if not result.success:
                        st.error(f"❌ Error loading sheet: {result.error}")
                    else:
                        df = result.df
                        st.session_state._temp_df = df
                        st.session_state._temp_filename = uploaded_file.name
                        st.session_state._temp_sheet = selected_sheet
                        
                        st.markdown(f"**Rows:** {len(df):,} · **Columns:** {len(df.columns)}")
                        
                        # Validate the data
                        validation = validate_database(df)
                        
                        if not validation.valid:
                            st.error("❌ **Validation errors found. Please fix and re-upload.**")
                            
                            for col_name, issues in validation.errors.items():
                                with st.expander(f"⚠️ Issues in '{col_name}' column ({len(issues)} errors)", expanded=True):
                                    if col_name == "index":
                                        st.markdown("All values in the `index` column must be integers.")
                                    else:
                                        st.markdown(f"All values in the `{col_name}` column must be non-empty strings.")
                                    
                                    st.markdown("**Problematic rows:**")
                                    for issue in issues[:20]:  # Show max 20
                                        st.text(f"  • {issue}")
                                    if len(issues) > 20:
                                        st.text(f"  ... and {len(issues) - 20} more")
                        else:
                            st.success("✅ Data validation passed")
                            
                            st.markdown("---")
                            
                            if st.button("✓ Load Database", type="primary", use_container_width=True):
                                st.session_state.database = df
                                st.session_state.database_validated = True
                                st.session_state.database_filename = uploaded_file.name
                                st.session_state.database_sheet_name = selected_sheet
                                
                                # Clean up temp state
                                for key in ["_temp_df", "_temp_filename", "_temp_sheet"]:
                                    if key in st.session_state:
                                        del st.session_state[key]
                                
                                st.success("✅ Database loaded!")
                                navigate_to(Screen.MAIN_MENU)
        
        st.markdown("---")
        
        if st.button("← Back to Welcome"):
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
            
            with st.expander("📋 Columns", expanded=False):
                for col in df.columns:
                    marker = "✓" if col in REQUIRED_COLUMNS else "·"
                    st.text(f"{marker} {col}")
            
            with st.expander("📊 Data Preview", expanded=True):
                st.dataframe(df.head(10), use_container_width=True, height=300)


def screen_main_menu():
    """Main menu with task categories and info panel."""
    
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
    
    # st.markdown("---")
    
    # col1, col2, col3, col4, col5 = st.columns([1, 1, 1, 1, 1])
    # with col3:
    #     st.image("assets/excelerant_banner.png", use_container_width=True)
    
    # st.image("assets/excelerant_banner.png", width=400)
    
    # st.markdown("---")
    
    import base64

    with open("assets/excelerant_banner.png", "rb") as f:
        banner_data = base64.b64encode(f.read()).decode()
    
    st.markdown(
        f'<div style="display: flex; justify-content: center; margin-bottom: 1rem;"><img src="data:image/png;base64,{banner_data}" width="600"></div>',
        unsafe_allow_html=True,
    )
    
    st.markdown("---")
    
    # Two-column layout (1/3 left, 2/3 right)
    left_col, right_col = st.columns([1, 2])
    
    with left_col:
        
        # Iterate through categories
        for category in TASK_CATEGORIES:
            st.markdown(f"**{category}**")
            
            # Get tasks in this category
            category_tasks = [t for t in TASKS.values() if t.category == category]
            
            for task in category_tasks:
                # Determine if this task is selected
                is_selected = st.session_state.selected_task == task.id
                is_enabled = task.id in ENABLED_TASKS

                # Use different button style for selected
                if is_selected:
                    button_type = "primary"
                else:
                    button_type = "secondary"

                if st.button(
                    task.name,
                    key=f"btn_{task.id}",
                    use_container_width=True,
                    type=button_type,
                    disabled=not is_enabled,
                ):
                    st.session_state.selected_task = task.id
                    st.rerun()
            
            st.markdown("")  # Spacer between categories
    
    with right_col:
        if st.session_state.selected_task is None:
            # No task selected - show hint, database options, then preview
            st.info("👈 Select a task from the left panel to see details and begin.")
            
            # Database management
            with st.expander("📂 Database Options"):
                if st.button("Replace Database", use_container_width=True):
                    navigate_to(Screen.UPLOAD_DATABASE)
                
                if st.button("Clear Database & Start Over", use_container_width=True):
                    st.session_state.database = None
                    st.session_state.database_validated = False
                    st.session_state.database_filename = None
                    st.session_state.database_sheet_name = None
                    st.session_state.selected_task = None
                    navigate_to(Screen.WELCOME)
            
            st.markdown("---")
            
            st.subheader("Database Preview")
            
            df = st.session_state.database
            st.markdown(f"**Rows:** {len(df):,} · **Columns:** {len(df.columns)}")
            
            with st.expander("📋 Columns", expanded=False):
                for col in df.columns:
                    st.text(f"• {col}")
            
            with st.expander("📊 Data Preview", expanded=True):
                st.dataframe(df.head(10), use_container_width=True, height=300)
        
        else:
            # Show selected task info
            task = TASKS[st.session_state.selected_task]
            
            # Navigation buttons at top
            col1, col2 = st.columns([1, 1])
            
            with col1:
                if st.button("← Back to Preview", use_container_width=True):
                    st.session_state.selected_task = None
                    st.rerun()
            
            with col2:
                if st.button("Begin →", type="primary", use_container_width=True):
                    # Navigate to task screen based on selected task
                    task_screens = {
                        "create_data_collection_script": Screen.TASK_CREATE_DATA_COLLECTION_SCRIPT,
                        "add_audio_links": Screen.TASK_ADD_AUDIO_LINKS,
                    }
                    target_screen = task_screens.get(task.id, Screen.TASK_PLACEHOLDER)
                    navigate_to(target_screen)
            
            st.subheader(task.name)
            st.markdown(f"*{task.category}*")
            
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
                st.markdown(f"🎬 [Watch Tutorial]({task.youtube_url})")
            else:
                st.markdown("🎬 *Tutorial video coming soon*")


def screen_task_placeholder():
    """Placeholder for task screens."""
    task_id = st.session_state.selected_task

    if task_id and task_id in TASKS:
        task = TASKS[task_id]
        st.title(task.name)
    else:
        st.title("Task")

    st.markdown("---")

    st.info("🚧 This task is not yet implemented.")

    st.markdown("This is where the task-specific interface will go.")

    st.markdown("---")

    if st.button("← Back to Main Menu", type="primary"):
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

        if st.button("← Back to Main Menu", use_container_width=True):
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
                st.error(f"Error: {result.error}")
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
        if st.button("← Back to Main Menu", use_container_width=True):
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
                st.error(result.error)

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
                excel_data = prepare_and_export(
                    df=result.df,
                    path_col='path',
                    gloss_col='gloss',
                    add_links=False,  # Links already added by add_audio_links
                    reorder=True,
                    platform=platform,
                )

                st.download_button(
                    label="Download Updated Database",
                    data=excel_data,
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


# =============================================================================
# SCREEN ROUTER
# =============================================================================

SCREEN_FUNCTIONS: dict[str, Callable] = {
    Screen.WELCOME: screen_welcome,
    Screen.UPLOAD_DATABASE: screen_upload_database,
    Screen.MAIN_MENU: screen_main_menu,
    Screen.ABOUT: screen_about,
    Screen.TUTORIAL: screen_tutorial,
    Screen.TASK_PLACEHOLDER: screen_task_placeholder,
    Screen.TASK_CREATE_DATA_COLLECTION_SCRIPT: screen_create_data_collection_script,
    Screen.TASK_ADD_AUDIO_LINKS: screen_add_audio_links,
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
