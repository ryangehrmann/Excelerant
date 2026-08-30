"""
Excelerant Tasks
================

Each task module contains the logic for a specific data processing task.
UI code remains in app.py; these modules handle the actual processing.
"""

from .upload_database import (
    REQUIRED_COLUMNS,
    COLLECT_REQUIRED_COLUMNS,
    ValidationResult,
    SheetLoadResult,
    find_valid_sheets,
    load_sheet,
    validate_database,
)

from .create_data_collection_script import (
    ScriptResult,
    generate_script,
)

from .create_prompts_list import (
    PROMPTS_COLUMNS,
    PromptsListResult,
    generate_prompts_list,
)

from .standard_word_lists import (
    FRAME_PLACEHOLDER,
    GlossLanguage,
    WordListTool,
    list_word_list_tools,
    get_word_list_tool,
    load_word_list,
    available_gloss_languages,
    documentation_html,
    generate_tool_script,
    generate_tool_prompts_list,
    read_wordlist_bytes,
)

from .add_audio_links import (
    FolderAnalysis,
    FilenameAnalysis,
    AudioLinkResult,
    get_windows_batch_file,
    get_mac_shell_script,
    parse_file_list,
    analyze_folder_structure,
    analyze_filenames,
    validate_delimiter_consistency,
    add_audio_links,
)

from .excel_export import (
    PRIORITY_COLUMNS,
    reorder_columns,
    add_link_column,
    generate_excel_file,
    prepare_and_export,
    export_database,
)

from .check_database_formatting import (
    FORMATTING_REQUIRED_COLUMNS,
    ColumnMappingResult,
    ValidationError,
    FormattingCheckResult,
    detect_columns,
    check_database_formatting,
)

from .explode_entries import (
    ExplosionResult,
    explode_entries,
)

from .segment_words import (
    SegmentationResult,
    segment_words,
)

from .generate_cards import (
    BLANK_SENTINEL,
    Card,
    CardBuildResult,
    get_column_filter_options,
    filter_dataframe,
    sort_dataframe,
    build_cards,
    generate_cards_html,
    SORT_ACTIVITY_FORMAT,
    SORT_ACTIVITY_FORMAT_VERSION,
    build_sort_activity_filters,
    build_sort_activity_json,
)

from .process_cards import (
    ProcessCardsResult,
    sanitize_activity_column_name,
    parse_uid_list,
    process_cards_manual,
    AI_ASSISTED_PROMPT,
    AIOutputParseResult,
    derive_category_from_filename,
    parse_ai_assisted_output,
)

from .sort_cards import (
    generate_single_card_html,
    find_card_index_by_uid,
)

from .script_converter.pipelines.registry import PIPELINES as SCRIPT_CONVERTER_PIPELINES
from .script_converter.processors.xlsx_input import (
    load_xlsx,
    detect_entry_column,
    detect_index_column,
    validate_entry_column,
    prepare_df,
)
from .script_converter.processors.xlsx_output import FIXED_COLS, write_xlsx
from .script_converter.processors.text_input import read_text_file
from .script_converter.processors.text_output import build_ipa_only_docx, build_interlinear_html
from .script_converter.core.conversion import find_unknown_chars

__all__ = [
    # upload_database
    "REQUIRED_COLUMNS",
    "COLLECT_REQUIRED_COLUMNS",
    "ValidationResult",
    "SheetLoadResult",
    "find_valid_sheets",
    "load_sheet",
    "validate_database",
    # create_data_collection_script
    "ScriptResult",
    "generate_script",
    # create_prompts_list
    "PROMPTS_COLUMNS",
    "PromptsListResult",
    "generate_prompts_list",
    # standard_word_lists
    "FRAME_PLACEHOLDER",
    "GlossLanguage",
    "WordListTool",
    "list_word_list_tools",
    "get_word_list_tool",
    "load_word_list",
    "available_gloss_languages",
    "documentation_html",
    "generate_tool_script",
    "generate_tool_prompts_list",
    "read_wordlist_bytes",
    # add_audio_links
    "FolderAnalysis",
    "FilenameAnalysis",
    "AudioLinkResult",
    "get_windows_batch_file",
    "get_mac_shell_script",
    "parse_file_list",
    "analyze_folder_structure",
    "analyze_filenames",
    "validate_delimiter_consistency",
    "add_audio_links",
    # excel_export
    "PRIORITY_COLUMNS",
    "reorder_columns",
    "add_link_column",
    "generate_excel_file",
    "prepare_and_export",
    "export_database",
    # check_database_formatting
    "FORMATTING_REQUIRED_COLUMNS",
    "ColumnMappingResult",
    "ValidationError",
    "FormattingCheckResult",
    "detect_columns",
    "check_database_formatting",
    # explode_entries
    "ExplosionResult",
    "explode_entries",
    # segment_words
    "SegmentationResult",
    "segment_words",
    # generate_cards
    "BLANK_SENTINEL",
    "Card",
    "CardBuildResult",
    "get_column_filter_options",
    "filter_dataframe",
    "sort_dataframe",
    "build_cards",
    "generate_cards_html",
    "SORT_ACTIVITY_FORMAT",
    "SORT_ACTIVITY_FORMAT_VERSION",
    "build_sort_activity_filters",
    "build_sort_activity_json",
    # process_cards
    "ProcessCardsResult",
    "sanitize_activity_column_name",
    "parse_uid_list",
    "process_cards_manual",
    "AI_ASSISTED_PROMPT",
    "AIOutputParseResult",
    "derive_category_from_filename",
    "parse_ai_assisted_output",
    # sort_cards
    "generate_single_card_html",
    "find_card_index_by_uid",
    # script_converter
    "SCRIPT_CONVERTER_PIPELINES",
    "load_xlsx",
    "detect_entry_column",
    "detect_index_column",
    "validate_entry_column",
    "prepare_df",
    "FIXED_COLS",
    "write_xlsx",
    "read_text_file",
    "build_ipa_only_docx",
    "build_interlinear_html",
    "find_unknown_chars",
]
