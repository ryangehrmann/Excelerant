"""
ui/tasks_registry.py
Task catalog: what tasks exist, their metadata, which are enabled, and
which menu category each belongs to.
"""

from dataclasses import dataclass


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
    # Collect Lexical Data
    "create_data_collection_script": TaskInfo(
        id="create_data_collection_script",
        name="Create Data Collection Script",
        category="Collect Lexical Data",
        description="Generate an XML script for [SpeechRecorder](https://www.bas.uni-muenchen.de/Bas/software/speechrecorder/) to collect audio recordings. Maps database columns to prompt fields (gloss, index, frame, extra info) and supports multiple token repetitions.",
        requirements=[
            "Database must have 'index' and 'gloss' columns populated",
            "Each index value must be unique",
        ],
        example="Input: Lexical database\nOutput: XML script for SpeechRecorder with prompts for each entry",
        youtube_url=None,
    ),
    "create_prompts_list": TaskInfo(
        id="create_prompts_list",
        name="Create Prompts List (Android)",
        category="Collect Lexical Data",
        description="Generate a prompt-list file for the **Prompts** Android app - an offline, one-prompt-at-a-time audio elicitation app for recording in the field straight from a phone. Maps database columns to the app's fields (vernacular gloss shown large, optional English gloss and IPA for the surveyor) and exports a .csv or .xlsx the app imports.",
        requirements=[
            "Database must have an 'index' column and a column of text to prompt with",
            "Each index value must be unique (the app saves one recording per index)",
        ],
        example="Input: Lexical database\nOutput: prompts.csv (index, gloss_v, gloss_e, ipa) for the Prompts app",
        youtube_url=None,
    ),

    # Configure Audio
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
    "sort_cards": TaskInfo(
        id="sort_cards",
        name="Sort Cards",
        category="Orthography Development",
        description="Digital, in-app card sorting -- an alternative to printing cards when that isn't practical, or for handing a sorting task off to someone else. One card is shown at a time; assign it to a pile (or skip it) until the deck is empty, naming piles as you go. Sort Cards doesn't write to the database itself -- finish a sort to export a results file, then bring it into the database with Process Cards.",
        requirements=[
            "Database must have an 'index' column (a 'sub_index' column is used automatically if present)",
            "Each index (or index + sub_index) among the rows you sort must be unique",
        ],
        example="Input: Lexical database\nOutput: A sorting-activity file ready to import in Process Cards",
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
    "Collect Lexical Data",
    "Configure Audio",
    "Configure Transcriptions",
    "Phonological Analysis",
    "Orthography Development",
    "Acoustic Phonetic Analysis",
]

# Tasks that are currently implemented and enabled
ENABLED_TASKS = {
    "create_data_collection_script",
    "create_prompts_list",
    "add_audio_links",
    "explode_entries",
    "segment_words",
    "update_entries_from_words",
    "generate_cards",
    "process_cards",
    "sort_cards",
}

# Which task categories appear on each analysis mode's main menu.
# (Tasks are filtered by both ENABLED_TASKS and this mapping, so a task
# belongs on exactly the menu(s) for its category.)
MENU_CATEGORIES = {
    "collect": ["Collect Lexical Data"],
    # Audio linking + transcription prep - database housekeeping, not analysis.
    "manage": ["Configure Audio", "Configure Transcriptions"],
    "phonological": ["Phonological Analysis"],
    "orthography": ["Orthography Development"],
    "acoustic": ["Acoustic Phonetic Analysis"],
}
