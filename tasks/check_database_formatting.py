"""
Check Database Formatting Task
==============================

Validates database formatting and reconstructs entries from words.

Required columns: index, sub_index, entry, gloss, word

Untranscribed rows (blank entry and blank word, in a group with no other words)
are set aside before validation and added back afterwards with sub_index 1.

Validation checks:
- No colons in entry, word or segment columns (they may or may not be length
  marks, so the user resolves them)
- No blanks in index, sub_index, entry, word (except untranscribed rows)
- index values must be integers
- sub_index values must be integers
- entry values must be strings
- word values must be strings
- index+sub_index pairs must be unique
- sub_index must start at 1 and be sequential per index (auto-fixed if possible)

Processing:
- Converts lookalike/precomposed characters in entry, word and segment
  columns to Excelerant's forms (see segment_words.convert_precomposed)
- Creates new 'entry' from space-joined words in sub_index order per index group
- If any entry changed, archives the previous entries as
  'entry_before_YYYY-MM-DD' (today's date; '_2', '_3', ... for repeat runs on
  the same day), placed just before 'entry'. If nothing changed, nothing is
  archived. Every run that changes something adds one dated column, so the
  database keeps a history of its revisions.
"""

import datetime
from collections import Counter

import pandas as pd
from dataclasses import dataclass, field

from tasks.colon_check import (
    COLON_RECOMMENDATION,
    SEGMENT_COLUMNS,
    colon_error_message,
    find_colons,
)

from tasks.segment_words import convert_precomposed_column

# Temporary name for the pre-update entries while the new ones are built
_PREVIOUS_ENTRY = "_entry_before"


# Required columns for this task
FORMATTING_REQUIRED_COLUMNS = ["index", "sub_index", "entry", "gloss", "word"]


@dataclass
class ColumnMappingResult:
    """Result of column detection/mapping."""
    success: bool
    column_mapping: dict[str, str] = field(default_factory=dict)  # required_name -> actual_name
    missing_columns: list[str] = field(default_factory=list)
    normalized_columns: list[str] = field(default_factory=list)  # columns that needed case normalization


@dataclass
class ValidationError:
    """A single validation error with details."""
    error_type: str
    message: str
    details: list[str] = field(default_factory=list)
    recommendation: str = ""
    # Column -> row IDs of cells containing colons (error_type "colons")
    colon_locations: dict[str, list[str]] = field(default_factory=dict)


@dataclass
class FormattingCheckResult:
    """Result of the formatting check and entry reconstruction."""
    success: bool
    df: pd.DataFrame | None = None
    error: ValidationError | None = None
    auto_fixes_applied: list[str] = field(default_factory=list)
    summary: dict = field(default_factory=dict)


def detect_columns(df: pd.DataFrame) -> ColumnMappingResult:
    """
    Detect required columns in the dataframe (case-insensitive).

    Args:
        df: DataFrame to analyze

    Returns:
        ColumnMappingResult with mapping of required names to actual column names,
        and list of any missing columns.
    """
    column_mapping = {}
    missing_columns = []
    normalized_columns = []

    # Create lowercase mapping of actual columns
    actual_columns = list(df.columns)
    lowercase_to_actual = {col.lower(): col for col in actual_columns}

    for required_col in FORMATTING_REQUIRED_COLUMNS:
        if required_col in actual_columns:
            # Exact match
            column_mapping[required_col] = required_col
        elif required_col.lower() in lowercase_to_actual:
            # Case-insensitive match
            actual_col = lowercase_to_actual[required_col.lower()]
            column_mapping[required_col] = actual_col
            if actual_col != required_col:
                normalized_columns.append(f"'{actual_col}' -> '{required_col}'")
        else:
            missing_columns.append(required_col)

    return ColumnMappingResult(
        success=len(missing_columns) == 0,
        column_mapping=column_mapping,
        missing_columns=missing_columns,
        normalized_columns=normalized_columns,
    )


def normalize_dataframe_columns(df: pd.DataFrame, column_mapping: dict[str, str]) -> pd.DataFrame:
    """
    Normalize required column names to lowercase standard names.

    Only renames columns that are in the mapping (the required columns).
    Other columns (like P, R, C, M, V, F, T) are left unchanged.

    Args:
        df: DataFrame to normalize
        column_mapping: Mapping from required name to actual name

    Returns:
        DataFrame with normalized column names for required columns only
    """
    df = df.copy()

    # Build rename mapping (actual -> required) for required columns only
    rename_map = {actual: required for required, actual in column_mapping.items() if actual != required}

    if rename_map:
        df = df.rename(columns=rename_map)

    return df


def _is_blank(series: pd.Series) -> pd.Series:
    """True for NaN cells and cells that are empty or only whitespace."""
    return series.isna() | (series.astype(str).str.strip() == "")


def find_untranscribed_rows(
    df: pd.DataFrame,
    categorical_columns: list[str] | None = None,
) -> pd.Series:
    """
    Mask of untranscribed rows: blank entry and blank word, with an index and
    no other row in the same group (index + categorical columns) that has a word.

    A blank word inside a group that has other words is a real gap, so those
    rows are left for validate_no_blanks to report.
    """
    cat_cols = categorical_columns or []
    group_cols = ["index"] + cat_cols

    candidate = _is_blank(df["entry"]) & _is_blank(df["word"]) & ~df["index"].isna()
    group_has_word = (~_is_blank(df["word"])).groupby(
        [df[col].astype(str) for col in group_cols]
    ).transform("any")

    return candidate & ~group_has_word


def validate_no_blanks(df: pd.DataFrame) -> ValidationError | None:
    """
    Check that index, sub_index, entry, and word columns have no blanks.

    Args:
        df: DataFrame to validate

    Returns:
        ValidationError if blanks found, None otherwise
    """
    columns_to_check = ["index", "sub_index", "entry", "word"]
    blank_details = []

    for col in columns_to_check:
        if col not in df.columns:
            continue

        # Find blank/null rows
        blank_mask = df[col].isna() | (df[col].astype(str).str.strip() == "")
        blank_rows = df.index[blank_mask].tolist()

        if blank_rows:
            for row_idx in blank_rows[:10]:  # Show first 10
                blank_details.append(f"Row {row_idx + 2}: '{col}' is blank")  # +2 for header + 0-index
            if len(blank_rows) > 10:
                blank_details.append(f"... and {len(blank_rows) - 10} more blank values in '{col}'")

    if blank_details:
        return ValidationError(
            error_type="blank_values",
            message="Blank values found in required columns",
            details=blank_details,
            recommendation=(
                "All values in 'index', 'sub_index', 'entry', and 'word' columns must be filled. "
                "Please fix the rows listed above in your Excel file, then clear the database and re-upload."
            )
        )

    return None


def validate_index_integers(df: pd.DataFrame) -> ValidationError | None:
    """
    Check that all index values are integers.

    Args:
        df: DataFrame to validate

    Returns:
        ValidationError if non-integers found, None otherwise
    """
    invalid_details = []

    for i, val in df["index"].items():
        if pd.isna(val):
            continue  # Already checked by validate_no_blanks

        # Check if it's a valid integer
        if isinstance(val, (int,)):
            continue
        elif isinstance(val, float):
            if not val.is_integer():
                invalid_details.append(f"Row {i + 2}: '{val}' (decimal number)")
            # else it's a float that represents an integer, which is OK
        else:
            invalid_details.append(f"Row {i + 2}: '{val}' (type: {type(val).__name__})")

    if invalid_details:
        return ValidationError(
            error_type="invalid_index_type",
            message="Non-integer values found in 'index' column",
            details=invalid_details[:20] + (["... and more"] if len(invalid_details) > 20 else []),
            recommendation=(
                "All values in the 'index' column must be whole numbers (integers). "
                "Please fix the values listed above in your Excel file, then clear the database and re-upload."
            )
        )

    return None


def validate_sub_index_integers(df: pd.DataFrame) -> ValidationError | None:
    """
    Check that all sub_index values are integers.

    Args:
        df: DataFrame to validate

    Returns:
        ValidationError if non-integers found, None otherwise
    """
    invalid_details = []

    for i, val in df["sub_index"].items():
        if pd.isna(val):
            continue  # Already checked by validate_no_blanks

        # Check if it's a valid integer
        if isinstance(val, (int,)):
            continue
        elif isinstance(val, float):
            if not val.is_integer():
                invalid_details.append(f"Row {i + 2}: '{val}' (decimal number)")
            # else it's a float that represents an integer, which is OK
        else:
            invalid_details.append(f"Row {i + 2}: '{val}' (type: {type(val).__name__})")

    if invalid_details:
        return ValidationError(
            error_type="invalid_sub_index_type",
            message="Non-integer values found in 'sub_index' column",
            details=invalid_details[:20] + (["... and more"] if len(invalid_details) > 20 else []),
            recommendation=(
                "All values in the 'sub_index' column must be whole numbers (integers). "
                "Please fix the values listed above in your Excel file, then clear the database and re-upload."
            )
        )

    return None


def validate_entry_strings(df: pd.DataFrame) -> ValidationError | None:
    """
    Check that all entry values are strings.

    Args:
        df: DataFrame to validate

    Returns:
        ValidationError if non-strings found, None otherwise
    """
    invalid_details = []

    for i, val in df["entry"].items():
        if pd.isna(val):
            continue  # Already checked by validate_no_blanks

        if not isinstance(val, str):
            invalid_details.append(f"Row {i + 2}: '{val}' (type: {type(val).__name__})")

    if invalid_details:
        return ValidationError(
            error_type="invalid_entry_type",
            message="Non-string values found in 'entry' column",
            details=invalid_details[:20] + (["... and more"] if len(invalid_details) > 20 else []),
            recommendation=(
                "All values in the 'entry' column must be text strings. "
                "If you have numeric entries, format them as text in your Excel file, then clear the database and re-upload."
            )
        )

    return None


def validate_word_strings(df: pd.DataFrame) -> ValidationError | None:
    """
    Check that all word values are strings.

    Args:
        df: DataFrame to validate

    Returns:
        ValidationError if non-strings found, None otherwise
    """
    invalid_details = []

    for i, val in df["word"].items():
        if pd.isna(val):
            continue  # Already checked by validate_no_blanks

        if not isinstance(val, str):
            invalid_details.append(f"Row {i + 2}: '{val}' (type: {type(val).__name__})")

    if invalid_details:
        return ValidationError(
            error_type="invalid_word_type",
            message="Non-string values found in 'word' column",
            details=invalid_details[:20] + (["... and more"] if len(invalid_details) > 20 else []),
            recommendation=(
                "All values in the 'word' column must be text strings. "
                "If you have numeric words, format them as text in your Excel file, then clear the database and re-upload."
            )
        )

    return None


def validate_unique_index_sub_index(
    df: pd.DataFrame,
    categorical_columns: list[str] | None = None,
) -> ValidationError | None:
    """
    Check that all index+sub_index (+ categorical columns) combinations are unique.

    Args:
        df: DataFrame to validate
        categorical_columns: Optional list of additional categorical columns to include
                           in uniqueness check (e.g., ['speaker', 'token'])

    Returns:
        ValidationError if duplicates found, None otherwise
    """
    df_temp = df.copy()
    cat_cols = categorical_columns or []

    # Build the key columns
    key_columns = ["index", "sub_index"] + cat_cols

    # Create a combined key for display purposes
    key_parts = [df_temp["index"].astype(str), df_temp["sub_index"].astype(str)]
    for col in cat_cols:
        key_parts.append(df_temp[col].astype(str))
    df_temp["_key"] = key_parts[0]
    for part in key_parts[1:]:
        df_temp["_key"] = df_temp["_key"] + "_" + part

    # Find duplicates
    duplicates = df_temp[df_temp.duplicated(subset=["_key"], keep=False)]

    if len(duplicates) > 0:
        # Group by the duplicate keys to show details
        duplicate_keys = duplicates["_key"].unique()
        details = []

        # Build column description for error message
        col_desc = "index + sub_index"
        if cat_cols:
            col_desc += " + " + " + ".join(cat_cols)

        for key in duplicate_keys[:10]:  # Show first 10 duplicate groups
            dup_rows = df_temp[df_temp["_key"] == key].index.tolist()
            row_nums = [str(r + 2) for r in dup_rows]  # +2 for header + 0-index
            details.append(f"Key '{key}' appears in rows: {', '.join(row_nums)}")

        if len(duplicate_keys) > 10:
            details.append(f"... and {len(duplicate_keys) - 10} more duplicate combinations")

        return ValidationError(
            error_type="duplicate_index_sub_index",
            message=f"Duplicate {col_desc} combinations found",
            details=details,
            recommendation=(
                f"Each combination of {col_desc} must be unique. "
                "This error occurs when the same grouping has duplicate sub_index values. "
                "Please ensure each word within a group has a unique sub_index value (typically 1, 2, 3, etc.) "
                "in your Excel file, then clear the database and re-upload."
            )
        )

    return None


def validate_unique_untranscribed(
    df: pd.DataFrame,
    categorical_columns: list[str] | None = None,
) -> ValidationError | None:
    """
    Check that untranscribed rows don't repeat a group (index + categorical
    columns), since each one becomes sub_index 1 of its group.
    """
    cat_cols = categorical_columns or []
    group_cols = ["index"] + cat_cols
    keys = df[group_cols].astype(str).agg("_".join, axis=1) if len(df) else pd.Series(dtype=str)
    duplicated = keys[keys.duplicated(keep=False)]

    if len(duplicated) == 0:
        return None

    details = []
    for key in duplicated.unique()[:10]:
        row_nums = [str(r + 2) for r in duplicated[duplicated == key].index]
        details.append(f"Key '{key}' appears in rows: {', '.join(row_nums)}")

    col_desc = " + ".join(group_cols)
    return ValidationError(
        error_type="duplicate_untranscribed",
        message=f"Duplicate {col_desc} combinations among rows with no entry or word",
        details=details,
        recommendation=(
            f"Each {col_desc} combination can appear only once among untranscribed rows. "
            "Please remove the extra rows in your Excel file, then clear the database and re-upload."
        ),
    )


def validate_and_fix_sub_index_sequences(
    df: pd.DataFrame,
    categorical_columns: list[str] | None = None,
) -> tuple[pd.DataFrame | None, ValidationError | None, list[str]]:
    """
    Check sub_index sequences per group and auto-fix if possible.

    For each group (index + categorical columns):
    - sub_indices must be unique (error if not - user must fix)
    - sub_indices should start at 1 and be sequential
    - If unique but not starting at 1 or has gaps, auto-renumber from 1

    Args:
        df: DataFrame to validate
        categorical_columns: Optional list of additional categorical columns to group by

    Returns:
        Tuple of (fixed_df or None, error or None, list of auto-fixes applied)
    """
    df = df.copy()
    auto_fixes = []
    cat_cols = categorical_columns or []

    # Convert to int for proper sorting/comparison
    df["index"] = df["index"].astype(int)
    df["sub_index"] = df["sub_index"].astype(int)

    # Build group columns
    group_cols = ["index"] + cat_cols

    # Group by index (and categorical columns if any) and check each group
    for group_key, group in df.groupby(group_cols):
        # Make group_key always a tuple for consistent handling
        if not isinstance(group_key, tuple):
            group_key = (group_key,)

        sub_indices = group["sub_index"].tolist()

        # Build group description for messages
        if cat_cols:
            group_desc = ", ".join(f"{col}={val}" for col, val in zip(group_cols, group_key))
        else:
            group_desc = f"index={group_key[0]}"

        # Check for duplicates within this group
        if len(sub_indices) != len(set(sub_indices)):
            # Find which sub_indices are duplicated
            seen = set()
            duplicates = set()
            for si in sub_indices:
                if si in seen:
                    duplicates.add(si)
                seen.add(si)

            dup_details = []
            for dup_si in sorted(duplicates):
                dup_rows = group[group["sub_index"] == dup_si].index.tolist()
                row_nums = [str(r + 2) for r in dup_rows]
                dup_details.append(f"{group_desc}, sub_index={dup_si} appears in rows: {', '.join(row_nums)}")

            col_desc = "index" + (f" + {' + '.join(cat_cols)}" if cat_cols else "")

            return None, ValidationError(
                error_type="duplicate_sub_index_in_group",
                message=f"Duplicate sub_index values found within group ({group_desc})",
                details=dup_details,
                recommendation=(
                    f"Within each {col_desc} group, sub_index values must be unique. "
                    "This error cannot be auto-fixed because duplicate sub_indices create ambiguity "
                    "about the correct word order. Please manually assign unique sub_index values "
                    "(1, 2, 3, etc.) to each word within this group in your Excel file, then clear the database and re-upload."
                )
            ), []

        # Check if sequence is correct (starts at 1, no gaps)
        sorted_sub_indices = sorted(sub_indices)
        expected = list(range(1, len(sub_indices) + 1))

        if sorted_sub_indices != expected:
            # Auto-fix: renumber from 1 based on current order
            # Sort the group by current sub_index and assign new sequential values
            group_sorted = group.sort_values("sub_index")
            new_sub_indices = list(range(1, len(group_sorted) + 1))

            # Update the dataframe
            for new_si, (orig_idx, _) in zip(new_sub_indices, group_sorted.iterrows()):
                df.at[orig_idx, "sub_index"] = new_si

            auto_fixes.append(
                f"{group_desc}: sub_indices {sorted_sub_indices} renumbered to {expected}"
            )

    return df, None, auto_fixes


def archive_column_name(existing_columns, today: datetime.date | None = None) -> str:
    """'entry_before_YYYY-MM-DD' for today, with '_2', '_3', ... appended if
    that name is already taken by an earlier run the same day."""
    base = f"entry_before_{(today or datetime.date.today()).isoformat()}"
    name, n = base, 2
    while name in existing_columns:
        name, n = f"{base}_{n}", n + 1
    return name


def _archive_previous_entries(
    df: pd.DataFrame,
    today: datetime.date | None = None,
) -> tuple[pd.DataFrame, str | None, int]:
    """Keep the pre-update entries (held in _PREVIOUS_ENTRY) as a dated column
    just before 'entry' if any entry changed; otherwise drop them.

    Returns (df, archive column name or None, number of rows whose entry changed).
    """
    def normalized(series):
        return series.fillna("").astype(str).str.strip()

    changed_rows = int((normalized(df[_PREVIOUS_ENTRY]) != normalized(df["entry"])).sum())

    if changed_rows == 0:
        return df.drop(columns=[_PREVIOUS_ENTRY]), None, 0

    name = archive_column_name(df.columns, today)
    previous = df.pop(_PREVIOUS_ENTRY)
    df.insert(df.columns.get_loc("entry"), name, previous)
    return df, name, changed_rows


def reconstruct_entries(
    df: pd.DataFrame,
    categorical_columns: list[str] | None = None,
) -> pd.DataFrame:
    """
    Reconstruct entries from words.

    - Moves the current 'entry' to a temporary column (_PREVIOUS_ENTRY) so
      check_database_formatting can decide whether to archive it
    - Creates new 'entry' by joining words in sub_index order per group

    Args:
        df: DataFrame with validated data
        categorical_columns: Optional list of additional categorical columns to group by

    Returns:
        DataFrame with the previous entries (temporary column) and new entry column
    """
    df = df.copy()
    cat_cols = categorical_columns or []

    df = df.rename(columns={"entry": _PREVIOUS_ENTRY})

    # Build group columns and sort columns
    group_cols = ["index"] + cat_cols
    sort_cols = group_cols + ["sub_index"]

    # Sort by group columns and sub_index to ensure correct order
    df = df.sort_values(sort_cols).reset_index(drop=True)

    # Group by index (and categorical columns) and join words
    entry_series = df.groupby(group_cols)["word"].apply(lambda x: " ".join(x.astype(str)))

    # Create a mapping key for each row to look up the entry
    if cat_cols:
        # Create a tuple key for each row
        df["_group_key"] = list(zip(*[df[col] for col in group_cols]))
        entry_mapping = entry_series.to_dict()
        df["entry"] = df["_group_key"].map(entry_mapping)
        df = df.drop(columns=["_group_key"])
    else:
        # Simple case - just index
        entry_mapping = entry_series.to_dict()
        df["entry"] = df["index"].map(entry_mapping)

    return df


def check_database_formatting(
    df: pd.DataFrame,
    column_mapping: dict[str, str] | None = None,
    categorical_columns: list[str] | None = None,
    today: datetime.date | None = None,
) -> FormattingCheckResult:
    """
    Main function to check database formatting and reconstruct entries.

    Performs all validation checks in order, stopping at first error.
    If all validations pass, reconstructs entries from words.

    Args:
        df: DataFrame to validate and process
        column_mapping: Optional mapping of required column names to actual column names.
                       If provided, columns will be renamed accordingly.
        categorical_columns: Optional list of additional categorical columns (e.g., 'speaker', 'token')
                           to include in uniqueness checks and grouping.
        today: Date used in the archive column name (default: today's date)

    Returns:
        FormattingCheckResult with success status, processed DataFrame, and any errors.
    """
    df = df.copy()
    auto_fixes = []
    cat_cols = categorical_columns or []

    # Step 1: Normalize column names if mapping provided
    if column_mapping:
        df = normalize_dataframe_columns(df, column_mapping)

    # Colons in entries, words or segments may or may not be length marks, so
    # the user must resolve them
    colon_locations = find_colons(df, ["entry", "word"] + SEGMENT_COLUMNS)
    if colon_locations:
        return FormattingCheckResult(success=False, error=ValidationError(
            error_type="colons",
            message=colon_error_message(colon_locations),
            recommendation=COLON_RECOMMENDATION,
            colon_locations=colon_locations,
        ))

    # Convert lookalike/precomposed characters to Excelerant's forms. Done to
    # 'entry' too, so a change of storage form alone doesn't count as a
    # changed entry when deciding whether to archive.
    characters_converted = Counter()
    for col in ["entry", "word"] + SEGMENT_COLUMNS:
        if col in df.columns:
            df[col], col_counts = convert_precomposed_column(df[col])
            characters_converted.update(col_counts)

    # Set aside untranscribed rows; they skip validation and reconstruction
    untranscribed_mask = find_untranscribed_rows(df, categorical_columns=cat_cols)

    # Step 2: Validate no blanks
    error = validate_no_blanks(df[~untranscribed_mask])
    if error:
        return FormattingCheckResult(success=False, error=error)

    # Step 3: Validate index integers (all rows, including untranscribed)
    error = validate_index_integers(df)
    if error:
        return FormattingCheckResult(success=False, error=error)

    df_untranscribed = df[untranscribed_mask].copy()
    df = df[~untranscribed_mask]

    error = validate_unique_untranscribed(df_untranscribed, categorical_columns=cat_cols)
    if error:
        return FormattingCheckResult(success=False, error=error)

    # Step 4: Validate sub_index integers
    error = validate_sub_index_integers(df)
    if error:
        return FormattingCheckResult(success=False, error=error)

    # Step 5: Validate entry strings
    error = validate_entry_strings(df)
    if error:
        return FormattingCheckResult(success=False, error=error)

    # Step 6: Validate word strings
    error = validate_word_strings(df)
    if error:
        return FormattingCheckResult(success=False, error=error)

    # Step 7: Validate unique index+sub_index (+ categorical columns) combinations
    error = validate_unique_index_sub_index(df, categorical_columns=cat_cols)
    if error:
        return FormattingCheckResult(success=False, error=error)

    # Step 8: Validate and fix sub_index sequences (per group)
    df, error, fixes = validate_and_fix_sub_index_sequences(df, categorical_columns=cat_cols)
    if error:
        return FormattingCheckResult(success=False, error=error)
    auto_fixes.extend(fixes)

    # Step 9: Reconstruct entries from words (per group)
    df = reconstruct_entries(df, categorical_columns=cat_cols)

    # Add untranscribed rows back: blank entry/word, sub_index 1
    if len(df_untranscribed) > 0:
        df_untranscribed = df_untranscribed.rename(columns={"entry": _PREVIOUS_ENTRY})
        df_untranscribed["entry"] = ""
        df_untranscribed["word"] = ""
        df_untranscribed["index"] = df_untranscribed["index"].astype(int)
        df_untranscribed["sub_index"] = 1
        sort_cols = ["index"] + cat_cols + ["sub_index"]
        df = (pd.concat([df, df_untranscribed], ignore_index=True)
              .sort_values(sort_cols, kind="stable")
              .reset_index(drop=True))

    # Archive the previous entries as a dated column, if anything changed
    df, archive_column, entries_changed = _archive_previous_entries(df, today)

    # Build summary
    num_indices = df["index"].nunique()
    num_rows = len(df)

    summary = {
        "total_rows": num_rows,
        "unique_indices": num_indices,
        "untranscribed_rows": len(df_untranscribed),
        "entries_changed": entries_changed,
        "characters_converted": dict(characters_converted.most_common()),
        "archive_column": archive_column,
        "auto_fixes_count": len(auto_fixes),
        "categorical_columns": cat_cols,
    }

    return FormattingCheckResult(
        success=True,
        df=df,
        auto_fixes_applied=auto_fixes,
        summary=summary,
    )
