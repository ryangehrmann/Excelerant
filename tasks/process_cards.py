"""
Process Cards Task
===================

Writes the results of a card-sorting activity back into the database. The
UID on each card (as built by Print Cards -- "{index}" or
"{index}.{sub_index}") is looked up against the same index/sub-index
columns, and the category label the card was sorted into is written into a
new column, one column per sorting activity.

Two input methods feed the same category-label / UID-list structure into
process_cards_manual():

- Manual: the user names each category and types/pastes in the UIDs by hand.
- AI-assisted: the user photographs each sorted pile, names the photos by
  category, and has an external AI chat tool (Claude, ChatGPT, etc.) read
  the UID printed on each card. derive_category_from_filename() and
  parse_ai_assisted_output() turn that AI reply into the same
  (label, uid_text) pairs the manual method produces, so validation and
  processing are identical from that point on.
"""

import re
import pandas as pd
from dataclasses import dataclass, field


def sanitize_activity_column_name(name: str) -> str:
    """Turn a user-typed activity name into a database column header:
    trim whitespace and replace internal runs of whitespace with underscores."""
    return re.sub(r"\s+", "_", name.strip())


def parse_uid_list(text: str) -> list[str]:
    """Split freeform UID text (newlines, commas, and/or spaces) into a
    list of UID strings, deduplicated and with blanks dropped."""
    if not text:
        return []
    pieces = re.split(r"[,\s]+", text.strip())
    seen = dict.fromkeys(p for p in pieces if p)
    return list(seen)


# =============================================================================
# AI-Assisted Input
# =============================================================================

# The photo is expected to end in a common image extension.
_IMAGE_EXT_RE = re.compile(r"\.(jpe?g|png|heic|heif|webp|gif|bmp|tiff?)$", re.IGNORECASE)

# A trailing "photo number" suffix on a filename, e.g. "_2", "-3", " (4)".
_TRAILING_PHOTO_NUM_RE = re.compile(r"[\s_-]*\(?\d+\)?$")

AI_ASSISTED_PROMPT = """I'm going to share several photos of physical cards from a card-sorting activity. Each card has a small identifier code (a plain number, or number.number, like "12" or "12.3") printed in its bottom-right corner.

For each photo, read every card's identifier code and list them, one photo per line, in this exact format:

<exact original filename>: <code>, <code>, <code>, ...

Rules:
- Use the exact filename I gave the image, including its extension.
- List every card visible in that photo, separated by commas.
- If a code is unreadable, blurry, or ambiguous, write ??? in its place instead of guessing -- don't guess.
- Reply with only these lines, one per photo, in this format -- no extra commentary."""


def derive_category_from_filename(filename: str) -> str:
    """Derive a category label from a photographed-pile filename.

    Strips a trailing image extension, then a trailing "photo number"
    suffix, so "i.jpg", "i_2.jpg", "i-3.jpg", and "i (4).jpg" all derive
    the category "i" -- letting multiple photos of the same (large) pile
    share one category. Falls back to the extension-stripped stem if
    removing the numeric suffix would leave nothing.
    """
    stem = _IMAGE_EXT_RE.sub("", filename.strip()).strip()
    stripped = _TRAILING_PHOTO_NUM_RE.sub("", stem).strip()
    return stripped if stripped else stem


@dataclass
class AIOutputParseResult:
    success: bool
    categories: list[tuple[str, str]] = field(default_factory=list)
    error: str | None = None
    unparsed_lines: list[str] = field(default_factory=list)


def parse_ai_assisted_output(text: str) -> AIOutputParseResult:
    """Parse a pasted AI reply ("filename: code, code, ..." per line) into
    (category_label, uid_text) pairs, merging UIDs from multiple photos of
    the same category together.

    Lines that don't match the expected "filename: codes" shape are
    collected in unparsed_lines rather than failing the whole parse, so a
    stray line of AI commentary doesn't discard everything else.
    """
    lines = [ln.strip() for ln in text.strip().splitlines() if ln.strip()]
    if not lines:
        return AIOutputParseResult(success=False, error="Paste the AI's reply before parsing.")

    grouped: dict[str, list[str]] = {}
    unparsed = []
    for line in lines:
        match = re.match(r"^(.+?):\s*(.+)$", line)
        if not match:
            unparsed.append(line)
            continue

        filename, uid_part = match.group(1).strip(), match.group(2).strip()
        category = derive_category_from_filename(filename)
        existing = grouped.setdefault(category, [])
        for uid in parse_uid_list(uid_part):
            if uid not in existing:
                existing.append(uid)

    if not grouped:
        return AIOutputParseResult(
            success=False,
            error="Couldn't find any lines in the expected 'filename: codes' format.",
            unparsed_lines=unparsed,
        )

    categories = [(label, ", ".join(uids)) for label, uids in grouped.items()]
    return AIOutputParseResult(success=True, categories=categories, unparsed_lines=unparsed)


@dataclass
class ProcessCardsResult:
    success: bool
    df: pd.DataFrame | None = None
    error: str | None = None
    duplicate_uids: list[str] = field(default_factory=list)
    unmatched_uids: list[str] = field(default_factory=list)
    column_name: str | None = None
    summary: dict = field(default_factory=dict)


def _build_uid_lookup(
    df: pd.DataFrame, index_col: str, sub_index_col: str | None
) -> tuple[dict[str, object], list[str]]:
    """Map each row's card UID ("index" or "index.sub_index") to its row
    label. Returns (lookup, duplicate_uids) -- duplicates mean the database
    itself has non-unique index (+ sub-index) values, so UIDs can't be
    matched reliably."""
    if sub_index_col:
        uids = df[index_col].astype(str) + "." + df[sub_index_col].astype(str)
    else:
        uids = df[index_col].astype(str)

    lookup: dict[str, object] = {}
    duplicates: set[str] = set()
    for row_label, uid in uids.items():
        if uid in lookup:
            duplicates.add(uid)
        else:
            lookup[uid] = row_label
    return lookup, sorted(duplicates)


def process_cards_manual(
    df: pd.DataFrame,
    index_col: str,
    sub_index_col: str | None,
    activity_name: str,
    categories: list[tuple[str, str]],
) -> ProcessCardsResult:
    """Add a new column recording which category each card's row was sorted into.

    Args:
        df: The current database.
        index_col: Column holding the index value used on the printed cards.
        sub_index_col: Optional column holding the sub-index value, if cards
            were printed with "index.sub_index" UIDs.
        activity_name: Raw user-typed name for the sorting activity; becomes
            the new column header after sanitizing.
        categories: List of (label, uid_text) pairs, one per category the
            cards were sorted into. label is the value written into the
            database for matching rows; uid_text is the raw textarea content
            of UIDs sorted into that category. Categories with a blank label
            or blank UID text are ignored.
    """
    column_name = sanitize_activity_column_name(activity_name)
    if not column_name:
        return ProcessCardsResult(success=False, error="Enter a name for the sorting activity.")

    if column_name in df.columns:
        return ProcessCardsResult(
            success=False,
            error=f"Column '{column_name}' already exists in the database. "
                  "Choose a different activity name, or rename/remove the existing column first.",
            column_name=column_name,
        )

    active_categories = [
        (label.strip(), text) for label, text in categories if label.strip() and text.strip()
    ]
    if not active_categories:
        return ProcessCardsResult(
            success=False,
            error="Add at least one category with a label and a list of UIDs.",
            column_name=column_name,
        )

    lookup, index_duplicates = _build_uid_lookup(df, index_col, sub_index_col)
    if index_duplicates:
        return ProcessCardsResult(
            success=False,
            error="Duplicate index values found in the database -- UIDs can't be matched reliably "
                  "until these are resolved."
                  + ("" if sub_index_col else " Consider selecting a sub-index column."),
            duplicate_uids=index_duplicates,
            column_name=column_name,
        )

    # Parse UIDs per category, then find UIDs listed under more than one
    # category (a conflict) and UIDs that don't match any row (a typo).
    uid_to_categories: dict[str, list[str]] = {}
    parsed_categories: list[tuple[str, list[str]]] = []
    for label, text in active_categories:
        uids = parse_uid_list(text)
        parsed_categories.append((label, uids))
        for uid in uids:
            uid_to_categories.setdefault(uid, []).append(label)

    # Include the offending category label(s) alongside each bad UID, so the
    # user can find the input error rather than just knowing it exists.
    duplicate_uids = [
        f"{uid} (categories: {', '.join(labels)})"
        for uid, labels in sorted(uid_to_categories.items())
        if len(labels) > 1
    ]
    unmatched_uids = [
        f"{uid} (category: {', '.join(labels)})"
        for uid, labels in sorted(uid_to_categories.items())
        if uid not in lookup
    ]

    if duplicate_uids or unmatched_uids:
        error_parts = []
        if duplicate_uids:
            error_parts.append(f"{len(duplicate_uids)} UID(s) listed under more than one category")
        if unmatched_uids:
            error_parts.append(f"{len(unmatched_uids)} UID(s) not found in the database")
        return ProcessCardsResult(
            success=False,
            error="Fix the following before processing: " + "; ".join(error_parts) + ".",
            duplicate_uids=duplicate_uids,
            unmatched_uids=unmatched_uids,
            column_name=column_name,
        )

    result_df = df.copy()
    result_df[column_name] = None
    labeled_count = 0
    for label, uids in parsed_categories:
        for uid in uids:
            result_df.loc[lookup[uid], column_name] = label
            labeled_count += 1

    return ProcessCardsResult(
        success=True,
        df=result_df,
        column_name=column_name,
        summary={
            "categories": len(parsed_categories),
            "rows_labeled": labeled_count,
            "rows_blank": len(result_df) - labeled_count,
            "total_rows": len(result_df),
        },
    )
