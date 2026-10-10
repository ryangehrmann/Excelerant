# Changelog

All notable changes to Excelerant are logged here. Versioning is now tracked
through git history in this folder — no more copy-pasting a new `v 0.X`
folder per version. Older pre-git snapshots live in `../archive/`.

## v0.5 (current)
- 2026-10-10 — Full-size `ɦ` now behaves like `h`: after an aspirable
  consonant it is read as voiced aspiration and written `ʱ` (`bɦa` -> `bʱ`,
  `dʑɦa` -> `dʑʱ`), and before a sonorant as pre-aspiration (`ɦma` -> `ʱm`).
  The stop+h warning now covers both and reads "stop/affricate + h/ɦ".
- 2026-10-10 — Segment Words warns before segmenting when words contain a
  stop/affricate followed by a plain `h`, which Excelerant reads as one
  aspirated segment (`pha` -> C = `pʰ`). The warning shows up to 20 examples
  from the database with the segmentation each will get, a copyable list of
  all affected row IDs, and "Stop and fix my database" / "Continue anyway"
  buttons. Parsing is unchanged. Detection: `check_stop_h` in
  tasks/segment_words.py; row IDs via the shared `format_row_id`.
- 2026-10-10 — Voiced aspiration in Segment Words: `ʱ` is now an accepted
  aspiration marker alongside `ʰ`, and voiced stops and affricates (b d ɖ ɟ
  g ɢ, dz dʒ dʑ ɖʐ ɟʝ gɣ, ...) can carry aspiration, so `bʰa`, `bʱa`,
  `dʑʱa` and tied `d͡ʑʱa` each have a single aspirated onset. Previously `ʱ`
  was rejected as non-IPA and `bʰa` was read as presyllable `baʰa`.
- 2026-10-10 — Support tie characters in Segment Words. The over-tie `͡` is
  now an accepted diacritic; under-ties `͜` are converted to it. A tie must
  join two consonants (each may carry combining diacritics, e.g. `t̪͡s̪`),
  otherwise the word is marked as an error. Tied units (`t͡s`, `t͡ɕ`, `k͡p`,
  `g͡b`, `ŋ͡m`) are swapped for placeholder characters before onset parsing,
  so every onset rule treats them as one consonant (aspiration, medials,
  nasal prefixes, presyllables, codas), and the tie is kept in the output.
  Untied sequences such as `kp` keep their presyllable reading. Removed the
  old, unreachable tie branches in the onset rules, which dropped the tie.
- 2026-10-10 — Convert precomposed characters to the form Excelerant's IPA
  inventory accepts, in the Explode Entries and Segment Words cleaning steps.
  `convert_precomposed` (tasks/segment_words.py) derives its maps from
  Unicode's canonical decompositions: 36 precomposed characters that break
  down entirely into inventory characters are decomposed (nasal ã ẽ ĩ õ ũ ỹ,
  creaky ḛ ḭ ṵ, breathy ṳ, voiceless ḁ, dot-below consonants, etc.), and
  c + combining cedilla is composed to ç. Characters whose diacritics aren't
  in the inventory (ä, ā) are still reported as non-IPA. Conversions are
  listed in the cleaning report; originals stay in `entry_orig` / `word_orig`.
- 2026-10-10 — Converter additions: `ñ` and n + combining tilde map to the
  palatal nasal `ɲ`; IPA script `ɡ` (U+0261) maps to `g`, the form the
  inventory uses (`LOOKALIKE_CONVERSIONS`). Check Database Formatting & Update
  Entries now runs the converter on `entry`, `word` and segment columns too,
  before comparing entries, so a storage-form change alone doesn't trigger an
  archive column; conversions are listed on its results screen.
- 2026-10-10 — Segment Words treats a long vowel with an offglide (vowel +
  ː + vowel, e.g. `iːə`, `uːə`, `aːi`) as one V unit. Previously `kiːə` was
  misparsed as presyllable `k`+`i`, onset `ː`, vowel `ə`.
- 2026-10-10 — Colons in transcriptions now stop Explode Entries, Segment
  Words and Check Database Formatting & Update Entries with an error listing
  each affected column and its row IDs (index for `entry`, index.sub_index
  for words and segments) in copyable boxes, plus a Find & Replace tip.
  Previously the cleaning step silently deleted colons as punctuation, so
  `ka:` became `ka`. Fullwidth colon, ratio sign and modifier letter colon
  are caught too; `ː` and `ˑ` are untouched. Shared check in
  `tasks/colon_check.py`.
- 2026-10-10 — Add a Manage Database landing page (`screen_manage_database_hub`),
  styled like the Collect Data landing page. It explains the
  revise-segments-then-update-entries cycle and the setup tasks before the
  upload screen.
- 2026-10-10 — Check Database Formatting & Update Entries now archives the
  previous entries as `entry_before_YYYY-MM-DD` (with `_2`, `_3`, ... for
  repeat runs the same day) instead of renaming `entry` to `entry_orig`,
  which left duplicate `entry_orig` columns on a second run. A column is
  only added when at least one entry changes. Exports place archive columns
  just before `entry`, oldest first. Existing `entry_orig` columns are left
  as they are.
- 2026-10-10 — Replace the deprecated `use_container_width` with
  `width="stretch"` / `width="content"` across all 130 UI calls (Streamlit
  scheduled its removal), and raise the Streamlit minimum to 1.49.0, the
  first tested version with `width` on buttons, images and dataframes.
- 2026-10-10 — Reorganize the task registry to match the app's sections.
  Categories renamed: "Collect Lexical Data" -> "Collect Data", "Orthography
  Development" -> "Participatory Card Sorting", "Phonological Analysis" ->
  "Analyze Phonology", "Acoustic Phonetic Analysis" -> "Analyze Phonetics".
  The card-sorting task menu is now its own mode (`card_sorting`,
  `Screen.MAIN_MENU_CARD_SORTING`) since both the Phonology and Orthography
  hubs lead to it.
- 2026-10-10 — Rename the Orthography hub's "Orthography Development" button
  to "Participatory Card Sorting". Enable "Analyze Phonology" on the welcome
  screen: it opens a new Phonology hub (`screen_phonology_hub`) with its own
  "Participatory Card Sorting" button. Both buttons share one entry point
  (`_start_participatory_card_sorting`) and lead to the same upload screen
  and card-sorting task menu.
- 2026-10-10 — Allow blank `entry` and `gloss` cells. Upload now warns
  instead of erroring and lists the affected index values in a copyable box.
  Untranscribed rows are carried through Explode Entries (blank `word`,
  `sub_index` 1), Segment Words (blank P–T) and Update Entries from Words.
  The SpeechRecorder script and the Prompts list skip rows with a blank
  primary gloss / prompt text and list them. `index` is still required.
- 2026-10-10 — Upload no longer treats cells containing `null`, `nan`, `NA`,
  `None`, etc. as empty (pandas' default NA strings); only truly empty cells
  count as missing.
- 2026-08-30 — Sort standard word list tools by `index` before use: the BEWL
  `wordlist.xlsx` had a few rows out of sequence, so both the downloadable
  spreadsheet and the generated SpeechRecorder / Prompts scripts came out
  unordered. The bundled file is now sorted, and `load_word_list` re-sorts
  by index as a safety net for every tool.
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
