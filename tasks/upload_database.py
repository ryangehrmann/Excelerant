"""
Upload Database Task
====================

Handles loading and validating lexical database spreadsheets.

Required columns: index, entry, gloss
- index: must contain integers (no blanks)
- entry: must contain strings; blank cells are allowed (untranscribed items)
- gloss: must contain strings; blank cells are allowed (unglossed items)

Blank entry/gloss cells don't block the upload. They're reported as warnings,
with the affected index values, so the user can follow up on them later.

The "Collect Data" flow runs before transcription exists, so it uses a
looser set (index + gloss only) - see COLLECT_REQUIRED_COLUMNS.
"""

import pandas as pd
from dataclasses import dataclass, field


REQUIRED_COLUMNS = ["index", "entry", "gloss"]

# Data collection happens before words are transcribed, so no "entry" column
# is expected yet - only an index and something to prompt with.
COLLECT_REQUIRED_COLUMNS = ["index", "gloss"]


@dataclass
class ValidationResult:
    """Result of database validation."""
    valid: bool
    errors: dict[str, list] = field(default_factory=dict)
    # Column name -> index values of rows whose cell in that column is blank
    blank_indices: dict[str, list[str]] = field(default_factory=dict)


@dataclass 
class SheetLoadResult:
    """Result of loading a sheet."""
    success: bool
    df: pd.DataFrame | None = None
    error: str | None = None


def find_valid_sheets(excel_file, required_columns: list[str] | None = None) -> list[str]:
    """
    Find all sheets that have the required columns.

    Args:
        excel_file: Uploaded file object or path to Excel file
        required_columns: Column names a sheet must contain (default: index, entry, gloss)

    Returns:
        List of sheet names that contain all required columns.
    """
    required_columns = required_columns or REQUIRED_COLUMNS
    valid_sheets = []

    try:
        xl = pd.ExcelFile(excel_file)

        for sheet_name in xl.sheet_names:
            df = pd.read_excel(xl, sheet_name=sheet_name)
            # Check if all required columns are present (case-insensitive)
            df_columns_lower = [col.lower().strip() for col in df.columns]

            if all(req.lower() in df_columns_lower for req in required_columns):
                valid_sheets.append(sheet_name)
                
    except Exception:
        return []
    
    return valid_sheets


def load_sheet(excel_file, sheet_name: str, required_columns: list[str] | None = None) -> SheetLoadResult:
    """
    Load a specific sheet and normalize required column names only.

    Args:
        excel_file: Uploaded file object or path to Excel file
        sheet_name: Name of the sheet to load
        required_columns: Column names to normalize to lowercase (default: index, entry, gloss)

    Returns:
        SheetLoadResult with success status, DataFrame (if successful), and error message (if failed)
    """
    required_columns = required_columns or REQUIRED_COLUMNS
    try:
        # Only truly empty cells count as missing. pandas' defaults would also
        # turn strings like "null", "nan", "NA", "None" into NaN, but those can
        # be legitimate glosses or entries in a lexical database.
        df = pd.read_excel(excel_file, sheet_name=sheet_name, keep_default_na=False, na_values=[""])

        # Strip whitespace from all column names
        df.columns = [col.strip() if isinstance(col, str) else col for col in df.columns]

        # Only normalize required columns to lowercase (preserve case for others like P, R, C, M, V, F, T)
        rename_map = {}
        for col in df.columns:
            if isinstance(col, str) and col.lower() in [r.lower() for r in required_columns]:
                if col != col.lower():
                    rename_map[col] = col.lower()

        if rename_map:
            df = df.rename(columns=rename_map)

        return SheetLoadResult(success=True, df=df)

    except Exception as e:
        return SheetLoadResult(success=False, error=str(e))


def format_index_value(val) -> str:
    """Render an index cell as text, dropping the '.0' pandas adds to whole numbers."""
    if isinstance(val, float) and val.is_integer():
        return str(int(val))
    return str(val)


def is_blank(val) -> bool:
    """True for NaN/None cells and strings that are empty or only whitespace."""
    return pd.isna(val) or (isinstance(val, str) and val.strip() == "")


def validate_database(df: pd.DataFrame, required_columns: list[str] | None = None) -> ValidationResult:
    """
    Validate the database contents.

    Checks (only for columns in required_columns):
    - 'index' column: all values must be integers (blanks are errors)
    - 'entry' and 'gloss' columns: non-blank values must be strings; blank
      cells are allowed and recorded in blank_indices

    Args:
        df: DataFrame to validate
        required_columns: Which columns to enforce (default: index, entry, gloss)

    Returns:
        ValidationResult with valid=True/False, dict of errors by column, and
        dict of blank-cell index values by column.
    """
    required_columns = required_columns or REQUIRED_COLUMNS
    errors = {}
    blank_indices = {}

    # Validate 'index' column - must be integers
    if "index" in required_columns and "index" in df.columns:
        invalid_indices = []
        for i, val in enumerate(df["index"]):
            if pd.isna(val):
                invalid_indices.append(f"Row {i+1}: empty")
            elif not isinstance(val, (int, float)) or (isinstance(val, float) and not val.is_integer()):
                invalid_indices.append(f"Row {i+1}: '{val}'")

        if invalid_indices:
            errors["index"] = invalid_indices

    # Validate 'entry' and 'gloss' columns - strings, blanks allowed
    for col in ("entry", "gloss"):
        if col not in required_columns or col not in df.columns:
            continue

        invalid_values = []
        blanks = []
        for i, val in enumerate(df[col]):
            if is_blank(val):
                if "index" in df.columns:
                    blanks.append(format_index_value(df["index"].iloc[i]))
                else:
                    blanks.append(f"row {i+1}")
            elif not isinstance(val, str):
                invalid_values.append(f"Row {i+1}: '{val}' (type: {type(val).__name__})")

        if invalid_values:
            errors[col] = invalid_values
        if blanks:
            blank_indices[col] = blanks

    return ValidationResult(
        valid=len(errors) == 0,
        errors=errors,
        blank_indices=blank_indices,
    )
