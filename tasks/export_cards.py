"""
Export Sorting Activity Task
=============================

Builds a printable HTML card deck for orthography-development card-sorting
activities (originally "Participator Lite"). Users pick which database
columns appear as the (up to three) lines of text on each card, then export
a Letter-size, 10-cards-per-page HTML file with Lao/IPA-aware fonts.

The HTML/CSS/JS rendering in generate_cards_html() is a near-verbatim port
of Participator Lite's create_cards_html() -- getting the font stack right
(Lao script vs. IPA vs. plain text) took a lot of iteration originally, so
that part is treated as a locked black box and left unchanged. The only
thing that changed upstream of it is how each card's lines are assembled:
Participator Lite parsed a single "\\n"-delimited "prompt" column; here the
lines come directly from user-selected columns, so that fragile parsing
step is gone rather than added to.
"""

import re
import pandas as pd
from dataclasses import dataclass, field

# Same detection patterns used by Participator Lite's detect_script().
LAO_SCRIPT_PATTERN = r'[຀-໿]'
IPA_PATTERN = r'[/\[\]ˈˌːɑɐɒæɓʙβɔɕçɗɖðʤəɘɛɜɝɞɟʄɡɠɢʛɦɧħɥʜɨɪʝɭɬɫɮʟɱɯɰŋɳɲɴøɵɸθœɶʘɹɺɾɻʀʁɽʂʃʈʧʉʊʋⱱʌɣɤʍχʎʏʑʐʒʔʡʕʢǀǁǂǃˌˑʼʴʰʱʲʷˠˤ˞]'

# Character limits per line tier (mirrors lao/english/ipa limits in the original)
LINE_1_MAX_LENGTH = 30
LINE_2_MAX_LENGTH = 45
LINE_3_MAX_LENGTH = 45

CARDS_PER_PAGE = 10

# Sentinel representing "empty/NaN" as a selectable filter value
BLANK_SENTINEL = "(blank)"


# =============================================================================
# Filtering (Step 1: Filter Database)
# =============================================================================

def get_column_filter_options(df: pd.DataFrame, column: str) -> list[str]:
    """Return the sorted list of selectable filter values for a column,
    with a '(blank)' sentinel first if the column has any empty/NaN cells."""
    str_values = df[column].apply(lambda v: "" if pd.isna(v) else str(v))
    is_blank = df[column].isna() | (str_values.str.strip() == "")
    has_blank = bool(is_blank.any())
    unique_non_blank = sorted(set(v for v in str_values[~is_blank]))
    options = ([BLANK_SENTINEL] if has_blank else []) + unique_non_blank
    return options


def filter_dataframe(df: pd.DataFrame, selected_filters: dict[str, list[str]]) -> pd.DataFrame:
    """Filter df to rows matching every column's selected allowed values.

    selected_filters maps column name -> list of allowed value strings
    (may include BLANK_SENTINEL to allow empty/NaN cells). A column absent
    from selected_filters, or with all its options selected, is not filtered.
    """
    mask = pd.Series(True, index=df.index)

    for column, allowed_values in selected_filters.items():
        if column not in df.columns or not allowed_values:
            continue

        allow_blank = BLANK_SENTINEL in allowed_values
        allowed_non_blank = set(v for v in allowed_values if v != BLANK_SENTINEL)

        str_values = df[column].apply(lambda v: "" if pd.isna(v) else str(v))
        is_blank = df[column].isna() | (str_values.str.strip() == "")

        column_mask = (is_blank & allow_blank) | (~is_blank & str_values.isin(allowed_non_blank))
        mask &= column_mask

    return df[mask]


# =============================================================================
# Card Building (Step 2: Card Content)
# =============================================================================

@dataclass
class Card:
    """A single card: up to 3 lines of text, top to bottom, plus its index label."""
    lines: list[str]
    index_display: str


@dataclass
class CardBuildResult:
    success: bool
    cards: list[Card] = field(default_factory=list)
    total_rows: int = 0
    included_rows: int = 0
    error: str | None = None
    duplicate_indices: list[str] = field(default_factory=list)


def sort_dataframe(df: pd.DataFrame, sort_col: str | None) -> pd.DataFrame:
    """Sort df by sort_col (stable, ascending, blanks last). Returns df unchanged
    if sort_col is None/empty or not a column of df."""
    if not sort_col or sort_col not in df.columns:
        return df
    return df.sort_values(by=sort_col, kind="stable", na_position="last")


def build_cards(
    df: pd.DataFrame,
    index_col: str,
    sub_index_col: str | None,
    line_columns: list[str],
    sort_by_col: str | None = None,
) -> CardBuildResult:
    """Build one Card per row of df from the selected line columns.

    Args:
        df: The (already filtered) dataframe to build cards from.
        index_col: Column holding the index value.
        sub_index_col: Optional column holding the sub-index value. If
            provided, card_index_display is "{index}.{sub_index}"; the
            index+sub_index pair must be unique. If None, just "{index}"
            is used and must be unique on its own.
        line_columns: 1-3 column names, in display order top to bottom.
        sort_by_col: Optional column (normally one of line_columns) to sort
            the cards by before export -- e.g. so near-duplicate entries
            land next to each other in the printed grid.
    """
    df = sort_dataframe(df, sort_by_col)
    total_rows = len(df)

    if total_rows == 0:
        return CardBuildResult(success=False, error="No rows to build cards from. Adjust your filters.", total_rows=0)

    if not line_columns:
        return CardBuildResult(success=False, error="Select at least one column for card content.", total_rows=total_rows)

    if sub_index_col:
        compound_index = df[index_col].astype(str) + "." + df[sub_index_col].astype(str)
    else:
        compound_index = df[index_col].astype(str)

    duplicated_mask = compound_index.duplicated()
    if duplicated_mask.any():
        duplicates = sorted(compound_index[duplicated_mask].unique().tolist())
        return CardBuildResult(
            success=False,
            error="Duplicate index values found among the rows being exported. Each card must have a unique index"
                  + (" + sub_index." if sub_index_col else "."),
            duplicate_indices=duplicates,
            total_rows=total_rows,
        )

    cards = []
    for _, row in df.iterrows():
        lines = ["" if pd.isna(row[col]) else str(row[col]) for col in line_columns]
        if sub_index_col:
            index_display = f"{row[index_col]}.{row[sub_index_col]}"
        else:
            index_display = f"{row[index_col]}"
        cards.append(Card(lines=lines, index_display=index_display))

    return CardBuildResult(success=True, cards=cards, total_rows=total_rows, included_rows=len(cards))


# =============================================================================
# HTML Export (Step 3) -- ported near-verbatim from Participator Lite
# =============================================================================

def _truncate_text(text: str, max_length: int) -> str:
    if len(text) > max_length:
        return text[:max_length - 3] + "..."
    return text


def generate_cards_html(cards: list[Card]) -> str:
    """Render cards into a printable HTML document (10 cards/page, US Letter).

    This mirrors Participator Lite's create_cards_html() exactly in its
    CSS, font stack, and font-forcing JS -- only the per-card text
    assembly is adapted to work from Card.lines instead of a delimited
    "prompt" string.
    """
    pages_html = []
    current_page = []

    for card in cards:
        lines = card.lines

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

        index_display = card.index_display

        full_text = "\n".join(lines)
        has_lao = bool(re.search(LAO_SCRIPT_PATTERN, full_text))
        has_ipa = bool(re.search(IPA_PATTERN, full_text))

        css_class = ""
        if has_lao and has_ipa:
            css_class = "mixed"
        elif has_lao:
            css_class = "lao"
        elif has_ipa:
            css_class = "ipa"

        card_html = f'''
        <div class="card">
            <div class="card-content {css_class}">{formatted_text}</div>
            <div class="card-index">{index_display}</div>
        </div>'''

        current_page.append(card_html)

        if len(current_page) == CARDS_PER_PAGE:
            pages_html.append("".join(current_page))
            current_page = []

    if current_page:
        pages_html.append("".join(current_page))

    wrapped_pages = []
    for page_content in pages_html:
        wrapped_pages.append(f'''
    <div class="page">
{page_content}
    </div>''')

    card_content = "\n".join(wrapped_pages)

    html = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sorting Activity Cards</title>
    <!-- Google Fonts for Lao script support -->
    <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Noto+Sans+Lao:wght@400;700&display=swap">
    <!-- Google Fonts for IPA support -->
    <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Noto+Sans:wght@400;700&display=swap">
    <style>
        /* Font face declarations */
        @font-face {
            font-family: 'Saysettha OT';
            src: local('Saysettha OT');
            font-weight: normal;
            font-style: normal;
        }

        /* Reset any default styles that might be coming from OS */
        * {
            -webkit-font-smoothing: antialiased;
            -moz-osx-font-smoothing: grayscale;
        }

        @page {
            size: letter;
            margin: 0.5in;
        }
        body {
            font-family: 'Noto Sans', Arial, 'Arial Unicode MS', sans-serif;
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        .page {
            page-break-after: always;
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            grid-template-rows: repeat(5, 1fr);
            gap: 0.35in;
            padding: 0.2in;
            height: 9.7in;  /* Letter paper height minus margins */
        }
        .page:last-child {
            page-break-after: avoid;
        }
        .card {
            width: 3in; /* Fixed width */
            height: 1.7in; /* Fixed height */
            border: 1px solid black;
            position: relative;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 0.15in;
            box-sizing: border-box;
            overflow: hidden;
            margin: 0 auto; /* Center card in grid cell */
        }
        .card-content {
            text-align: center;
            width: 100%;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            max-width: 100%;
        }
        .lao-text {
            font-size: 18pt; /* Larger Lao text */
            line-height: 1.4;
            margin-bottom: 0.05in;
            font-family: 'Saysettha OT', 'Noto Sans Lao', 'Phetsarath OT', sans-serif !important;
            width: 100%;
            word-wrap: break-word;
            overflow-wrap: break-word;
        }
        .english-text {
            font-size: 12pt; /* Smaller English text */
            line-height: 1.3;
            margin-bottom: 0.05in;
            font-family: 'Noto Sans', Arial, sans-serif;
            width: 100%;
            word-wrap: break-word;
            overflow-wrap: break-word;
        }
        .ipa-text {
            font-size: 12pt; /* Smaller IPA text */
            line-height: 1.3;
            font-family: 'Noto Sans', 'Charis SIL', 'Doulos SIL', 'Arial Unicode MS', sans-serif;
            width: 100%;
            word-wrap: break-word;
            overflow-wrap: break-word;
        }
        .card-index {
            position: absolute;
            bottom: 0.1in;
            right: 0.1in;
            font-size: 8pt;
        }
        /* Font stack for Lao script - explicitly avoid Dok Champa */
        .card-content.lao {
            font-family: 'Saysettha OT', 'Noto Sans Lao', 'Phetsarath OT', sans-serif !important;
            font-size: 18pt;
        }
        /* Additional selectors to ensure proper font application */
        [class*="lao"] {
            font-family: 'Saysettha OT', 'Noto Sans Lao', 'Phetsarath OT', sans-serif !important;
        }

        /* IPA specific styles */
        .card-content.ipa {
            font-family: 'Noto Sans', 'Charis SIL', 'Doulos SIL', 'Arial Unicode MS', sans-serif;
            font-size: 14pt;
        }

        /* Mixed content (both Lao and IPA) */
        .card-content.mixed {
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
        }

        @media print {
            body {
                width: 8.5in;
                margin: 0;
                padding: 0;
            }
            .page {
                margin: 0.5in;
                height: 9.7in;  /* Letter paper height minus margins */
                page-break-after: always;
                page-break-inside: avoid;
            }
            .page:last-child {
                page-break-after: avoid;
            }
            .card {
                page-break-inside: avoid;
            }
            .no-print {
                display: none;
            }
        }
        .controls {
            padding: 1em;
            margin-bottom: 1em;
            background-color: #f0f0f0;
        }
        button {
            padding: 0.5em 1em;
            margin-right: 0.5em;
        }
        /* Font sample for debugging */
        .font-sample {
            margin: 10px 0;
            padding: 10px;
            border: 1px solid #ccc;
        }
    </style>
    <script>
        // Function to toggle debug information
        function toggleDebug() {
            document.body.classList.toggle('show-debug');
        }

        window.onload = function() {
            // Force Saysettha OT font for all Lao text
            document.querySelectorAll('.lao-text, .card-content.lao').forEach(function(element) {
                let text = element.textContent || element.innerText;
                if (/[຀-໿]/.test(text)) {
                    element.setAttribute('lang', 'lo');

                    // Force style directly with !important to override any other styles
                    element.style.fontFamily = "'Saysettha OT', 'Noto Sans Lao', 'Phetsarath OT', sans-serif !important";
                    // Enforce with a higher priority by setting it directly on the element
                    element.setAttribute('style', element.getAttribute('style') + "; font-family: 'Saysettha OT', 'Noto Sans Lao', 'Phetsarath OT', sans-serif !important");
                }
            });

            // Set appropriate style for IPA text
            document.querySelectorAll('.ipa-text').forEach(function(element) {
                let text = element.textContent || element.innerText;
                if (/[/\[\]ˈˌːɑɐɒæɓʙβɔɕçɗɖðʤəɘɛɜɝɞɟʄɡɠɢʛɦɧħɥʜɨɪʝɭɬɫɮʟɱɯɰŋɳɲɴøɵɸθœɶʘɹɺɾɻʀʁɽʂʃʈʧʉʊʋⱱʌɣɤʍχʎʏʑʐʒʔʡʕʢǀǁǂǃˌˑʼʴʰʱʲʷˠˤ˞]/.test(text)) {
                    element.classList.add('has-ipa');
                }
            });

            // Update the cards per page display
            document.getElementById('cardsPerPage').textContent = "''' + str(CARDS_PER_PAGE) + '''";
        };
    </script>
</head>
<body>
    <div class="controls no-print">
        <h1>Sorting Activity Cards</h1>
        <p>Click the Print button below or use your browser's print function to print these cards.</p>
        <button onclick="window.print()">Print Cards</button>
        <p>Cards per page: <span id="cardsPerPage">''' + str(CARDS_PER_PAGE) + '''</span></p>
        <div class="font-sample">
            <h3>Font Samples:</h3>
            <p>Saysettha OT: <span style="font-family: 'Saysettha OT', sans-serif;">ລາວ ພາສາລາວ</span></p>
            <p>Noto Sans Lao: <span style="font-family: 'Noto Sans Lao', sans-serif;">ລາວ ພາສາລາວ</span></p>
            <p>IPA: <span style="font-family: 'Noto Sans', sans-serif;">/kʰwaam.suk/</span></p>
        </div>
    </div>'''

    return html + card_content + '''
</body>
</html>'''
