"""
Sort Cards Task
================

Digital, in-app card sorting -- an alternative to the physical
Generate-Cards-then-sort-then-Process-Cards workflow for cases where
printing isn't practical, or for handing a sorting task off to a remote
participant. One card is shown at a time; the sorter assigns it to a
pile (or skips it) until the deck is empty.

Sort Cards never writes to the database directly. A finished (or
paused) sort is exported as a JSON file in the same format Generate
Cards' prepared activities use -- see SORT_CARDS_JSON_FORMAT.md at the
project root -- and brought into the database via Process Cards' JSON
import method, the same path a remote participant's results would take.
This keeps exactly one place in the app that ever writes sort results
into the database.

The deck itself is built with generate_cards.py's build_cards(), so a
digital sort's card content, uniqueness validation, and Lao/IPA-aware
styling all stay in sync with the physical card deck rather than
reimplementing any of that.
"""

import html
import re

from .generate_cards import Card, LAO_SCRIPT_PATTERN, IPA_PATTERN, LINE_1_MAX_LENGTH, LINE_2_MAX_LENGTH, LINE_3_MAX_LENGTH


def _truncate_text(text: str, max_length: int) -> str:
    if len(text) > max_length:
        return text[:max_length - 3] + "..."
    return text


def _format_card_display(card: Card) -> tuple[str, str]:
    """Build (formatted_text, css_class) for one card's HTML content.

    Mirrors generate_cards_html()'s per-card formatting (line tiers,
    truncation, Lao/IPA detection), kept as a separate function rather
    than factored out of that "locked" one so the tested physical-card
    export is never touched. Unlike that function, lines are HTML-escaped
    here -- this renders directly in the live app's DOM (not a standalone
    downloaded file), so a stray "<" or "&" in the data shouldn't be able
    to break the page.
    """
    lines = [html.escape(line) for line in card.lines]

    if len(lines) >= 3:
        line_1 = _truncate_text(lines[0], LINE_1_MAX_LENGTH)
        line_2 = _truncate_text(lines[1], LINE_2_MAX_LENGTH)
        line_3 = _truncate_text(lines[2], LINE_3_MAX_LENGTH)
        formatted_text = f'''
            <div class="lao-text">{line_1}</div>
            <div class="english-text">{line_2}</div>
            <div class="ipa-text">{line_3}</div>
            '''
    elif len(lines) == 2:
        line_1 = _truncate_text(lines[0], LINE_1_MAX_LENGTH)
        line_2 = _truncate_text(lines[1], LINE_2_MAX_LENGTH)
        formatted_text = f'''
            <div class="lao-text">{line_1}</div>
            <div class="english-text">{line_2}</div>
            '''
    else:
        single_line = lines[0] if lines else ""
        formatted_text = _truncate_text(single_line, LINE_2_MAX_LENGTH)

    full_text = "\n".join(card.lines)
    has_lao = bool(re.search(LAO_SCRIPT_PATTERN, full_text))
    has_ipa = bool(re.search(IPA_PATTERN, full_text))

    css_class = ""
    if has_lao and has_ipa:
        css_class = "mixed"
    elif has_lao:
        css_class = "lao"
    elif has_ipa:
        css_class = "ipa"

    return formatted_text, css_class


_SINGLE_CARD_FONT_LINKS = (
    '<link rel="stylesheet" '
    'href="https://fonts.googleapis.com/css2?family=Noto+Sans+Lao:wght@400;700&display=swap">'
    '<link rel="stylesheet" '
    'href="https://fonts.googleapis.com/css2?family=Noto+Sans:wght@400;700&display=swap">'
)

_SINGLE_CARD_CSS = '''
<style>
.sc-card-display {
    display: flex;
    justify-content: center;
    margin: 1rem 0;
}
.sc-card-display .card {
    width: 400px;
    height: 220px;
    border: 2px solid black;
    border-radius: 4px;
    position: relative;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 0.6rem;
    box-sizing: border-box;
    overflow: hidden;
    background: white;
}
.sc-card-display .card-content {
    text-align: center;
    width: 100%;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    max-width: 100%;
    color: #111;
}
.sc-card-display .lao-text {
    font-size: 26pt;
    line-height: 1.4;
    margin-bottom: 0.2rem;
    font-family: 'Saysettha OT', 'Noto Sans Lao', 'Phetsarath OT', sans-serif !important;
    width: 100%;
    word-wrap: break-word;
    overflow-wrap: break-word;
}
.sc-card-display .english-text {
    font-size: 18pt;
    line-height: 1.3;
    margin-bottom: 0.2rem;
    font-family: 'Noto Sans', Arial, sans-serif;
    width: 100%;
    word-wrap: break-word;
    overflow-wrap: break-word;
}
.sc-card-display .ipa-text {
    font-size: 18pt;
    line-height: 1.3;
    font-family: 'Noto Sans', 'Charis SIL', 'Doulos SIL', 'Arial Unicode MS', sans-serif;
    width: 100%;
    word-wrap: break-word;
    overflow-wrap: break-word;
}
.sc-card-display .card-index {
    position: absolute;
    bottom: 0.5rem;
    right: 0.7rem;
    font-size: 11pt;
    color: #555;
}
.sc-card-display .card-content.lao {
    font-family: 'Saysettha OT', 'Noto Sans Lao', 'Phetsarath OT', sans-serif !important;
}
.sc-card-display .card-content.ipa {
    font-family: 'Noto Sans', 'Charis SIL', 'Doulos SIL', 'Arial Unicode MS', sans-serif;
}
</style>
'''


def generate_single_card_html(card: Card) -> str:
    """Render one Card as a standalone HTML snippet for Sort Cards' "current
    card" display -- same border box, font stack, and bottom-right UID as
    the printed cards from generate_cards_html(), just sized for on-screen
    display instead of a printable grid.

    Every line is stripped of leading whitespace before returning: when
    this is passed to st.markdown(unsafe_allow_html=True), Markdown's own
    "4-space indented text is a code block" rule fires on indented HTML
    (even with unsafe_allow_html on) and renders it as literal text
    instead of live markup, unless indentation is removed first.
    """
    formatted_text, css_class = _format_card_display(card)

    html_out = (
        _SINGLE_CARD_FONT_LINKS
        + _SINGLE_CARD_CSS
        + f'''
        <div class="sc-card-display">
            <div class="card">
                <div class="card-content {css_class}">{formatted_text}</div>
                <div class="card-index">{html.escape(card.index_display)}</div>
            </div>
        </div>
        '''
    )
    return "\n".join(line.lstrip() for line in html_out.splitlines())


def find_card_index_by_uid(cards: list[Card], uid: str) -> int | None:
    """Return the position of the card whose index_display matches uid,
    or None if not found. Used for Sort Cards' quick-entry UID lookups."""
    for i, card in enumerate(cards):
        if card.index_display == uid:
            return i
    return None
