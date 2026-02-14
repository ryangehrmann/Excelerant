"""
Add Audio Links Task
====================

Links audio files to database entries by matching filenames to index values.

Supports:
- Windows and Mac platforms (different file generators and link formats)
- Phonological analysis (one audio per index) vs Acoustic Phonetic (one row per audio file)
- Subfolders representing categories (speaker, token, etc.)
- Delimited filenames with multiple categories
"""

import pandas as pd
from pathlib import Path, PureWindowsPath, PurePosixPath
from dataclasses import dataclass, field


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class FolderAnalysis:
    """Result of analyzing folder structure."""
    total_files: int
    has_subfolders: bool
    subfolder_names: list[str] = field(default_factory=list)
    error: str | None = None


@dataclass
class FilenameAnalysis:
    """Result of analyzing filename structure."""
    delimiter: str | None
    num_sections: int
    example_filename: str
    example_sections: list[str]
    all_integers: bool  # True if no delimiter and all filenames are just integers
    error: str | None = None


@dataclass
class AudioLinkResult:
    """Result of adding audio links to database."""
    success: bool
    df: pd.DataFrame | None = None
    files_matched: int = 0
    files_unmatched: int = 0
    rows_before: int = 0
    rows_after: int = 0
    error: str | None = None


# =============================================================================
# File Generators
# =============================================================================

def get_windows_batch_file() -> str:
    """Return Windows batch file content for generating file list."""
    return r'''@echo off
cls
color 0A
title File List Generator

echo ===============================================
echo           FILE LIST GENERATOR
echo ===============================================
echo.
echo This tool will create a text file listing all
echo files in your audio folder and its subfolders.
echo.
echo INSTRUCTIONS:
echo 1. Open your audio folder in File Explorer
echo 2. Drag and drop the folder into this window
echo 3. Press Enter
echo.
echo ===============================================
echo.

:INPUT
set "folder_path="
set /p folder_path="Drag your audio folder here and press Enter: "

:: Remove quotes if they exist (drag-drop adds them automatically)
set "folder_path=%folder_path:"=%"

:: Check if path was provided
if "%folder_path%"=="" (
    echo.
    echo ERROR: No folder path provided!
    echo.
    goto INPUT
)

:: Check if folder exists
if not exist "%folder_path%" (
    echo.
    echo ERROR: Folder does not exist or path is invalid!
    echo Please try again.
    echo.
    goto INPUT
)

echo.
echo Processing folder: %folder_path%
echo.
echo Generating file list...

:: Generate the file list
dir "%folder_path%" /s /b > filelist.txt

:: Check if file was created successfully
if exist filelist.txt (
    echo.
    echo ===============================================
    echo SUCCESS!
    echo.
    echo File 'filelist.txt' has been created in:
    echo %~dp0
    echo.
    echo You can now upload this file to the website.
    echo ===============================================
) else (
    echo.
    echo ERROR: Failed to create file list.
    echo Please check folder permissions and try again.
)

echo.
pause
'''


def get_mac_shell_script() -> str:
    """Return Mac/Linux shell script content for generating file list."""
    return r'''#!/bin/bash

clear
echo "==============================================="
echo "         FILE LIST GENERATOR (Mac)"
echo "==============================================="
echo ""
echo "This tool will create a text file listing all"
echo "files in your audio folder and its subfolders."
echo ""
echo "INSTRUCTIONS:"
echo "1. Drag and drop your audio folder into this"
echo "   Terminal window (or type the path)"
echo "2. Press Enter"
echo ""
echo "==============================================="
echo ""

# Get folder path from user
read -p "Drag your audio folder here and press Enter: " folder_path

# Remove quotes if present (drag-drop may add them)
folder_path="${folder_path%\"}"
folder_path="${folder_path#\"}"
folder_path="${folder_path%\'}"
folder_path="${folder_path#\'}"

# Remove trailing spaces
folder_path="${folder_path%% }"

# Check if path was provided
if [ -z "$folder_path" ]; then
    echo ""
    echo "ERROR: No folder path provided!"
    exit 1
fi

# Check if folder exists
if [ ! -d "$folder_path" ]; then
    echo ""
    echo "ERROR: Folder does not exist or path is invalid!"
    exit 1
fi

echo ""
echo "Processing folder: $folder_path"
echo ""
echo "Generating file list..."

# Get the directory where the script is located
script_dir="$(cd "$(dirname "$0")" && pwd)"

# Generate the file list
find "$folder_path" -type f > "$script_dir/filelist.txt"

# Check if file was created successfully
if [ -f "$script_dir/filelist.txt" ]; then
    echo ""
    echo "==============================================="
    echo "SUCCESS!"
    echo ""
    echo "File 'filelist.txt' has been created in:"
    echo "$script_dir"
    echo ""
    echo "You can now upload this file to the website."
    echo "==============================================="
else
    echo ""
    echo "ERROR: Failed to create file list."
    echo "Please check folder permissions and try again."
fi

echo ""
read -p "Press Enter to close..."
'''


# =============================================================================
# File List Parsing
# =============================================================================

def parse_file_list(content: str, platform: str) -> tuple[list[str], str | None]:
    """
    Parse uploaded file list content into list of .wav file paths.

    Args:
        content: Raw text content from filelist.txt
        platform: 'windows' or 'mac'

    Returns:
        Tuple of (list of file paths, error message or None)
    """
    lines = [line.strip() for line in content.split('\n') if line.strip()]

    # Filter to .wav files only (case-insensitive)
    wav_files = [x for x in lines if x.lower().endswith('.wav')]

    if not wav_files:
        return [], "No .wav files were found in the uploaded file list."

    return wav_files, None


def analyze_folder_structure(file_paths: list[str], platform: str) -> FolderAnalysis:
    """
    Analyze the folder structure of audio files.

    Determines if files are in subfolders and extracts subfolder names.
    Only supports one level of subfolders.
    """
    if not file_paths:
        return FolderAnalysis(
            total_files=0,
            has_subfolders=False,
            error="No files to analyze"
        )

    # Parse paths based on platform
    if platform == 'windows':
        paths = [PureWindowsPath(p) for p in file_paths]
    else:
        paths = [PurePosixPath(p) for p in file_paths]

    # Get parent folder names (immediate parent of each file)
    parents = list(set([p.parent.name for p in paths]))

    # If all files have the same parent, no subfolders
    if len(parents) == 1:
        return FolderAnalysis(
            total_files=len(file_paths),
            has_subfolders=False
        )

    # Multiple parents means subfolders exist
    # Check that we don't have more than one level of nesting
    grandparents = list(set([p.parent.parent.name for p in paths]))

    if len(grandparents) > 1:
        return FolderAnalysis(
            total_files=len(file_paths),
            has_subfolders=True,
            subfolder_names=parents,
            error="Audio folder contains more than one level of subfolders. "
                  "Please reorganize so all audio files are either in the main folder "
                  "or in one level of subfolders."
        )

    return FolderAnalysis(
        total_files=len(file_paths),
        has_subfolders=True,
        subfolder_names=sorted(parents)
    )


def analyze_filenames(file_paths: list[str], platform: str) -> FilenameAnalysis:
    """
    Analyze filename structure to detect delimiters and sections.
    """
    if not file_paths:
        return FilenameAnalysis(
            delimiter=None,
            num_sections=0,
            example_filename="",
            example_sections=[],
            all_integers=False,
            error="No files to analyze"
        )

    # Parse paths and get filenames without extension
    if platform == 'windows':
        paths = [PureWindowsPath(p) for p in file_paths]
    else:
        paths = [PurePosixPath(p) for p in file_paths]

    filenames = [p.stem for p in paths]  # stem = filename without extension
    example = filenames[0]

    # Check if all filenames are integers (simplest case)
    all_integers = all(fn.isdigit() for fn in filenames)

    if all_integers:
        return FilenameAnalysis(
            delimiter=None,
            num_sections=1,
            example_filename=example + ".wav",
            example_sections=[example],
            all_integers=True
        )

    # Check for delimiters (underscore first, then others)
    detected_delimiter = None
    for delim in ['_', '-', ' ']:
        if delim in example:
            detected_delimiter = delim
            break

    if detected_delimiter is None:
        # No delimiter, treat whole filename as one section
        return FilenameAnalysis(
            delimiter=None,
            num_sections=1,
            example_filename=example + ".wav",
            example_sections=[example],
            all_integers=False
        )

    # Split by delimiter
    sections = example.split(detected_delimiter)

    return FilenameAnalysis(
        delimiter=detected_delimiter,
        num_sections=len(sections),
        example_filename=example + ".wav",
        example_sections=sections,
        all_integers=False
    )


def validate_delimiter_consistency(file_paths: list[str], delimiter: str, platform: str) -> str | None:
    """
    Validate that all files have consistent delimiter counts.

    Returns error message if inconsistent, None if valid.
    """
    if platform == 'windows':
        paths = [PureWindowsPath(p) for p in file_paths]
    else:
        paths = [PurePosixPath(p) for p in file_paths]

    filenames = [p.stem for p in paths]

    # Count delimiters in each file
    delimiter_counts = {}
    for fn in filenames:
        count = fn.count(delimiter)
        delimiter_counts[count] = delimiter_counts.get(count, 0) + 1

    if len(delimiter_counts) > 1:
        details = [f"{num} file(s) with {count} delimiter(s)"
                   for count, num in sorted(delimiter_counts.items())]
        return f"Inconsistent delimiter counts: {', '.join(details)}. All files must have the same structure."

    return None


# =============================================================================
# Link Formatting
# =============================================================================

def format_link_windows(path: str) -> str:
    """
    Format link for Windows.

    Returns 'listen' - the excel_export module will add the actual hyperlink.
    """
    return "listen"


def format_link_mac(path: str) -> str:
    """
    Format link as terminal command for Mac.

    Mac users copy this command and paste into Terminal to play audio.
    """
    escaped_path = path.replace('"', '\\"')
    return f'open "{escaped_path}"'


# =============================================================================
# Database Operations
# =============================================================================

def extract_file_info(
    file_paths: list[str],
    platform: str,
    delimiter: str | None,
    section_categories: list[str] | None,
    subfolder_category: str | None
) -> list[dict]:
    """
    Extract structured information from file paths.

    Returns list of dicts with keys for each category (index, speaker, token, etc.)
    plus 'path' for the full file path.
    """
    if platform == 'windows':
        paths = [PureWindowsPath(p) for p in file_paths]
    else:
        paths = [PurePosixPath(p) for p in file_paths]

    file_info_list = []

    for i, path in enumerate(paths):
        info = {'path': file_paths[i]}  # Keep original path string

        # Extract filename without extension
        filename = path.stem

        # Parse filename sections
        if delimiter and section_categories:
            sections = filename.split(delimiter)
            for j, cat in enumerate(section_categories):
                if cat and cat != '-none-' and j < len(sections):
                    info[cat] = sections[j]
        else:
            # No delimiter - assume entire filename is index
            info['index'] = filename

        # Add subfolder category if applicable
        if subfolder_category and subfolder_category != '-none-':
            info[subfolder_category] = path.parent.name

        file_info_list.append(info)

    return file_info_list


def add_audio_links_phonological(
    df: pd.DataFrame,
    file_info_list: list[dict],
    index_col: str,
    platform: str,
    section_categories: list[str] | None = None,
    subfolder_category: str | None = None
) -> AudioLinkResult:
    """
    Add audio links for phonological analysis mode.

    One row per index - multiple audio files create multiple path/link columns.
    For example, with speakers M1/M2 and tokens 1/2, creates:
    link_M1_1, link_M1_2, link_M2_1, link_M2_2, path_M1_1, path_M1_2, etc.
    """
    df = df.copy()
    rows_before = len(df)

    # Identify non-index categories (these determine column suffixes)
    non_index_cats = []
    if section_categories:
        non_index_cats.extend([cat for cat in section_categories if cat and cat != 'index'])
    if subfolder_category:
        non_index_cats.append(subfolder_category)

    # Build mapping: index value -> list of file info dicts
    index_to_files: dict[str, list[dict]] = {}
    for info in file_info_list:
        idx_val = str(info.get('index', ''))
        if idx_val:
            if idx_val not in index_to_files:
                index_to_files[idx_val] = []
            index_to_files[idx_val].append(info)

    # If no non-index categories, use simple single path/link columns
    if not non_index_cats:
        df['path'] = None
        df['link'] = None

        for i, row in df.iterrows():
            idx_val = str(row[index_col])
            if idx_val in index_to_files and index_to_files[idx_val]:
                file_info = index_to_files[idx_val][0]  # Take first file
                path = file_info['path']
                df.at[i, 'path'] = path
                df.at[i, 'link'] = format_link_windows(path) if platform == 'windows' else format_link_mac(path)

        unique_matched = df[df['path'].notna()][index_col].nunique()
        unique_unmatched = df[df['path'].isna()][index_col].nunique()

        return AudioLinkResult(
            success=True,
            df=df,
            files_matched=unique_matched,
            files_unmatched=unique_unmatched,
            rows_before=rows_before,
            rows_after=len(df)
        )

    # Find all unique combinations of non-index category values
    # Each combination becomes a column suffix (e.g., "M1_1", "M1_2", "M2_1", "M2_2")
    all_combinations = set()
    for info in file_info_list:
        combo_parts = []
        for cat in non_index_cats:
            if cat in info:
                combo_parts.append(str(info[cat]))
        if combo_parts:
            all_combinations.add('_'.join(combo_parts))

    # Sort combinations for consistent column ordering
    sorted_combinations = sorted(all_combinations)

    # Create link and path columns for each combination
    for combo in sorted_combinations:
        df[f'link_{combo}'] = None
        df[f'path_{combo}'] = None

    # Populate columns for each row
    for i, row in df.iterrows():
        idx_val = str(row[index_col])
        if idx_val in index_to_files:
            for file_info in index_to_files[idx_val]:
                # Build the combination suffix for this file
                combo_parts = []
                for cat in non_index_cats:
                    if cat in file_info:
                        combo_parts.append(str(file_info[cat]))

                if combo_parts:
                    combo = '_'.join(combo_parts)
                    path = file_info['path']

                    df.at[i, f'path_{combo}'] = path
                    if platform == 'windows':
                        df.at[i, f'link_{combo}'] = format_link_windows(path)
                    else:
                        df.at[i, f'link_{combo}'] = format_link_mac(path)

    # Count matches - an index is "matched" if it has at least one path
    path_cols = [col for col in df.columns if col.startswith('path_')]
    if path_cols:
        has_any_path = df[path_cols].notna().any(axis=1)
        unique_matched = df[has_any_path][index_col].nunique()
        unique_unmatched = df[~has_any_path][index_col].nunique()
    else:
        unique_matched = 0
        unique_unmatched = df[index_col].nunique()

    return AudioLinkResult(
        success=True,
        df=df,
        files_matched=len(file_info_list),
        files_unmatched=unique_unmatched,
        rows_before=rows_before,
        rows_after=len(df)
    )


def add_audio_links_acoustic(
    df: pd.DataFrame,
    file_info_list: list[dict],
    index_col: str,
    platform: str,
    section_categories: list[str] | None,
    subfolder_category: str | None
) -> AudioLinkResult:
    """
    Add audio links for acoustic phonetic analysis mode.

    One row per audio file - database is expanded based on actual audio files.
    """
    df = df.copy()
    rows_before = len(df)

    # Identify which new category columns need to be added
    new_categories = set()
    if section_categories:
        for cat in section_categories:
            if cat and cat != '-none-' and cat != 'index' and cat not in df.columns:
                new_categories.add(cat)
    if subfolder_category and subfolder_category != '-none-' and subfolder_category not in df.columns:
        new_categories.add(subfolder_category)

    # Build expanded rows
    expanded_rows = []
    matched_indices = set()

    for file_info in file_info_list:
        file_index = str(file_info.get('index', ''))

        # Find matching rows in original df
        matching_rows = df[df[index_col].astype(str) == file_index]

        if len(matching_rows) == 0:
            continue

        matched_indices.add(file_index)

        # Create expanded rows for each matching original row
        for _, orig_row in matching_rows.iterrows():
            new_row = orig_row.copy()

            # Add path and link
            path = file_info['path']
            new_row['path'] = path
            if platform == 'windows':
                new_row['link'] = format_link_windows(path)
            else:
                new_row['link'] = format_link_mac(path)

            # Add category columns
            for cat in new_categories:
                if cat in file_info:
                    new_row[cat] = file_info[cat]

            expanded_rows.append(new_row)

    if not expanded_rows:
        return AudioLinkResult(
            success=False,
            error="No audio files could be matched to database entries. "
                  "Please check that: (1) the correct index column is selected, and "
                  "(2) filename index values match the values in your database. "
                  "If your database index values are incorrect, fix them in your Excel file, "
                  "then clear the database and re-upload."
        )

    # Create new dataframe
    df_expanded = pd.DataFrame(expanded_rows).reset_index(drop=True)

    # Count unmatched indices
    all_indices = set(df[index_col].astype(str).unique())
    unmatched_indices = all_indices - matched_indices

    return AudioLinkResult(
        success=True,
        df=df_expanded,
        files_matched=len(file_info_list),
        files_unmatched=len(unmatched_indices),
        rows_before=rows_before,
        rows_after=len(df_expanded)
    )


# =============================================================================
# Main Entry Point
# =============================================================================

def add_audio_links(
    df: pd.DataFrame,
    file_paths: list[str],
    platform: str,
    analysis_mode: str,
    index_col: str,
    delimiter: str | None,
    section_categories: list[str] | None,
    subfolder_category: str | None
) -> AudioLinkResult:
    """
    Main function to add audio links to database.

    Args:
        df: Original database DataFrame
        file_paths: List of audio file paths from uploaded file list
        platform: 'windows' or 'mac'
        analysis_mode: 'phonological' or 'acoustic'
        index_col: Name of index column in database
        delimiter: Delimiter character in filenames (or None)
        section_categories: List of category names for each filename section
        subfolder_category: Category name for subfolders (or None)

    Returns:
        AudioLinkResult with updated dataframe or error
    """
    # Extract structured info from file paths
    file_info_list = extract_file_info(
        file_paths,
        platform,
        delimiter,
        section_categories,
        subfolder_category
    )

    # Process based on analysis mode
    if analysis_mode == 'phonological':
        return add_audio_links_phonological(
            df, file_info_list, index_col, platform,
            section_categories, subfolder_category
        )
    else:
        return add_audio_links_acoustic(
            df, file_info_list, index_col, platform,
            section_categories, subfolder_category
        )
