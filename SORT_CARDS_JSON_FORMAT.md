# Sort Cards JSON Format

> **Status:** The "Sort Cards" task (digital, in-app card sorting) is planned
> but not yet built. Prepared-activity JSONs *can* already be generated,
> though -- Generate Cards (formerly "Print Cards") produces one alongside
> its printable HTML deck. This document defines the format so those files
> can be understood, hand-edited, or hand-authored from scratch if needed.
> Once Sort Cards ships, this same document describes what it produces and
> what its "load a prepared activity" / "resume" options accept.

## Why one format for three situations

The same JSON shape is used whether the file represents:

1. **A prepared activity** you hand off to a participant before they start.
2. **A paused, in-progress sort** (yours or theirs) to resume later.
3. **A completed result** ready to import into Process Cards.

The difference between the three is just how full the fields are, not the
structure. This means a participant's completed export is trivially valid
input to Process Cards, and a prepared activity you write by hand today
will work the same way once Sort Cards can load one.

## No filtered spreadsheet copies needed

A prepared activity almost always targets a *subset* of the database --
e.g. "only back vowels, only before a velar nasal coda" -- so a sorting
task is a manageable size and isn't diluted by irrelevant categories. That
subset is described with `filters` *inside the JSON*, not by handing the
participant a cut-down `.xlsx`. The participant always uploads your one
master spreadsheet; Sort Cards narrows it down using the same
column-by-column filtering Generate Cards' "Filter Database" step already
does (`filter_dataframe()` in `tasks/generate_cards.py`). This means:

- No filtered file copies to create, keep track of, or accidentally use a
  stale version of.
- Editing the master database later doesn't invalidate old activity
  files -- the filter is re-applied fresh each time.
- You don't have to hand-type `filters` into JSON at all: build the
  filter interactively in Generate Cards' Step 1 (multiselect columns and
  values, watch the row count update live), pick your card content in
  Step 2, then Step 3 exports both the printable HTML deck *and* this
  JSON from that same configuration in one click. Hand-typing is only
  needed for the cases Generate Cards doesn't have a UI for yet --
  prescribed categories, or editing a file after the fact -- see below.

## Fields

| Field | Type | Meaning |
|---|---|---|
| `format` | string | Always `"excelerant_sort_cards"`. Lets an importer reject an unrelated JSON file with a clear error instead of a confusing crash. |
| `format_version` | integer | Currently `1`. Bump only if the shape of this file changes incompatibly. |
| `activity_name` | string | Same meaning as Process Cards' "Sorting Activity Name" — the raw, human-typed name. Sanitized (spaces → underscores) at processing time, not in this file. |
| `index_col` | string | Name of the spreadsheet column holding each row's index, e.g. `"index"`. Must match the column used when the cards were printed or displayed, so UIDs line up. |
| `sub_index_col` | string \| `null` | Name of the sub-index column, e.g. `"sub_index"`, or `null` if the activity doesn't use one. |
| `filters` | object | **Optional.** Maps a column name to the list of values from that column to include — identical semantics to Generate Cards' filter step. Omit, or use `{}`, to sort the whole database. Use the literal string `"(blank)"` as a value to include rows where that column is empty. Generate Cards only includes columns that actually narrow the row set, so a fresh export's `filters` is already minimal. |
| `line_columns` | array of strings | 1–3 column names, in display order, shown on each digital card — same concept as Generate Cards' "Card lines". |
| `categories` | array of `{label, uids}` | **Optional, usually empty (`[]`).** An empty array is the normal case: the participant creates their own piles as they sort, naming them freely, same as clicking "Add Pile" in the original desktop tool. A *non-empty* array with every `uids: []` instead prescribes fixed category names the participant can only assign cards to — use this only when you specifically need consistent category names across multiple participants sorting the same activity. Once sorting starts, `uids` fills in per category regardless of which mode was used. |
| `remaining_uids` | array of strings \| `null` | UIDs not yet sorted, in deck order (after `filters` is applied), for resuming a paused session. `null` (or omit) if this wasn't tracked, or once a sort is finished. |
| `created` | string | ISO 8601 timestamp of when the file was first created. |
| `updated` | string \| `null` | ISO 8601 timestamp of the last change, or `null` for a freshly prepared activity that hasn't been touched yet. |

## The three states in practice

**1. Prepared activity** (you → participant, before sorting starts)

- `filters` and `line_columns` set to define the task.
- `categories`: `[]` in the normal, open-ended case (participant names
  their own piles) — or pre-populated with `uids: []` only if you need to
  prescribe exact category names.
- `remaining_uids`: `null` (there's no "in progress deck" yet).
- `updated`: `null`.

**2. Paused / in-progress** (either of you, mid-sort)

- `categories` partially filled, possibly including piles the participant
  created themselves that weren't in the original file.
- `remaining_uids` populated with whatever's left in the (filtered) deck.
- `updated` set to the last save time.

**3. Completed result** (participant → you, ready to import into Process Cards)

- `categories` filled in.
- `remaining_uids`: `null` or `[]`.
- Process Cards only reads `activity_name`, `index_col`, `sub_index_col`,
  and `categories` — it ignores `filters`, `line_columns`, and
  `remaining_uids` entirely, so a *partial* sort is still a perfectly
  valid file to import. Whatever wasn't sorted is left blank in the
  database, same as it would be with manual entry.

## Preparing an activity

**The normal case — open-ended categories, no fixed labels:** use
Generate Cards. Set up your filter (Step 1) and card content (Step 2) as
usual, then Step 3 downloads both the HTML deck and the matching JSON
from the same configuration. Nothing to hand-write.

**Prescribed categories, or hand-editing an existing file:** Generate
Cards doesn't have a UI for pre-populating fixed category names yet, so
for that case, edit the JSON directly in any text editor:

1. Start from a Generate Cards export (recommended, so `filters` and
   `line_columns` are already correct), or copy the template below.
2. Set `activity_name` to whatever you want the resulting database column
   to be called.
3. Set `index_col` (and `sub_index_col`, or `null` if unused) to match the
   spreadsheet you're sending the participant.
4. Set `filters` to narrow the task down to the rows you actually want
   sorted, and `line_columns` to the 1–3 columns that should appear on
   each card.
5. Add one entry per prescribed category to `categories`, each with
   `"uids": []` — the `label` is exactly what gets written into the
   database later, so spell it exactly as you want it to appear.
6. Save as `<activity_name>.json`, UTF-8 encoded (important if a label
   uses IPA or other non-Latin characters).
7. Send this file alongside the spreadsheet the participant should
   upload — both are needed; the JSON alone has no card content.

### Example: filtered subset, open-ended categories (the normal case)

A task built around your "back vowels before a velar nasal coda" example
— the participant sees only the matching rows, and invents their own
category names as they sort by vowel quality:

```json
{
  "format": "excelerant_sort_cards",
  "format_version": 1,
  "activity_name": "back vowels before velar nasal coda",
  "index_col": "index",
  "sub_index_col": "sub_index",
  "filters": {
    "vowel": ["a", "ɔ", "o", "u", "ɯ"],
    "coda": ["ŋ"]
  },
  "line_columns": ["entry", "gloss", "word"],
  "categories": [],
  "remaining_uids": null,
  "created": "2026-08-10T14:22:00",
  "updated": null
}
```

### Example: prescribed categories (the exception)

Use this shape only when category names must be fixed in advance, e.g.
comparing results across several participants sorting the same set:

```json
{
  "format": "excelerant_sort_cards",
  "format_version": 1,
  "activity_name": "front p",
  "index_col": "index",
  "sub_index_col": "sub_index",
  "filters": {},
  "line_columns": ["entry", "gloss"],
  "categories": [
    {"label": "i", "uids": []},
    {"label": "e", "uids": []},
    {"label": "ɛ", "uids": []}
  ],
  "remaining_uids": null,
  "created": "2026-08-10T14:22:00",
  "updated": null
}
```

### Example: completed result (what comes back)

```json
{
  "format": "excelerant_sort_cards",
  "format_version": 1,
  "activity_name": "back vowels before velar nasal coda",
  "index_col": "index",
  "sub_index_col": "sub_index",
  "filters": {
    "vowel": ["a", "ɔ", "o", "u", "ɯ"],
    "coda": ["ŋ"]
  },
  "line_columns": ["entry", "gloss", "word"],
  "categories": [
    {"label": "high back", "uids": ["4", "9", "22.1"]},
    {"label": "mid back", "uids": ["3", "7"]},
    {"label": "low back", "uids": ["15.2"]}
  ],
  "remaining_uids": [],
  "created": "2026-08-10T14:22:00",
  "updated": "2026-08-10T15:04:00"
}
```

Note the category names here (`"high back"`, etc.) didn't exist in the
prepared activity at all -- the participant invented them while sorting,
exactly as intended for an open-ended task.

## Gotchas

- **UID format must match exactly** what the spreadsheet's `index_col` /
  `sub_index_col` would produce for that row (same as Generate Cards /
  Process Cards elsewhere in Excelerant) -- plain `"12"` if no sub-index,
  `"12.3"` if there is one.
- **`filters` values must match cell contents exactly**, including
  capitalization and diacritics -- there's no fuzzy matching, same as
  Generate Cards' filter step. A typo just silently excludes every
  matching row rather than erroring, so double-check against the source
  data (this only applies if you're hand-editing -- an unmodified
  Generate Cards export can't have this problem).
- **Category labels are written verbatim** as database cell values. Unlike
  `activity_name` (which becomes a column header and gets spaces replaced
  with underscores), nothing about a category `label` is sanitized.
- **UTF-8 only.** Non-Latin labels (IPA symbols, Lao script, etc.) will
  break if the file is saved in any other encoding.
- A JSON missing `format` / `format_version`, or with a `format_version`
  the app doesn't recognize, should be rejected with a clear error rather
  than partially processed -- this is a forward-compatibility seam, not
  just validation.
