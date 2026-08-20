"""
ui/process_cards.py
Screen for recording card-sorting activity results back into the database.
"""

import pandas as pd
import streamlit as st

from tasks import (
    ProcessCardsResult,
    sanitize_activity_column_name,
    parse_uid_list,
    process_cards_manual,
    AI_ASSISTED_PROMPT,
    AIOutputParseResult,
    parse_ai_assisted_output,
    export_database,
)
from ui.navigation import go_back_to_menu


def _clear_process_cards_state():
    """Remove all Process Cards session-state, including per-category widget keys."""
    for cat_id in st.session_state.get("_process_cards_categories", []):
        for prefix in ("_pc_label_", "_pc_uids_"):
            key = f"{prefix}{cat_id}"
            if key in st.session_state:
                del st.session_state[key]

    for key in [
        "_process_cards_categories",
        "_process_cards_next_id",
        "_process_cards_generate_params",
        "_process_cards_result",
        "_process_cards_method",
        "_pc_ai_paste",
        "_process_cards_ai_parse_feedback",
    ]:
        if key in st.session_state:
            del st.session_state[key]


def screen_process_cards():
    """Screen for recording card-sorting activity results back into the database."""

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

    st.title("Process Cards")
    st.markdown("---")

    config_col, output_col = st.columns([1, 2])

    df = st.session_state.database
    columns = list(df.columns)

    with config_col:
        # === METHOD ===
        st.subheader("Method")

        if "_process_cards_method" not in st.session_state:
            st.session_state._process_cards_method = "manual"

        def _method_pill(label: str):
            st.markdown(
                f'<div style="padding:0.5rem 1rem;border-radius:0.5rem;'
                f'background-color:#2E7D32;color:white;text-align:center;'
                f'font-weight:600;">{label}</div>',
                unsafe_allow_html=True,
            )

        method_col1, method_col2 = st.columns(2)
        with method_col1:
            if st.session_state._process_cards_method == "manual":
                _method_pill("Manual Input")
            elif st.button("Manual Input", use_container_width=True):
                st.session_state._process_cards_method = "manual"
                st.rerun()
        with method_col2:
            if st.session_state._process_cards_method == "ai":
                _method_pill("AI-Assisted Input")
            elif st.button("AI-Assisted Input", use_container_width=True):
                st.session_state._process_cards_method = "ai"
                st.rerun()

        st.markdown("---")

        # === STEP 1: INDEX COLUMNS ===
        st.subheader("Step 1: Index Columns")
        st.caption("Must match the index/sub-index columns used to print the cards, so UIDs line up.")

        index_default = columns.index("index") if "index" in columns else 0
        index_col = st.selectbox(
            "Index column",
            options=columns,
            index=index_default,
            key="_pc_index_col",
        )

        sub_index_options = ["-none-"] + columns
        sub_index_default = sub_index_options.index("sub_index") if "sub_index" in columns else 0
        sub_index_choice = st.selectbox(
            "Sub-index column (optional)",
            options=sub_index_options,
            index=sub_index_default,
            key="_pc_sub_index_col",
            help="Select this if the cards were printed with 'index.sub_index' UIDs.",
        )
        sub_index_col = None if sub_index_choice == "-none-" else sub_index_choice

        st.markdown("---")

        # === STEP 2: ACTIVITY NAME ===
        st.subheader("Step 2: Sorting Activity Name")

        activity_name = st.text_input(
            "Activity name",
            key="_pc_activity_name",
            placeholder="e.g. front p",
            help="Becomes the new database column name. Spaces are replaced with underscores.",
        )

        sanitized_column_name = sanitize_activity_column_name(activity_name)
        if sanitized_column_name:
            if sanitized_column_name in df.columns:
                st.caption(f"Column name: `{sanitized_column_name}` -- already exists, choose another name.")
            else:
                st.caption(f"Column name: `{sanitized_column_name}`")

        st.markdown("---")

        # === AI-ASSISTED INPUT (photo-based pre-fill for Step 3) ===
        if st.session_state._process_cards_method == "ai":
            st.subheader("AI-Assisted Photo Reading")

            with st.expander("How AI-Assisted Input works -- read before your workshop", expanded=True):
                st.markdown(
                    """
                    This method uses an AI chat tool you already have access to (Claude, ChatGPT,
                    or similar) to read the UID codes off photographed cards, instead of you typing
                    them in by hand. Plan the photo side of this **before** your workshop:

                    **1. During the workshop -- spread and photograph each pile**

                    For each sorted pile, spread the cards out so every card's UID (bottom-right
                    corner) is visible in the photo -- a stacked deck only shows the top card.
                    Take one photo per pile; if a pile is too big to fit in one frame, take
                    several photos of it.

                    **2. Name your photos by category**

                    Rename each photo to match the category it shows, e.g. `i.jpg`. If a pile
                    needed more than one photo, add a number: `i_2.jpg`, `i_3.jpg` -- these get
                    combined back into a single "i" category automatically. The name becomes the
                    value written into the database for every card in that pile, so spell it
                    exactly as you want it to appear.

                    **3. Get the codes read by AI**

                    Copy the prompt below, start a new conversation in Claude, ChatGPT, or a
                    similar tool, paste the prompt in, and attach all of your category-labeled
                    photos to that same message. If you're shooting on an iPhone, note that AI
                    chat tools don't reliably accept its default `.HEIC` photos -- switch to
                    "Most Compatible" mode first (Settings > Camera > Formats) so photos save as
                    `.jpg`, or convert existing ones before uploading.

                    **4. Bring the results back here**

                    Copy the AI's full reply, paste it into the box below, and click
                    **Parse & Fill Categories** to fill in Step 3. Review what gets filled in
                    before processing -- a misread code will usually show up as a UID "not found"
                    error below, which is your cue to check the original photo.
                    """
                )

            st.markdown("**Prompt to copy into your AI chat tool:**")
            st.code(AI_ASSISTED_PROMPT, language=None)

            ai_paste_text = st.text_area(
                "Paste the AI's reply here",
                key="_pc_ai_paste",
                height=150,
                placeholder="i.jpg: 4, 9, 22.1\ni_2.jpg: 15, 30.2\ne.jpg: 3, 7, 12.1",
            )

            st.caption("After pasting, press **Ctrl+Enter** (or **Cmd+Enter** on Mac) to submit the text before clicking the button below.")

            if st.button(
                "Parse & Fill Categories",
                use_container_width=True,
                disabled=not ai_paste_text.strip(),
            ):
                parse_result = parse_ai_assisted_output(ai_paste_text)
                st.session_state._process_cards_ai_parse_feedback = parse_result

                if parse_result.success:
                    for cat_id in st.session_state.get("_process_cards_categories", []):
                        for prefix in ("_pc_label_", "_pc_uids_"):
                            key = f"{prefix}{cat_id}"
                            if key in st.session_state:
                                del st.session_state[key]

                    next_id = st.session_state.get("_process_cards_next_id", 0)
                    new_ids = []
                    for label, uid_text in parse_result.categories:
                        st.session_state[f"_pc_label_{next_id}"] = label
                        st.session_state[f"_pc_uids_{next_id}"] = uid_text
                        new_ids.append(next_id)
                        next_id += 1

                    st.session_state._process_cards_categories = new_ids
                    st.session_state._process_cards_next_id = next_id

                st.rerun()

            ai_feedback: AIOutputParseResult | None = st.session_state.get("_process_cards_ai_parse_feedback")
            if ai_feedback is not None:
                if ai_feedback.success:
                    n = len(ai_feedback.categories)
                    st.success(f"Filled in {n} categor{'y' if n == 1 else 'ies'} below -- review before processing.")
                else:
                    st.error(ai_feedback.error)
                if ai_feedback.unparsed_lines:
                    st.warning(
                        "Some lines didn't match the expected format and were skipped:\n\n"
                        + "\n".join(f"- {ln}" for ln in ai_feedback.unparsed_lines)
                    )

            st.markdown("---")

        # === STEP 3: CATEGORIES ===
        st.subheader("Step 3: Categories")
        st.caption(
            "One category per pile the cards were sorted into. Enter the UID from the "
            "bottom-right of each card, separated by commas, spaces, or newlines."
        )

        if "_process_cards_categories" not in st.session_state:
            st.session_state._process_cards_categories = [0, 1]
            st.session_state._process_cards_next_id = 2

        categories: list[tuple[str, str]] = []
        for cat_id in list(st.session_state._process_cards_categories):
            label_key = f"_pc_label_{cat_id}"
            uids_key = f"_pc_uids_{cat_id}"

            cat_label_col, cat_remove_col = st.columns([5, 1])
            with cat_label_col:
                label = st.text_input(
                    "Category label",
                    key=label_key,
                    placeholder="e.g. i",
                    label_visibility="collapsed",
                )
            with cat_remove_col:
                if st.button("✕", key=f"_pc_remove_{cat_id}", use_container_width=True, help="Remove this category"):
                    st.session_state._process_cards_categories.remove(cat_id)
                    for key in (label_key, uids_key):
                        if key in st.session_state:
                            del st.session_state[key]
                    st.rerun()

            uid_text = st.text_area(
                "UIDs",
                key=uids_key,
                placeholder="e.g. 4, 9, 22.1",
                label_visibility="collapsed",
                height=80,
            )

            if uid_text.strip():
                st.caption(f"{len(parse_uid_list(uid_text))} UID(s)")

            categories.append((label, uid_text))

            st.markdown("")

        if st.button("+ Add Category", use_container_width=True):
            new_id = st.session_state._process_cards_next_id
            st.session_state._process_cards_categories.append(new_id)
            st.session_state._process_cards_next_id = new_id + 1
            st.rerun()

        st.markdown("---")

        # === STEP 4: PROCESS ===
        st.subheader("Step 4: Process")

        can_process = bool(sanitized_column_name) and any(
            label.strip() and text.strip() for label, text in categories
        )

        process_clicked = st.button(
            "Process Cards",
            type="primary",
            use_container_width=True,
            disabled=not can_process,
        )

        if not can_process:
            if not sanitized_column_name:
                st.caption("Enter a sorting activity name.")
            else:
                st.caption("Add at least one category with a label and UIDs.")

        if process_clicked:
            st.session_state._process_cards_generate_params = {
                "index_col": index_col,
                "sub_index_col": sub_index_col,
                "activity_name": activity_name,
                "categories": categories,
            }
            st.rerun()

        st.markdown("")

        if st.button("Back to Main Menu", use_container_width=True):
            _clear_process_cards_state()
            go_back_to_menu()

    # === OUTPUT COLUMN ===
    with output_col:
        st.subheader("Output")

        # Process if triggered
        if "_process_cards_generate_params" in st.session_state:
            params = st.session_state._process_cards_generate_params
            del st.session_state._process_cards_generate_params

            with st.spinner("Processing cards..."):
                result = process_cards_manual(
                    df=df,
                    index_col=params["index_col"],
                    sub_index_col=params["sub_index_col"],
                    activity_name=params["activity_name"],
                    categories=params["categories"],
                )

            st.session_state._process_cards_result = result
            if result.success:
                st.session_state.database = result.df
                st.session_state.database_validated = True
                st.session_state._scroll_to_top = True
            st.rerun()

        # Display result if available
        if "_process_cards_result" in st.session_state:
            result: ProcessCardsResult = st.session_state._process_cards_result

            if result.success:
                categories_n = result.summary["categories"]
                st.success(
                    f"Column '{result.column_name}' added: {result.summary['rows_labeled']:,} row(s) labeled "
                    f"across {categories_n} categor{'y' if categories_n == 1 else 'ies'}, "
                    f"{result.summary['rows_blank']:,} row(s) left blank."
                )

                st.markdown("---")

                btn_col1, btn_col2 = st.columns(2)

                with btn_col1:
                    st.download_button(
                        label="Download Updated Database",
                        data=export_database(result.df),
                        file_name="database_processed.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        type="primary",
                        use_container_width=True,
                    )

                with btn_col2:
                    if st.button("Return to Main Menu", use_container_width=True, key="return_after_process_cards"):
                        del st.session_state._process_cards_result
                        _clear_process_cards_state()
                        go_back_to_menu()

                st.markdown("---")

                st.markdown("**Updated Database Preview:**")
                st.caption("Showing only rows updated by this activity.")
                preview_cols = [c for c in [index_col, sub_index_col, result.column_name] if c]
                updated_rows = result.df[result.df[result.column_name].notna()]
                st.dataframe(updated_rows[preview_cols].head(20), use_container_width=True)

            else:
                st.error(f"**Error:** {result.error}")

                if result.duplicate_uids:
                    st.markdown("**Duplicate UIDs:**")
                    for uid in result.duplicate_uids[:20]:
                        st.text(f"  {uid}")
                    if len(result.duplicate_uids) > 20:
                        st.text(f"  ... and {len(result.duplicate_uids) - 20} more")

                if result.unmatched_uids:
                    st.markdown("**UIDs not found in database:**")
                    for uid in result.unmatched_uids[:20]:
                        st.text(f"  {uid}")
                    if len(result.unmatched_uids) > 20:
                        st.text(f"  ... and {len(result.unmatched_uids) - 20} more")

                st.markdown("---")

                if st.button("Back to Configuration", use_container_width=True):
                    del st.session_state._process_cards_result
                    st.rerun()

        else:
            # Not yet processed - show instructions
            st.info(
                "Configure the index columns, name your sorting activity, add categories with "
                "their UIDs, then click **Process Cards** in the left panel."
            )

            st.markdown("---")

            st.markdown("**About Processing Cards**")
            st.markdown(
                """
                This task records the results of a card-sorting activity back into the database.

                1. **Index Columns** must match what was used to print the cards, so UIDs line up.
                2. **Activity Name** becomes a new database column (spaces become underscores).
                3. **Categories** -- one per pile the cards were sorted into. Each category has a
                   label (the value written into the database) and a list of UIDs (from the
                   bottom-right of each card) sorted into that pile.
                4. **Process** writes the category label onto each matching row's new column.
                   Rows not covered by any category are left blank.
                """
            )

            st.markdown("---")

            st.markdown("**Example:**")
            example_df = pd.DataFrame({
                "index": [4, 9, 15, 22],
                "sub_index": [1, 1, 1, 1],
                "front_p": ["i", "i", "e", None],
            })
            st.dataframe(example_df, use_container_width=True, hide_index=True)
