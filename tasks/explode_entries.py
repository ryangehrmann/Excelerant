"""
Explode Entries Task
====================

Splits multi-word entries into one-word-per-row, adding 'sub_index' and 'word' columns.

Processing pipeline:
1. Validate entry column exists and has no NaN
2. Clean entry column (normalize whitespace, remove punctuation)
3. Preserve existing 'word' and 'sub_index' columns (rename to _old)
4. Build group key from index + categorical columns
5. Split entries by spaces -> 'word' column
6. Assign sub_index per group
7. Reorder columns and return result
"""

import re
import pandas as pd
import string
import unicodedata
from collections import Counter
from dataclasses import dataclass, field


@dataclass
class ExplosionResult:
    """Result of the explode entries operation."""
    success: bool
    df: pd.DataFrame | None = None
    error: str | None = None
    cleaning_report: dict = field(default_factory=dict)
    summary: dict = field(default_factory=dict)


def clean_transcription_column(df: pd.DataFrame, col: str) -> tuple[pd.DataFrame, dict]:
    """
    Clean a transcription column by normalizing whitespace and removing punctuation.

    Creates '{col}_orig' only if changes were made.

    Args:
        df: DataFrame to clean
        col: Column name to clean

    Returns:
        Tuple of (cleaned DataFrame, cleaning report dict)
    """
    df = df.copy()
    report = {
        "punctuation_removed": {},
        "whitespace_changes": 0,
        "changes_made": False,
    }

    # Save original for comparison
    original = df[col].copy()

    # Convert to string
    df[col] = df[col].astype(str)

    # Normalize Unicode whitespace to regular space
    unicode_spaces = [
        '\u00A0', '\u2000', '\u2001', '\u2002', '\u2003', '\u2004',
        '\u2005', '\u2006', '\u2007', '\u2008', '\u2009', '\u200A',
        '\u202F', '\u205F', '\u3000',
    ]
    for uspace in unicode_spaces:
        df[col] = df[col].str.replace(uspace, ' ', regex=False)

    # Count and remove punctuation
    all_text = ' '.join(df[col].dropna().astype(str))
    punct_counter = Counter(char for char in all_text if char in string.punctuation)
    if punct_counter:
        report["punctuation_removed"] = dict(punct_counter.most_common())
    translator = str.maketrans('', '', string.punctuation)
    df[col] = df[col].str.translate(translator)

    # Insert spaces at tone-marked syllable boundaries
    # Tone marks mid-string indicate a syllable break; insert space after them
    tone_break_pattern = r'([¹²³⁴⁵⁶⁷⁸⁹⁰˥˦˧˨˩]+)(?=[^\s¹²³⁴⁵⁶⁷⁸⁹⁰˥˦˧˨˩])'
    tone_before = df[col].copy()
    df[col] = df[col].str.replace(tone_break_pattern, r'\1 ', regex=True)
    report["tone_breaks_inserted"] = int((tone_before != df[col]).sum())

    # Normalize multiple whitespace to single space
    ws_before = df[col].copy()
    df[col] = df[col].str.replace(r'\s+', ' ', regex=True)
    report["whitespace_changes"] = int((ws_before != df[col]).sum())

    # Strip leading/trailing whitespace
    df[col] = df[col].str.strip()

    # Check if any changes were made
    changes_made = not df[col].equals(original.astype(str))
    report["changes_made"] = changes_made

    if changes_made:
        df[f'{col}_orig'] = original

    return df, report


def preserve_existing_column(df: pd.DataFrame, col_name: str) -> pd.DataFrame:
    """
    If col_name exists in df, rename it to '{col_name}_old' (with numerical
    suffixes if needed to avoid collisions).

    Args:
        df: DataFrame to modify
        col_name: Column name to preserve

    Returns:
        DataFrame with column renamed if it existed
    """
    if col_name not in df.columns:
        return df

    df = df.copy()
    new_name = f'{col_name}_old'

    # Handle collisions with numerical suffixes
    if new_name in df.columns:
        suffix = 1
        while f'{col_name}_old_{suffix}' in df.columns:
            suffix += 1
        new_name = f'{col_name}_old_{suffix}'

    df = df.rename(columns={col_name: new_name})
    return df


def explode_entries(
    df: pd.DataFrame,
    entry_col: str = 'entry',
    gloss_col: str = 'gloss',
    categorical_columns: list[str] | None = None,
) -> ExplosionResult:
    """
    Split multi-word entries into one-word-per-row.

    Adds 'sub_index' (word position within entry) and 'word' (individual word)
    columns. Groups by index + any categorical columns to handle multiple
    speakers/tokens correctly.

    Args:
        df: DataFrame with lexical data
        entry_col: Name of the column containing multi-word entries
        gloss_col: Name of the gloss column
        categorical_columns: Optional list of categorical columns (speaker, token, etc.)

    Returns:
        ExplosionResult with processed DataFrame
    """
    df = df.copy()
    cat_cols = categorical_columns or []

    # Step 1: Validate entry column exists
    if entry_col not in df.columns:
        return ExplosionResult(
            success=False,
            error=f"Entry column '{entry_col}' not found in database.",
        )

    # Check for NaN in entry column
    nan_count = df[entry_col].isna().sum()
    if nan_count > 0:
        return ExplosionResult(
            success=False,
            error=f"Found {nan_count} empty values in '{entry_col}' column. "
                  f"All entries must have values.",
        )

    # Step 2: Clean entry column
    df, cleaning_report = clean_transcription_column(df, entry_col)

    # Check if any entries became empty after cleaning
    empty_mask = df[entry_col] == ''
    if empty_mask.any():
        return ExplosionResult(
            success=False,
            error=f"After cleaning, {empty_mask.sum()} entries became empty. "
                  f"Please check your data for entries that are only punctuation.",
        )

    # Step 3: Preserve existing 'word' and 'sub_index' columns
    df = preserve_existing_column(df, 'word')
    df = preserve_existing_column(df, 'sub_index')

    rows_before = len(df)

    # Step 4: Build group key from index + categorical columns
    group_parts = [df['index'].astype(str)]
    for col in cat_cols:
        if col in df.columns:
            group_parts.append(df[col].astype(str))

    df['_group_key'] = group_parts[0]
    for part in group_parts[1:]:
        df['_group_key'] = df['_group_key'] + '_' + part

    # Step 5: Count spaces per entry (for sub_index ordering)
    df['_space_count'] = df[entry_col].str.count(' ')

    # Step 6: Split entries by spaces -> word column
    df = (df
          .assign(word=df[entry_col].str.split())
          .explode('word')
          .assign(word=lambda x: x['word'].fillna(''))
          .reset_index(drop=True))

    # Sort by group key and space count for proper ordering
    df = df.sort_values(['_group_key', '_space_count'], ascending=True)

    # Step 7: Assign sub_index per group
    df['sub_index'] = df.groupby('_group_key').cumcount() + 1
    df['sub_index'] = df['sub_index'].astype(int)

    # Sort by group key and sub_index for clean output
    df = df.sort_values(['_group_key', 'sub_index']).reset_index(drop=True)

    # Remove temporary columns
    df = df.drop(columns=['_group_key', '_space_count'])

    rows_after = len(df)
    entries_processed = rows_before
    words_created = rows_after

    # Build summary
    summary = {
        "entries_processed": entries_processed,
        "words_created": words_created,
        "rows_before": rows_before,
        "rows_after": rows_after,
    }

    return ExplosionResult(
        success=True,
        df=df,
        cleaning_report=cleaning_report,
        summary=summary,
    )
