# Changelog

All notable changes to Excelerant are logged here. Versioning is now tracked
through git history in this folder — no more copy-pasting a new `v 0.X`
folder per version. Older pre-git snapshots live in `../archive/`.

## v0.5 (current)
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
