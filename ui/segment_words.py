"""
ui/segment_words.py
Screen for segmenting words into phonological columns.
"""

import pandas as pd
import streamlit as st

from tasks.segment_words import check_stop_h
from tasks import segment_words, export_database
from ui.shared import render_colon_locations
from ui.navigation import Screen, navigate_to, go_back_to_menu


STOP_H_WARNING = (
    "**Warning:** Excelerant will interpret sequences of stop/affricate + h/ɦ "
    "as a single aspirated segment (see examples below). If the \"h\" or \"ɦ\" "
    "characters in these "
    "examples actually represent a separate segment, you should either "
    "(1) quit now and update the transcription in your database before running "
    "Excelerant again or (2) allow Excelerant to continue, understanding that "
    "you will need to fix the segmentation of words like this later."
)


def _render_stop_h_warning(stop_h):
    """Warning shown before segmenting when words contain stop + plain 'h'."""
    st.warning(STOP_H_WARNING)

    n = len(stop_h.row_ids)
    st.markdown(
        f"**{n:,} {'word contains' if n == 1 else 'words contain'}** "
        "a stop or affricate followed by `h` or `ɦ`."
    )
    if stop_h.examples is not None:
        shown = len(stop_h.examples)
        caption = "How Excelerant will segment them"
        if shown < len(stop_h.row_ids):
            caption += f" (first {shown})"
        st.markdown(f"**{caption}:**")
        st.dataframe(stop_h.examples, width="stretch", hide_index=True)

    st.caption("IDs of all affected words (index.sub_index; use the copy button):")
    st.code(", ".join(stop_h.row_ids), language=None, wrap_lines=True)

    stop_col, continue_col = st.columns(2)
    with stop_col:
        if st.button("Stop and fix my database", width="stretch"):
            st.session_state.pop("_segment_params", None)
            go_back_to_menu()
    with continue_col:
        if st.button("Continue anyway", type="primary", width="stretch"):
            st.session_state._segment_params["stop_h_confirmed"] = True
            st.rerun()


def screen_segment_words():
    """Screen for segmenting words into phonological columns."""

    # Add vertical divider CSS
    st.markdown(
        """
        <style>
        div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"]:first-child {
            border-right: 1px solid #ccc;
            padding-right: 1.5rem !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.title("Segment Words")
    st.markdown("---")

    # Two-column layout
    config_col, output_col = st.columns([1, 2])

    df = st.session_state.database
    columns = list(df.columns)

    with config_col:
        st.subheader("Configuration")

        # Auto-detect word column
        word_col = None
        for col in columns:
            if col.lower() == 'word':
                word_col = col
                break

        if word_col:
            st.success(f"Word column detected: **{word_col}**")
        else:
            st.info(
                "No 'word' column found. Run **Explode Entries** first, "
                "or select a column containing individual words below."
            )
            word_col = st.selectbox(
                "Select word column",
                options=columns,
                help="Column containing individual IPA-transcribed words to segment",
            )

        st.markdown("---")

        # Process button
        process_clicked = st.button(
            "Segment Words",
            type="primary",
            width="stretch",
        )

        if process_clicked:
            st.session_state._segment_params = {
                "word_col": word_col,
            }
            st.rerun()

        st.markdown("---")

        if st.button("Back to Main Menu", width="stretch"):
            for key in ["_segment_params", "_segment_result"]:
                if key in st.session_state:
                    del st.session_state[key]
            go_back_to_menu()

    # === OUTPUT COLUMN ===
    with output_col:
        st.subheader("Output")

        # Before segmenting, warn about stop + plain 'h' (read as aspiration)
        # and wait for the user to stop or continue
        params = st.session_state.get("_segment_params")
        if params and not params.get("stop_h_confirmed"):
            stop_h = check_stop_h(df, params["word_col"])
            if stop_h.row_ids:
                _render_stop_h_warning(stop_h)
                return

        # Process if triggered
        if "_segment_params" in st.session_state:
            params = st.session_state._segment_params
            del st.session_state._segment_params

            with st.spinner("Segmenting words..."):
                result = segment_words(
                    df=df,
                    word_col=params["word_col"],
                )

            if result.success:
                st.session_state._segment_result = result
                st.session_state._scroll_to_top = True
                st.session_state.database = result.df
                st.session_state.database_validated = True
                st.rerun()
            else:
                st.error(f"**Error:** {result.error}")
                if result.colon_locations:
                    render_colon_locations(result.colon_locations)

                st.markdown("---")

                if st.button("Clear Database & Start Over", type="primary", width="stretch"):
                    for key in ["_segment_params", "_segment_result"]:
                        if key in st.session_state:
                            del st.session_state[key]
                    st.session_state.database = None
                    st.session_state.database_validated = False
                    st.session_state.database_filename = None
                    st.session_state.database_sheet_name = None
                    st.session_state.selected_task = None
                    navigate_to(Screen.UPLOAD_DATABASE)

        # Display result if available
        if "_segment_result" in st.session_state:
            result = st.session_state._segment_result
            error_count = result.summary.get("error_count", 0)
            total_words = result.summary.get("total_words", 0)
            words_segmented = result.summary.get("words_segmented", 0)

            if error_count == 0:
                st.success("All words segmented successfully!")
            else:
                st.warning(
                    f"Segmentation complete with {error_count} error(s) "
                    f"out of {total_words} words."
                )

            untranscribed = result.summary.get("untranscribed_rows", 0)
            if untranscribed:
                st.info(
                    f"{untranscribed:,} rows have no word yet. They were kept with blank "
                    "segmentation columns."
                )

            st.markdown(f"""
            **Summary:**
            - Words segmented: {words_segmented}
            - Errors: {error_count}
            - Total words: {total_words}
            """)

            # Show errors in expander
            if error_count > 0:
                error_words = result.summary.get("error_words", {})
                with st.expander(f"Error details ({error_count} words)", expanded=False):
                    st.markdown(
                        "These words have `'error'` in their segmentation columns:"
                    )
                    for word_text, reason in list(error_words.items())[:30]:
                        st.text(f"  '{word_text}': {reason}")
                    if len(error_words) > 30:
                        st.text(f"  ... and {len(error_words) - 30} more")

            # Cleaning report
            if result.cleaning_report.get("changes_made"):
                with st.expander("Cleaning report", expanded=False):
                    punct = result.cleaning_report.get("punctuation_removed", {})
                    ws = result.cleaning_report.get("whitespace_changes", 0)
                    if punct:
                        st.markdown("**Punctuation removed:**")
                        for char, count in punct.items():
                            st.text(f"  '{char}': {count}")
                    if ws:
                        st.markdown(f"**Whitespace normalized:** {ws} cells")
                    converted = result.cleaning_report.get("precomposed_converted", {})
                    if converted:
                        st.markdown(
                            "**Characters converted to Excelerant's form** (they look the "
                            "same, but were stored as a different Unicode sequence):"
                        )
                        for char, count in converted.items():
                            st.text(f"  '{char}': {count}")

            st.markdown("---")

            # Buttons row
            btn_col1, btn_col2 = st.columns(2)

            with btn_col1:
                st.download_button(
                    label="Download Updated Database",
                    data=export_database(result.df),
                    file_name="database_segmented.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    type="primary",
                    width="stretch",
                )

            with btn_col2:
                if st.button("Return to Main Menu", width="stretch", key="return_after_segment"):
                    for key in ["_segment_params", "_segment_result"]:
                        if key in st.session_state:
                            del st.session_state[key]
                    go_back_to_menu()

            st.markdown("---")

            st.markdown("**Updated Database Preview:**")
            preview_cols = []
            for col in ['index', 'sub_index', 'word', 'P', 'R', 'C', 'M', 'V', 'F', 'T']:
                if col in result.df.columns:
                    preview_cols.append(col)

            if preview_cols:
                st.dataframe(result.df[preview_cols].head(20), width="stretch")
            else:
                st.dataframe(result.df.head(20), width="stretch")

        else:
            # Initial state - show instructions
            st.info(
                "Click **Segment Words** to break words into phonological columns."
            )

            st.markdown("---")

            st.markdown("**About This Task**")
            st.markdown(
                """
                This task breaks IPA-transcribed words into phonological columns:

                | Column | Description |
                |--------|-------------|
                | **P** | Presyllable onset |
                | **R** | Presyllable rime |
                | **C** | Main syllable onset (consonant; a tied pair such as `t͡s` or `k͡p` is one C) |
                | **M** | Medial (glide between onset and vowel) |
                | **V** | Vowel (nucleus; a long vowel with an offglide, e.g. `iːə`, is one V) |
                | **F** | Final (coda) |
                | **T** | Tone / register |

                A tie (`͡`) joins two consonants into one segment: affricates
                (`t͡s`, `t͡ɕ`) and double articulations (`k͡p`, `g͡b`). Ties written
                below (`͜`) are converted to `͡`. Untied sequences like `kp` are
                not joined; they're read as a presyllable (`kapa`).

                Stops and affricates, voiceless or voiced, can be aspirated with
                `ʰ` or `ʱ`: `pʰ`, `bʰ`, `bʱ`, `tɕʰ`, `dʑʱ`, `t͡ɕʰ`, `d͡ʑʱ`.

                Words containing non-IPA characters, invalid tone sequences,
                a tie that doesn't join two consonants, or no detectable vowels
                will have `'error'` in their segmentation columns. These do not
                block processing of other words.
                """
            )

            st.markdown("---")

            st.markdown("**Example (before):**")
            example_before = pd.DataFrame({
                'index': [1, 1, 2],
                'sub_index': [1, 2, 1],
                'word': ['kʰaːw', 'maː', 'pa'],
            })
            st.dataframe(example_before, width="stretch", hide_index=True)

            st.markdown("**Example (after):**")
            example_after = pd.DataFrame({
                'index': [1, 1, 2],
                'sub_index': [1, 2, 1],
                'word': ['kʰaːw', 'maː', 'pa'],
                'P': ['', '', ''],
                'R': ['', '', ''],
                'C': ['kʰ', 'm', 'p'],
                'M': ['', '', ''],
                'V': ['aː', 'aː', 'a'],
                'F': ['w', '∅', '∅'],
                'T': ['', '', ''],
            })
            st.dataframe(example_after, width="stretch", hide_index=True)
