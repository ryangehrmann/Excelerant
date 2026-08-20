"""
ui/generate_cards.py
Screen for exporting a printable card-sorting activity (Orthography Development).
"""

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from tasks import (
    CardBuildResult,
    get_column_filter_options,
    filter_dataframe,
    sort_dataframe,
    build_cards,
    generate_cards_html,
    build_sort_activity_filters,
    build_sort_activity_json,
)
from ui.navigation import go_back_to_menu


def _render_filter_and_card_content_config(df, columns, key_prefix: str, filter_epoch_key: str):
    """Render the "Filter Database" + "Card Content" config steps shared by
    Generate Cards and Sort Cards' "New Sort" flow.

    key_prefix namespaces widget keys so the two screens' instances of
    this config don't collide; filter_epoch_key is the caller's own
    session-state key for resetting filters via "Clear Filters".

    Returns (filtered_df, index_col, sub_index_col, line_columns, sort_by_col, selected_filters).
    """
    st.subheader("Step 1: Filter Database (Optional)")
    st.caption("Narrow down which rows are available before choosing card content. Leave blank to include everything.")

    if filter_epoch_key not in st.session_state:
        st.session_state[filter_epoch_key] = 0
    epoch = st.session_state[filter_epoch_key]

    filter_columns = st.multiselect(
        "Filter by columns",
        options=columns,
        default=[],
        key=f"_{key_prefix}_filter_cols_{epoch}",
    )

    selected_filters = {}
    for col in filter_columns:
        col_options = get_column_filter_options(df, col)
        selected_filters[col] = st.multiselect(
            f"Values to include — '{col}'",
            options=col_options,
            default=col_options,
            key=f"_{key_prefix}_filter_val_{epoch}_{col}",
        )

    if st.button(
        "Clear Filters",
        use_container_width=True,
        disabled=not filter_columns,
        key=f"_{key_prefix}_clear_filters",
    ):
        st.session_state[filter_epoch_key] = epoch + 1
        st.rerun()

    filtered_df = filter_dataframe(df, selected_filters)

    st.markdown(f"**{len(filtered_df):,}** of **{len(df):,}** rows match your filters.")

    st.markdown("---")

    st.subheader("Step 2: Card Content")

    index_default = columns.index("index") if "index" in columns else 0
    index_col = st.selectbox(
        "Index column",
        options=columns,
        index=index_default,
        key=f"_{key_prefix}_index_col",
    )

    sub_index_options = ["-none-"] + columns
    sub_index_default = sub_index_options.index("sub_index") if "sub_index" in columns else 0
    sub_index_choice = st.selectbox(
        "Sub-index column (optional)",
        options=sub_index_options,
        index=sub_index_default,
        key=f"_{key_prefix}_sub_index_col",
        help="If your entries have been exploded into words, select 'sub_index' so each card gets an 'index.sub_index' label.",
    )
    sub_index_col = None if sub_index_choice == "-none-" else sub_index_choice

    st.markdown("**Card lines** (top to bottom)")

    line_options = ["-none-"] + columns
    line_1 = st.selectbox("Line 1 (large)", options=line_options, index=0, key=f"_{key_prefix}_line_1")
    line_2 = st.selectbox("Line 2", options=line_options, index=0, key=f"_{key_prefix}_line_2")
    line_3 = st.selectbox("Line 3", options=line_options, index=0, key=f"_{key_prefix}_line_3")

    line_columns = [c for c in [line_1, line_2, line_3] if c != "-none-"]

    st.markdown("")

    sort_options = ["-none-"] + columns
    sort_key = f"_{key_prefix}_sort_by"
    if sort_key in st.session_state and st.session_state[sort_key] not in sort_options:
        st.session_state[sort_key] = "-none-"
    sort_choice = st.selectbox(
        "Sort by",
        options=sort_options,
        index=0,
        key=sort_key,
        help="Sort cards by any database column -- handy for spotting near-duplicate entries, since they'll land next to each other. Doesn't need to be one of the card lines above.",
    )
    sort_by_col = None if sort_choice == "-none-" else sort_choice

    return filtered_df, index_col, sub_index_col, line_columns, sort_by_col, selected_filters


def screen_generate_cards():
    """Screen for exporting a printable card-sorting activity (Orthography Development)."""

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

    st.title("Generate Cards")
    st.markdown("---")

    # Two-column layout
    config_col, output_col = st.columns([1, 2])

    df = st.session_state.database
    columns = list(df.columns)

    with config_col:
        filtered_df, index_col, sub_index_col, line_columns, sort_by_col, selected_filters = (
            _render_filter_and_card_content_config(
                df, columns, key_prefix="sort", filter_epoch_key="_generate_cards_filter_epoch"
            )
        )

        st.markdown("---")

        # === STEP 3: EXPORT ===
        st.subheader("Step 3: Export")

        file_name = st.text_input(
            "Export name",
            value="sorting_activity",
            key="_sort_file_name",
            help="Used as the HTML deck's filename, and (for the JSON) as the resulting sorting activity's name.",
        )

        can_generate = len(filtered_df) > 0 and len(line_columns) > 0

        generate_clicked = st.button(
            "Generate Cards",
            type="primary",
            use_container_width=True,
            disabled=not can_generate,
        )

        if not can_generate:
            if len(filtered_df) == 0:
                st.caption("No rows match your current filters.")
            else:
                st.caption("Select at least one card line above.")

        if generate_clicked:
            st.session_state._generate_cards_generate_params = {
                "filtered_df": filtered_df,
                "index_col": index_col,
                "sub_index_col": sub_index_col,
                "line_columns": line_columns,
                "sort_by_col": sort_by_col,
                "file_name": file_name,
                "selected_filters": selected_filters,
            }
            st.rerun()

        st.markdown("")

        if st.button("Back to Main Menu", use_container_width=True):
            for key in ["_generate_cards_generate_params", "_generate_cards_export_result"]:
                if key in st.session_state:
                    del st.session_state[key]
            go_back_to_menu()

    # === OUTPUT COLUMN ===
    with output_col:
        st.subheader("Output")

        # Process generation if triggered
        if "_generate_cards_generate_params" in st.session_state:
            params = st.session_state._generate_cards_generate_params
            del st.session_state._generate_cards_generate_params

            with st.spinner("Building cards..."):
                build_result = build_cards(
                    df=params["filtered_df"],
                    index_col=params["index_col"],
                    sub_index_col=params["sub_index_col"],
                    line_columns=params["line_columns"],
                    sort_by_col=params["sort_by_col"],
                )

                if build_result.success:
                    html = generate_cards_html(build_result.cards)
                    narrowing_filters = build_sort_activity_filters(
                        df=df,
                        selected_filters=params["selected_filters"],
                    )
                    json_bytes = build_sort_activity_json(
                        activity_name=params["file_name"],
                        index_col=params["index_col"],
                        sub_index_col=params["sub_index_col"],
                        filters=narrowing_filters,
                        line_columns=params["line_columns"],
                    )
                else:
                    html = None
                    json_bytes = None

            st.session_state._generate_cards_export_result = {
                "build_result": build_result,
                "html": html,
                "json_bytes": json_bytes,
                "file_name": params["file_name"],
            }
            st.session_state._scroll_to_top = True
            st.rerun()

        if "_generate_cards_export_result" in st.session_state:
            export = st.session_state._generate_cards_export_result
            build_result: CardBuildResult = export["build_result"]

            if build_result.success:
                st.success(
                    f"Cards generated: {build_result.included_rows:,} card(s) "
                    f"from {build_result.total_rows:,} row(s)."
                )

                st.markdown("---")

                base_name = export["file_name"].strip() or "sorting_activity"
                html_name = base_name if base_name.endswith(".html") else base_name + ".html"
                json_name = base_name if base_name.endswith(".json") else base_name + ".json"

                btn_col1, btn_col2 = st.columns(2)

                with btn_col1:
                    st.download_button(
                        label=f"Download {html_name}",
                        data=export["html"].encode("utf-8"),
                        file_name=html_name,
                        mime="text/html",
                        type="primary",
                        use_container_width=True,
                        help="Printable HTML card deck for physical sorting.",
                    )

                with btn_col2:
                    st.download_button(
                        label=f"Download {json_name}",
                        data=export["json_bytes"],
                        file_name=json_name,
                        mime="application/json",
                        type="primary",
                        use_container_width=True,
                        help="Prepared activity file for digital/asynchronous sorting in Sort Cards.",
                    )

                if st.button("Return to Main Menu", use_container_width=True, key="return_after_sorting"):
                    del st.session_state._generate_cards_export_result
                    go_back_to_menu()

                st.markdown("---")

                st.markdown("**Preview (HTML deck):**")
                components.html(export["html"], height=500, scrolling=True)

            else:
                st.error(f"**Error:** {build_result.error}")

                if build_result.duplicate_indices:
                    st.markdown("**Duplicate values:**")
                    for dup in build_result.duplicate_indices[:20]:
                        st.text(f"  {dup}")
                    if len(build_result.duplicate_indices) > 20:
                        st.text(f"  ... and {len(build_result.duplicate_indices) - 20} more")

                st.markdown("---")

                if st.button("Back to Configuration", use_container_width=True):
                    del st.session_state._generate_cards_export_result
                    st.rerun()

        else:
            # Not yet generated - show live filtered (and sorted) preview + instructions
            preview_df = sort_dataframe(filtered_df, sort_by_col)

            st.markdown("**Filtered Database Preview**")
            st.markdown(f"**{len(filtered_df):,}** of **{len(df):,}** rows match your current filters.")
            if sort_by_col:
                st.caption(f"Sorted by '{sort_by_col}'.")
            st.dataframe(preview_df.head(15), use_container_width=True)

            st.markdown("---")

            st.markdown("**About Generating Cards**")
            st.markdown(
                """
                This task generates cards for orthography-development card-sorting activities
                with speakers, for either physical or digital sorting.

                1. **Filter** (optional) narrows down which rows are eligible.
                2. **Card lines** pick up to 3 columns to display on each card (e.g. a native
                   script gloss, an English gloss, and a phonetic transcription).
                3. **Export** generates a Letter-size HTML deck (10 cards per page, with
                   automatic Lao-script and IPA font handling) for physical sorting, and a
                   prepared-activity JSON file to hand off for digital/asynchronous sorting in
                   Sort Cards.
                """
            )

            st.markdown("---")

            st.markdown("**Example card content:**")
            example_card = pd.DataFrame({
                "index": [1],
                "gloss_lao": ["ສຸຂ"],
                "gloss_eng": ["happiness"],
                "phonetic": ["/suk/"],
            })
            st.dataframe(example_card, use_container_width=True, hide_index=True)
