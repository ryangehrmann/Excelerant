"""
Colon Check
===========

Finds colons in transcription columns (entry, word, segment columns).

A colon is often typed in place of the IPA length mark (ː, U+02D0), but not
always, so Excelerant never converts colons itself. Steps that clean or
segment transcriptions run this check first and stop with a list of where the
colons are, so the user can review them and fix them in Excel.
"""

import pandas as pd


# ASCII colon plus lookalikes that get typed by accident. The IPA length mark
# (ː) and half-long mark (ˑ) are not included - those are correct.
COLON_CHARACTERS = {
    ":": "colon",
    "：": "fullwidth colon",
    "∶": "ratio sign",
    "꞉": "modifier letter colon",
}

# Columns that hold one word's segments
SEGMENT_COLUMNS = ["P", "R", "C", "M", "V", "F", "T"]

COLON_RECOMMENDATION = (
    "Colons are ambiguous to Excelerant; they could indicate punctuation or "
    "segment length. Please change all colons that represent length to the "
    "IPA length mark (ː) and replace any remaining colons with another symbol. "
    "If you have many to change, Excel's Find & Replace (Ctrl+H, or "
    "Cmd+Shift+H on a Mac) can replace every : with ː in one go. Then clear "
    "the database and re-upload."
)


def _format_index(value) -> str:
    """Render an index cell as text, dropping the '.0' pandas adds to whole numbers."""
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def format_row_id(df: pd.DataFrame, row_label, include_sub_index: bool = True) -> str:
    """A row's ID as shown to users: its index, plus '.sub_index' when the
    database has a sub_index column (the same UIDs printed on cards).
    Falls back to the spreadsheet row number if there's no index column."""
    if "index" not in df.columns:
        return str(row_label + 2)
    row_id = _format_index(df.at[row_label, "index"])
    if include_sub_index and "sub_index" in df.columns and pd.notna(df.at[row_label, "sub_index"]):
        row_id += f".{_format_index(df.at[row_label, 'sub_index'])}"
    return row_id


def find_colons(df: pd.DataFrame, columns: list[str]) -> dict[str, list[str]]:
    """
    Find cells containing a colon (or colon lookalike) in the given columns.

    Rows are identified by index for 'entry' (an entry belongs to the whole
    index), and by index.sub_index for word and segment columns when a
    sub_index column exists - the same UIDs printed on cards.

    Args:
        df: DataFrame to check
        columns: Columns to check; any not in df are skipped

    Returns:
        Dict of column name -> row IDs (in row order, no repeats) whose cell
        contains a colon. Empty if no colons were found.
    """
    colon_chars = "".join(COLON_CHARACTERS)
    locations = {}

    for col in columns:
        if col not in df.columns:
            continue

        has_colon = df[col].astype(str).str.contains(f"[{colon_chars}]", regex=True, na=False)
        has_colon &= df[col].notna()
        if not has_colon.any():
            continue

        row_ids = []
        for row_label in df.index[has_colon]:
            row_id = format_row_id(df, row_label, include_sub_index=(col != "entry"))
            if row_id not in row_ids:
                row_ids.append(row_id)
        locations[col] = row_ids

    return locations


def colon_error_message(locations: dict[str, list[str]]) -> str:
    """One-line summary of a find_colons result, for error messages."""
    columns = ", ".join(f"'{col}'" for col in locations)
    plural = "s" if len(locations) > 1 else ""
    return f"Found colons in the {columns} column{plural}. Please review them before continuing."
