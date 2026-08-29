"""
Upload Database Task
====================

Handles loading and validating lexical database spreadsheets.

Required columns: index, entry, gloss
- index: must contain integers
- entry: must contain non-empty strings
- gloss: must contain non-empty strings

The "Collect Lexical Data" flow runs before transcription exists, so it uses a
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
        df = pd.read_excel(excel_file, sheet_name=sheet_name)

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


def validate_database(df: pd.DataFrame, required_columns: list[str] | None = None) -> ValidationResult:
    """
    Validate the database contents.

    Checks (only for columns in required_columns):
    - 'index' column: all values must be integers
    - 'entry' column: all values must be non-empty strings
    - 'gloss' column: all values must be non-empty strings

    Args:
        df: DataFrame to validate
        required_columns: Which columns to enforce (default: index, entry, gloss)

    Returns:
        ValidationResult with valid=True/False and dict of errors by column.
    """
    required_columns = required_columns or REQUIRED_COLUMNS
    errors = {}

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
    
    # Validate 'entry' column - must be non-empty strings
    if "entry" in required_columns and "entry" in df.columns:
        invalid_entries = []
        for i, val in enumerate(df["entry"]):
            if pd.isna(val):
                invalid_entries.append(f"Row {i+1}: empty")
            elif not isinstance(val, str):
                invalid_entries.append(f"Row {i+1}: '{val}' (type: {type(val).__name__})")
            elif val.strip() == "":
                invalid_entries.append(f"Row {i+1}: empty string")
        
        if invalid_entries:
            errors["entry"] = invalid_entries
    
    # Validate 'gloss' column - must be non-empty strings
    if "gloss" in required_columns and "gloss" in df.columns:
        invalid_glosses = []
        for i, val in enumerate(df["gloss"]):
            if pd.isna(val):
                invalid_glosses.append(f"Row {i+1}: empty")
            elif not isinstance(val, str):
                invalid_glosses.append(f"Row {i+1}: '{val}' (type: {type(val).__name__})")
            elif val.strip() == "":
                invalid_glosses.append(f"Row {i+1}: empty string")
        
        if invalid_glosses:
            errors["gloss"] = invalid_glosses
    
    return ValidationResult(
        valid=len(errors) == 0,
        errors=errors
    )
