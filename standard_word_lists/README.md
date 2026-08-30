# Standard word list tools

Each folder here is one **tool** shown in Excelerant under
*Collect Data → Use a standard word list*. The user picks a tool, then a
recording platform (SpeechRecorder / Prompts); the tool page (tailored to
that platform) offers three actions - download the word list spreadsheet,
download its documentation, or generate the import file for the chosen
platform (a SpeechRecorder XML script, or a Prompts list as `.csv` +
`.xlsx`).

## Folder layout

```
standard_word_lists/
    <tool_id>/
        tool.toml          # metadata + gloss-language list (required)
        wordlist.xlsx      # the word list itself (required; wordlist.csv also accepted)
        documentation.md   # optional - bundled in the package and offered as a download
```

- `<tool_id>` — lowercase, digits and underscores only (it shows up in
  filenames and element ids). e.g. `bewl_v01`, `swadesh_207`.
- Add a folder, restart the app, and it appears in the catalog. No code
  changes.
- `documentation.md` is authored in Markdown but served to users as a
  self-contained **`.html`** page (rendered by `documentation_html()`), so
  they don't need a Markdown viewer.

## `tool.toml`

```toml
name = "Swadesh 207 Word List"
summary = "The classic 207-item basic-vocabulary list for lexicostatistics and first-contact elicitation."
recommended_tokens = 1
order = 20
download_filename = "Swadesh_207.xlsx"   # optional; defaults to <tool_id>.<ext>

# One block per selectable gloss language. `column` names a column in the
# wordlist; `label` is what the user sees in the dropdown. The first block
# is the default primary gloss.
[[gloss_languages]]
label = "English"
column = "gloss_en"

[[gloss_languages]]
label = "Lao"
column = "gloss_lao"

description = """
Markdown. Shown on the tool's info page. Use as many paragraphs as you like.

Cover: what it's for, how to use it, what's included, and — importantly —
**source / citation** and **licence / attribution** for the word list.
"""
```

| key | required | notes |
|-----|----------|-------|
| `name` | yes | Display name (catalog button + info-page title). |
| `summary` | recommended | One line, shown under the name in the catalog. |
| `description` | recommended | Markdown, shown on the info page. Put the citation and licence here. |
| `gloss_languages` | **yes** | One or more `[[gloss_languages]]` blocks, each with `label` and `column`. |
| `recommended_tokens` | no | Default for the "number of tokens" box (1–9). Defaults to `1`. |
| `order` | no | Sort position in the catalog (ascending). Defaults to `100`; ties break by name. |
| `download_filename` | no | Name for the downloaded word list file. Defaults to `<tool_id>.<ext>`. |

On the tool's page the user picks which gloss language to use for the
**primary** gloss and, optionally, a different one for the **secondary**
gloss (shown on the item-number line). With only one `gloss_languages` block
there's no dropdown — that language is used and there's no secondary.

## `wordlist.csv` (or `wordlist.xlsx`)

A header row, then one row per prompt. Column names are case-insensitive.
For `.xlsx`, only the first sheet is read.

| column | required | purpose |
|--------|----------|---------|
| `index` | **yes** | Unique whole number per item. Becomes the recording's item code. |
| `gloss_*` | **yes** | One column per language named in `gloss_languages` (e.g. `gloss_en`, `gloss_lao`). |
| `extra` | no | Any extra line to show in every prompt. |

Every column named in `gloss_languages` must exist. Blank `extra` cells are
fine. Any other columns are ignored.

### Example

```csv
index,gloss_en,gloss_lao
1,hand,ມື
2,water,ນ້ຳ
3,to eat,ກິນ
```

### Sentence frames

Frames are **not** part of the file. On the tool's page the user can type an
optional carrier sentence with `___` where the word goes (e.g.
`I will say ___ now`); each prompt then shows the frame with that item's
**primary** gloss filled in.

## Outputs

The tool page has three buttons:

- **Word list spreadsheet** — the `wordlist` file, verbatim (renamed per
  `download_filename`).
- **Word list documentation** — `documentation.md` from the folder (if
  present), converted to a self-contained HTML page.
- **Generate SpeechRecorder script** *or* **Generate Prompts list**, depending
  on the platform chosen upstream:
  - SpeechRecorder XML via `generate_script`: `index`→index, the chosen
    primary/secondary gloss columns→primary/secondary gloss, `extra`→extra,
    with the chosen token count and optional sentence frame. Shown with import
    instructions and a copy-to-clipboard button.
  - Prompts list (`.csv` + `.xlsx`) via `generate_prompts_list`: primary
    gloss→`gloss_v`, secondary gloss→`gloss_e`.
