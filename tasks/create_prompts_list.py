"""
Create Prompts List Task
========================

Generates a prompt-list file for the **Prompts** Android app (an offline,
one-prompt-at-a-time audio elicitation app - the phone-based counterpart to
SpeechRecorder).

Prompts reads a .csv (or .xlsx) whose header row is matched by name,
case-insensitive, in any order:
- ``index``   - one of index/id/no/number (optional in the app; we always write it)
- ``gloss_v`` - the vernacular/primary text shown large on the recording screen (required)
- ``gloss_e`` - an English gloss shown smaller below it (optional)
- ``ipa``     - an IPA transcription shown small, bottom-right, for the surveyor (optional)

The app saves one recording per prompt as ``<index>.wav``, so index values
must be unique.
"""

import csv
import io
from dataclasses import dataclass

import pandas as pd


# Column headers the Prompts app recognizes, in the order we write them.
PROMPTS_COLUMNS = ["index", "gloss_v", "gloss_e", "ipa"]


@dataclass
class PromptsListResult:
    """Result of prompt-list generation."""
    success: bool
    dataframe: pd.DataFrame | None = None
    csv_text: str | None = None
    xlsx_bytes: bytes | None = None
    error: str | None = None


def _clean_cell(value) -> str:
    """Coerce a cell to a single-line string (Prompts' CSV reader can't handle
    embedded newlines)."""
    if pd.isna(value):
        return ""
    text = str(value)
    return " ".join(text.split())


def generate_prompts_list(
    df: pd.DataFrame,
    index_col: str,
    vernacular_col: str,
    english_col: str | None = None,
    ipa_col: str | None = None,
) -> PromptsListResult:
    """
    Build a Prompts-app prompt list from the lexical database.

    Args:
        df: DataFrame with the lexical data
        index_col: Column to use as the prompt index (must be unique)
        vernacular_col: Column shown large to the speaker (-> gloss_v)
        english_col: Optional column shown smaller below it (-> gloss_e)
        ipa_col: Optional column shown bottom-right for the surveyor (-> ipa)

    Returns:
        PromptsListResult with the assembled table plus .csv and .xlsx renderings.
    """
    # Prompts writes <index>.wav per prompt, so duplicate indices would collide.
    if df[index_col].duplicated().any():
        duplicate_values = df[index_col][df[index_col].duplicated()].unique()
        error_msg = (
            "Your index column contains duplicate values. Each item must have a "
            "unique index so the app can save one recording per prompt. Please fix "
            "this in your Excel file, then clear the database and re-upload. "
            f"Duplicate values: {', '.join(map(str, duplicate_values))}"
        )
        return PromptsListResult(success=False, error=error_msg)

    out = pd.DataFrame()
    out["index"] = df[index_col].map(_clean_cell)
    out["gloss_v"] = df[vernacular_col].map(_clean_cell)

    if english_col:
        out["gloss_e"] = df[english_col].map(_clean_cell)
    if ipa_col:
        out["ipa"] = df[ipa_col].map(_clean_cell)

    # Order columns as PROMPTS_COLUMNS, keeping only the ones we populated.
    out = out[[c for c in PROMPTS_COLUMNS if c in out.columns]]

    # Drop rows with no vernacular text - the app skips them anyway.
    out = out[out["gloss_v"] != ""].reset_index(drop=True)

    if out.empty:
        return PromptsListResult(
            success=False,
            error=(
                f"No usable prompts: the '{vernacular_col}' column is empty for "
                "every row."
            ),
        )

    # CSV (UTF-8, minimal quoting - matches the app's simple reader).
    csv_buf = io.StringIO()
    out.to_csv(csv_buf, index=False, quoting=csv.QUOTE_MINIMAL, lineterminator="\n")
    csv_text = csv_buf.getvalue()

    # XLSX (first sheet is all the app reads).
    xlsx_buf = io.BytesIO()
    with pd.ExcelWriter(xlsx_buf, engine="openpyxl") as writer:
        out.to_excel(writer, index=False, sheet_name="prompts")
    xlsx_bytes = xlsx_buf.getvalue()

    return PromptsListResult(
        success=True,
        dataframe=out,
        csv_text=csv_text,
        xlsx_bytes=xlsx_bytes,
    )
