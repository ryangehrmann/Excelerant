# Changelog

All notable changes to Excelerant are logged here. Versioning is now tracked
through git history in this folder — no more copy-pasting a new `v 0.X`
folder per version. Older pre-git snapshots live in `../archive/`.

## v0.5 (current)
- 2026-08-30 — Fix "Copy XML Script to Clipboard": it wrote raw UTF-8 bytes
  (mojibake for non-ASCII scripts like Lao). Now decodes the bytes back
  through UTF-8 in the browser (`TextDecoder` on `atob` output).
- 2026-08-30 — Drop decorative emoji from the Collect Data section headings
  and link labels (minimalist/professional direction going forward).
- 2026-08-30 — Reorder the Collect Data flow: a landing screen forks between
  a standard word list tool and a custom upload; the SpeechRecorder-vs-Prompts
  platform choice now comes *after* choosing a tool / uploading a database
  (new `screen_collect_platform`). The standard word list catalog is its own
  fork off the landing screen (removed from the upload screen); the tool page
  is tailored to the chosen platform.
- 2026-08-30 — Bundle the Big Excelerant Word List (BEWL) v1.0 as a standard
  word list tool (`standard_word_lists/bewl_v01/`: 1,886 items, English + Lao
  glosses, adapted from the EFEO-CNRS-SOAS list, with its full documentation).
- 2026-08-30 — Standard word list tool page streamlined to three actions:
  download the word list spreadsheet, download its documentation (a tool's
  `documentation.md` is served as a self-contained `.html` page so users
  don't need a Markdown viewer), or generate the platform's import file
  (SpeechRecorder XML with copy/paste instructions, or a Prompts `.csv`/
  `.xlsx`). A tool folder may set `download_filename`. Adds `markdown` dep.
- 2026-08-29 — Add "Standard Word List Tools" to the SpeechRecorder path of
  Collect Lexical Data: bundled word lists under `standard_word_lists/` (one
  folder per tool: `tool.toml` with `[[gloss_languages]]` + `wordlist.csv`/
  `.xlsx` with `index`, one column per gloss language, optional `extra`),
  browsable from the upload screen. Each tool's info page lets the user pick
  the primary gloss language and an optional secondary one, a token count,
  and an optional user-typed sentence frame (`___` marks where the primary
  gloss goes), then one-click XML download. Runs through the same generator
  as Create Data Collection Script; the copy / download / instructions block
  is now a shared `render_script_output` helper (and the custom screen gains
  a Download XML button).
- 2026-08-29 — Move audio-linking and transcription-prep tasks (Add Audio
  File Links, Explode Entries, Segment Words, Check Database Formatting) out
  of Analyze Phonology into "Manage Lexical Data", now an active section.
  Analyze Phonology is grayed until real phonological-analysis tools land.
  The four per-mode task menus are now one shared `_render_mode_menu` helper.
- 2026-08-29 — Restructure the welcome menu into five sections: "Collect
  Lexical Data" and (grayed, staged) "Manage Lexical Data" on the left, then
  "Analyze Phonology", "Develop Orthography", and (grayed) "Analyze Phonetics"
  (renamed from Phonology / Orthography / Acoustic Phonetics)
- 2026-08-29 — Add "Collect Lexical Data" section: a fork between building a
  script for SpeechRecorder (PC/Mac, existing task, moved here out of the
  Phonology menu) and the Prompts Android app. New "Create Prompts List"
  task exports an index/gloss_v/gloss_e/ipa CSV or XLSX the Prompts app imports
- 2026-08-29 — Prompts app published at github.com/ryangehrmann/Prompts
  (public repo, signed v1.0 APK on GitHub Releases); the Create Prompts List
  screen and the Collect Lexical Data fork now link straight to the APK
- 2026-08-29 — Collect Lexical Data uploads only require `index` + `gloss`
  (no `entry`/transcription column, which doesn't exist yet at collection time);
  other modes still require the full `index`/`entry`/`gloss` database
- 2026-08-07 — Add Sort Cards task (stage 1): digital, in-app card sorting
  as an alternative to printing, with a card display styled to match the
  physical cards, piles with quick-reference previews and whole-pile
  removal, and quick-add by UID. Never writes to the database directly --
  results always go through Process Cards, same as every other input path.
- 2026-08-07 — Rename Print Cards to Generate Cards; its export step now
  produces a Sort Cards "prepared activity" JSON alongside the printable
  HTML deck, from the same filter/card-content configuration
- 2026-08-07 — Add Process Cards task: record card-sorting results into the
  database by typing UIDs manually or via an AI-assisted photo-reading
  workflow (paste a vision AI's reading of category-labeled workshop photos)
- 2026-08-06 — Add Orthography Development branch with Export Sorting Activity task

## v0.4
- 2026-02-17 — Split app into Phonological/Acoustic paths with redesigned UI
- 2026-02-16 — Add tone syllable break detection and word column formulae in Excel export
- 2026-02-14 — Add explode entries, segment words, and check database formatting tasks
- 2026-01-28 — Remove all emojis for cleaner, professional presentation
- 2026-01-28 — Update favicon: change arrow color from light green to white
- 2026-01-28 — Update banner: change arrow color from light green to white
- 2026-01-28 — Add requirements.txt for Replit deployment
- 2026-01-28 — Initial commit: Excelerant lexical database processing app

## Pre-git prototypes (see `archive/`)
These predate git and have no commit-level history — noted here for continuity.

- **v0.3** — Streamlit layout/UI template experiments, staged before the app
  became git-tracked as v0.4.
- **v0.2** — Early Streamlit rewrite (`app.py`, `func.py`) with audio
  reconciliation test data.
- **v0.1** — Initial prototype built around the MAUS forced-alignment workflow
  (`app.py`, `func.py`, `ide.py`).
