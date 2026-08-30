"""
Standard Word List Tools
========================

Bundled, pre-prepared word lists that produce a SpeechRecorder data-collection
script without the user uploading their own spreadsheet. An alternative entry
point into the same XML generator used by "Create Data Collection Script".

Each tool is a folder under ``standard_word_lists/`` at the project root:

    standard_word_lists/<tool_id>/
        tool.toml           # metadata + gloss-language list
        wordlist.csv        # or wordlist.xlsx - the word list itself
        documentation.md    # optional - authored in Markdown, served as HTML

A tool declares one or more *gloss languages* (``[[gloss_languages]]`` in
``tool.toml``), each pointing at a column in the wordlist. On the tool's page
the user picks which language to use for the primary gloss and, optionally, a
second language for the secondary gloss, then downloads the word list
spreadsheet, its documentation, or the generated import file (SpeechRecorder
XML / Prompts list) for the chosen recording platform.

A sentence frame is *not* part of a tool - it's an optional carrier phrase
the user types on the tool's page, with ``___`` marking where each item's
primary gloss goes.

See ``standard_word_lists/README.md`` for the full format.
"""

import tomllib
from dataclasses import dataclass, field
from html import escape
from pathlib import Path

import pandas as pd

try:
    import markdown as _markdown
except ImportError:  # pragma: no cover - markdown is a declared dependency
    _markdown = None

from tasks.create_data_collection_script import ScriptResult, generate_script
from tasks.create_prompts_list import PromptsListResult, generate_prompts_list


# Inline stylesheet for the downloadable documentation page - self-contained,
# no internet needed, readable light or dark.
_DOC_CSS = """
body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
       Helvetica, Arial, sans-serif; line-height: 1.6; max-width: 780px;
       margin: 2.5rem auto; padding: 0 1.2rem; color: #1b1b1b; }
h1, h2, h3, h4 { line-height: 1.25; margin-top: 2rem; }
h1 { font-size: 1.9rem; border-bottom: 2px solid #2E7D32; padding-bottom: .3rem; }
h2 { font-size: 1.4rem; border-bottom: 1px solid #ddd; padding-bottom: .2rem; }
h3 { font-size: 1.12rem; }
table { border-collapse: collapse; margin: 1rem 0; width: 100%; font-size: .95rem; }
th, td { border: 1px solid #ccc; padding: .4rem .6rem; text-align: left; vertical-align: top; }
th { background: #E8F5E9; }
code { background: #f2f2f2; padding: .1rem .3rem; border-radius: 3px; font-size: .9em; }
pre { background: #f6f8fa; padding: .8rem; border-radius: 6px; overflow-x: auto; }
pre code { background: none; padding: 0; }
blockquote { border-left: 3px solid #2E7D32; margin: 1rem 0; padding: .2rem 1rem;
             color: #444; background: #fafafa; }
hr { border: none; border-top: 1px solid #ddd; margin: 2rem 0; }
a { color: #2E7D32; }
@media (prefers-color-scheme: dark) {
  body { background: #1e1e1e; color: #e2e2e2; }
  th { background: #2a3b2a; } code { background: #333; } pre { background: #252525; }
  blockquote { background: #252525; color: #bbb; }
  h2, td, th { border-color: #444; } hr { border-color: #444; }
}
""".strip()


WORD_LISTS_DIR = Path(__file__).resolve().parent.parent / "standard_word_lists"

# Non-gloss columns a wordlist may contain (matched case-insensitively).
# 'index' is required; every column named by a tool's gloss_languages is
# required; 'extra' is optional.
REQUIRED_WORDLIST_COLUMNS = ["index"]
OPTIONAL_WORDLIST_COLUMNS = ["extra"]

# In a user-typed sentence frame, this marks where the item's gloss goes.
FRAME_PLACEHOLDER = "___"


@dataclass
class GlossLanguage:
    """One selectable gloss language for a tool: a display label + the wordlist
    column it maps to."""
    label: str
    column: str


@dataclass
class WordListTool:
    """Metadata for one bundled word list tool (not the word list itself)."""
    id: str
    name: str
    summary: str
    description: str          # markdown, shown on the tool's info page
    recommended_tokens: int
    order: int
    folder: Path
    gloss_languages: list[GlossLanguage] = field(default_factory=list)
    download_filename: str = ""

    @property
    def wordlist_path(self) -> Path | None:
        for ext in ("xlsx", "csv"):
            candidate = self.folder / f"wordlist.{ext}"
            if candidate.exists():
                return candidate
        return None

    @property
    def documentation_path(self) -> Path | None:
        """The Markdown documentation source, if the folder has one. It is
        served to users as HTML (see ``documentation_html``)."""
        candidate = self.folder / "documentation.md"
        return candidate if candidate.exists() else None

    @property
    def wordlist_download_name(self) -> str:
        """Filename to hand the user when they download the raw word list."""
        path = self.wordlist_path
        ext = path.suffix if path else ".xlsx"
        return self.download_filename or f"{self.id}{ext}"


def documentation_html(tool: WordListTool) -> str | None:
    """Render a tool's Markdown documentation as a self-contained HTML page
    (inline styles, no external resources) so it opens cleanly in any browser.
    Returns None if the tool has no documentation."""
    path = tool.documentation_path
    if path is None:
        return None

    md_text = path.read_text(encoding="utf-8")
    if _markdown is not None:
        body = _markdown.markdown(
            md_text,
            extensions=["tables", "fenced_code", "sane_lists"],
        )
    else:  # graceful fallback if the dependency is missing
        body = f"<pre>{escape(md_text)}</pre>"

    title = f"{tool.name} — documentation"
    return (
        "<!DOCTYPE html>\n"
        '<html lang="en">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f"<title>{escape(title)}</title>\n"
        f"<style>\n{_DOC_CSS}\n</style>\n</head>\n<body>\n"
        f"{body}\n</body>\n</html>\n"
    )


def _parse_gloss_languages(meta: dict) -> list[GlossLanguage]:
    langs: list[GlossLanguage] = []
    for entry in meta.get("gloss_languages", []):
        if not isinstance(entry, dict):
            continue
        column = str(entry.get("column", "")).strip().lower()
        if not column:
            continue
        label = str(entry.get("label") or column)
        langs.append(GlossLanguage(label=label, column=column))
    return langs


def list_word_list_tools() -> list[WordListTool]:
    """Discover every valid tool folder, sorted by (order, name)."""
    tools: list[WordListTool] = []
    if not WORD_LISTS_DIR.is_dir():
        return tools

    for folder in WORD_LISTS_DIR.iterdir():
        if not folder.is_dir():
            continue
        meta_path = folder / "tool.toml"
        if not meta_path.exists():
            continue
        try:
            meta = tomllib.loads(meta_path.read_text(encoding="utf-8"))
        except (tomllib.TOMLDecodeError, OSError):
            continue

        tool = WordListTool(
            id=folder.name,
            name=str(meta.get("name", folder.name)),
            summary=str(meta.get("summary", "")),
            description=str(meta.get("description", "")),
            recommended_tokens=int(meta.get("recommended_tokens", 1)),
            order=int(meta.get("order", 100)),
            folder=folder,
            gloss_languages=_parse_gloss_languages(meta),
            download_filename=str(meta.get("download_filename", "")).strip(),
        )
        if tool.wordlist_path is not None:
            tools.append(tool)

    tools.sort(key=lambda t: (t.order, t.name.lower()))
    return tools


def get_word_list_tool(tool_id: str) -> WordListTool | None:
    """Look up one tool by its folder id."""
    for tool in list_word_list_tools():
        if tool.id == tool_id:
            return tool
    return None


def load_word_list(tool: WordListTool) -> pd.DataFrame:
    """Read a tool's wordlist file, lower-casing its column names."""
    path = tool.wordlist_path
    if path is None:
        raise FileNotFoundError(f"No wordlist file in {tool.folder}")

    if path.suffix.lower() == ".xlsx":
        df = pd.read_excel(path)
    else:
        df = pd.read_csv(path)

    df.columns = [str(c).strip().lower() for c in df.columns]

    # Always present the word list in index order: the source file may have
    # rows out of sequence, but both the downloadable spreadsheet and the
    # generated import script must run 1, 2, 3, ...
    if "index" in df.columns:
        sort_key = pd.to_numeric(df["index"], errors="coerce")
        if sort_key.isna().any():  # non-numeric index - fall back to string sort
            sort_key = df["index"].astype(str)
        df = (
            df.assign(_sort_key=sort_key)
            .sort_values("_sort_key", kind="stable")
            .drop(columns="_sort_key")
            .reset_index(drop=True)
        )
    return df


def available_gloss_languages(tool: WordListTool, df: pd.DataFrame) -> list[GlossLanguage]:
    """The tool's gloss languages whose column is actually present in the file."""
    return [g for g in tool.gloss_languages if g.column in df.columns]


def validate_word_list(tool: WordListTool, df: pd.DataFrame) -> str | None:
    """Return an error message if the wordlist can't produce a script, else None."""
    if "index" not in df.columns:
        return "Word list is missing a required 'index' column."
    if df.empty:
        return "Word list has no rows."
    if df["index"].isna().any():
        return "Word list has blank values in the 'index' column."
    if df["index"].duplicated().any():
        dupes = df["index"][df["index"].duplicated()].unique()
        return f"Word list has duplicate index values: {', '.join(map(str, dupes))}."

    if not tool.gloss_languages:
        return "This tool defines no gloss languages (see tool.toml)."
    missing = [g.column for g in tool.gloss_languages if g.column not in df.columns]
    if missing:
        return f"Word list is missing gloss column(s): {', '.join(missing)}."
    return None


def apply_sentence_frame(
    df: pd.DataFrame,
    sentence_frame: str,
    gloss_column: str,
) -> pd.DataFrame:
    """Return a copy of df with a '_frame' column: the sentence frame with
    FRAME_PLACEHOLDER replaced by each row's value in ``gloss_column`` (frame
    shown as-is if it contains no placeholder)."""
    df = df.copy()
    df["_frame"] = df[gloss_column].map(
        lambda g: sentence_frame.replace(FRAME_PLACEHOLDER, str(g))
    )
    return df


def generate_tool_script(
    tool: WordListTool,
    num_tokens: int,
    primary_gloss_column: str,
    secondary_gloss_column: str | None = None,
    sentence_frame: str = "",
) -> ScriptResult:
    """Load the tool's wordlist and run it through the SpeechRecorder generator.

    ``primary_gloss_column`` / ``secondary_gloss_column`` are wordlist column
    names chosen from the tool's gloss languages. If ``sentence_frame`` is
    non-empty it's added to every prompt, with ``___`` replaced by that item's
    primary gloss.
    """
    try:
        df = load_word_list(tool)
    except Exception as e:  # noqa: BLE001 - surface any read failure to the UI
        return ScriptResult(success=False, error=f"Could not read the word list: {e}")

    error = validate_word_list(tool, df)
    if error:
        return ScriptResult(success=False, error=error)

    if primary_gloss_column not in df.columns:
        return ScriptResult(
            success=False,
            error=f"Primary gloss column '{primary_gloss_column}' is not in the word list.",
        )
    if secondary_gloss_column and secondary_gloss_column not in df.columns:
        secondary_gloss_column = None

    frame_col = None
    if sentence_frame and sentence_frame.strip():
        df = apply_sentence_frame(df, sentence_frame.strip(), primary_gloss_column)
        frame_col = "_frame"

    return generate_script(
        df=df,
        index_col="index",
        primary_gloss_col=primary_gloss_column,
        secondary_gloss_col=secondary_gloss_column,
        frame_col=frame_col,
        extra_col="extra" if "extra" in df.columns else None,
        num_tokens=num_tokens,
        tokens_in_frame=list(range(1, num_tokens + 1)) if frame_col else [],
    )


def read_wordlist_bytes(tool: WordListTool) -> bytes:
    """The tool's word list file, verbatim, for download."""
    path = tool.wordlist_path
    if path is None:
        raise FileNotFoundError(f"No wordlist file in {tool.folder}")
    return path.read_bytes()


def generate_tool_prompts_list(
    tool: WordListTool,
    primary_gloss_column: str,
    secondary_gloss_column: str | None = None,
) -> PromptsListResult:
    """Load the tool's wordlist and run it through the Prompts-list generator.

    The primary gloss becomes the app's ``gloss_v`` (shown large); the
    secondary gloss, if chosen, becomes ``gloss_e``. Standard word list tools
    carry no IPA column.
    """
    try:
        df = load_word_list(tool)
    except Exception as e:  # noqa: BLE001
        return PromptsListResult(success=False, error=f"Could not read the word list: {e}")

    error = validate_word_list(tool, df)
    if error:
        return PromptsListResult(success=False, error=error)

    if primary_gloss_column not in df.columns:
        return PromptsListResult(
            success=False,
            error=f"Primary gloss column '{primary_gloss_column}' is not in the word list.",
        )
    if secondary_gloss_column and secondary_gloss_column not in df.columns:
        secondary_gloss_column = None

    return generate_prompts_list(
        df=df,
        index_col="index",
        vernacular_col=primary_gloss_column,
        english_col=secondary_gloss_column,
    )
