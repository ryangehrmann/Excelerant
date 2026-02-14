"""
Excelerant Tasks
================

Each task module contains the logic for a specific data processing task.
UI code remains in app.py; these modules handle the actual processing.
"""

from .upload_database import (
    REQUIRED_COLUMNS,
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

__all__ = [
    # upload_database
    "REQUIRED_COLUMNS",
    "ValidationResult",
    "SheetLoadResult",
    "find_valid_sheets",
    "load_sheet",
    "validate_database",
    # create_data_collection_script
    "ScriptResult",
    "generate_script",
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
]
