"""
ui/explode_entries.py
Screen for splitting multi-word entries into one-word-per-row.
"""

import pandas as pd
import streamlit as st

from tasks import explode_entries, export_database
from ui.navigation import Screen, navigate_to, go_back_to_menu


def screen_explode_entries():
    """Screen for splitting multi-word entries into one-word-per-row."""

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

    st.title("Explode Entries")
    st.markdown("---")

    # Two-column layout
    config_col, output_col = st.columns([1, 2])

    df = st.session_state.database
    columns = list(df.columns)

    with config_col:
        st.subheader("Configuration")

        # Auto-detect entry column (case-insensitive)
        entry_col = None
        for col in columns:
            if col.lower() == 'entry':
                entry_col = col
                break

        if entry_col:
            st.success(f"Entry column detected: **{entry_col}**")
        else:
            entry_col = st.selectbox(
                "Select entry column",
                options=columns,
                help="Column containing multi-word transcriptions to split",
            )

        # Auto-detect gloss column
        gloss_col = None
        for col in columns:
            if col.lower() == 'gloss':
                gloss_col = col
                break

        if gloss_col:
            st.markdown(f"Gloss column detected: **{gloss_col}**")
        else:
            gloss_col = st.selectbox(
                "Select gloss column",
                options=["-none-"] + columns,
                help="Column containing glosses/meanings",
            )
            if gloss_col == "-none-":
                gloss_col = None

        st.markdown("---")

        # Categorical columns (optional)
        st.markdown("**Categorical Columns (Optional)**")
        st.caption(
            "If your data has multiple speakers or tokens, "
            "select those columns so grouping works correctly."
        )

        # Exclude standard columns from categorical options
        exclude_cols = {'index', 'entry', 'gloss', 'sub_index', 'word'}
        available_cat_cols = [c for c in columns if c.lower() not in exclude_cols]

        categorical_columns = st.multiselect(
            "Select categorical columns",
            options=available_cat_cols,
            default=[],
            help="Columns like 'speaker', 'token', etc.",
        )

        st.markdown("---")

        # Process button
        process_clicked = st.button(
            "Explode Entries",
            type="primary",
            use_container_width=True,
        )

        if process_clicked:
            st.session_state._explode_params = {
                "entry_col": entry_col,
                "gloss_col": gloss_col,
                "categorical_columns": categorical_columns if categorical_columns else None,
            }
            st.rerun()

        st.markdown("---")

        if st.button("Back to Main Menu", use_container_width=True):
            for key in ["_explode_params", "_explode_result"]:
                if key in st.session_state:
                    del st.session_state[key]
            go_back_to_menu()

    # === OUTPUT COLUMN ===
    with output_col:
        st.subheader("Output")

        # Process if triggered
        if "_explode_params" in st.session_state:
            params = st.session_state._explode_params
            del st.session_state._explode_params

            with st.spinner("Exploding entries..."):
                result = explode_entries(
                    df=df,
                    entry_col=params["entry_col"],
                    gloss_col=params["gloss_col"],
                    categorical_columns=params["categorical_columns"],
                )

            if result.success:
                st.session_state._explode_result = result
                st.session_state._scroll_to_top = True
                st.session_state.database = result.df
                st.session_state.database_validated = True
                st.rerun()
            else:
                st.error(f"**Error:** {result.error}")

                st.markdown("---")

                if st.button("Clear Database & Start Over", type="primary", use_container_width=True):
                    for key in ["_explode_params", "_explode_result"]:
                        if key in st.session_state:
                            del st.session_state[key]
                    st.session_state.database = None
                    st.session_state.database_validated = False
                    st.session_state.database_filename = None
                    st.session_state.database_sheet_name = None
                    st.session_state.selected_task = None
                    navigate_to(Screen.UPLOAD_DATABASE)

        # Display result if available
        if "_explode_result" in st.session_state:
            result = st.session_state._explode_result

            st.success("Entries exploded successfully!")

            st.markdown(f"""
            **Summary:**
            - Entries processed: {result.summary.get('entries_processed', 'N/A')}
            - Total words created: {result.summary.get('words_created', 'N/A')}
            - Rows before: {result.summary.get('rows_before', 'N/A')}
            - Rows after: {result.summary.get('rows_after', 'N/A')}
            """)

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
                    st.markdown(
                        "Original values preserved in the `entry_orig` column."
                    )

            # Note about preserved columns
            if 'word_old' in result.df.columns:
                st.info("Existing 'word' column was preserved as 'word_old'.")
            if 'sub_index_old' in result.df.columns:
                st.info("Existing 'sub_index' column was preserved as 'sub_index_old'.")

            st.markdown("---")

            # Buttons row
            btn_col1, btn_col2 = st.columns(2)

            with btn_col1:
                st.download_button(
                    label="Download Updated Database",
                    data=export_database(result.df),
                    file_name="database_exploded.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    type="primary",
                    use_container_width=True,
                )

            with btn_col2:
                if st.button("Return to Main Menu", use_container_width=True, key="return_after_explode"):
                    for key in ["_explode_params", "_explode_result"]:
                        if key in st.session_state:
                            del st.session_state[key]
                    go_back_to_menu()

            st.markdown("---")

            st.markdown("**Updated Database Preview:**")
            preview_cols = []
            for col in ['index', 'sub_index', 'entry', 'word', 'gloss']:
                if col in result.df.columns:
                    preview_cols.append(col)

            if preview_cols:
                st.dataframe(result.df[preview_cols].head(20), use_container_width=True)
            else:
                st.dataframe(result.df.head(20), use_container_width=True)

        else:
            # Initial state - show instructions
            st.info(
                "Configure your column mappings in the left panel, "
                "then click **Explode Entries** to split multi-word entries."
            )

            st.markdown("---")

            st.markdown("**About This Task**")
            st.markdown(
                """
                This task splits multi-word entries into one-word-per-row,
                adding two new columns:

                - **sub_index**: The position of each word within its entry (1, 2, 3...)
                - **word**: The individual word from the entry

                Before splitting, entry transcriptions are cleaned:
                - Unicode whitespace is normalized
                - Punctuation is removed
                - Multiple spaces are collapsed

                If your database already has `word` or `sub_index` columns,
                they will be preserved as `word_old` and `sub_index_old`.
                """
            )

            st.markdown("---")

            st.markdown("**Example (before):**")
            example_before = pd.DataFrame({
                'index': [1, 2, 3],
                'entry': ['ma pa', 'ka', 'ta na sa'],
                'gloss': ['parents', 'house', 'three words'],
            })
            st.dataframe(example_before, use_container_width=True, hide_index=True)

            st.markdown("**Example (after):**")
            example_after = pd.DataFrame({
                'index': [1, 1, 2, 3, 3, 3],
                'sub_index': [1, 2, 1, 1, 2, 3],
                'entry': ['ma pa', 'ma pa', 'ka', 'ta na sa', 'ta na sa', 'ta na sa'],
                'word': ['ma', 'pa', 'ka', 'ta', 'na', 'sa'],
                'gloss': ['parents', 'parents', 'house', 'three words', 'three words', 'three words'],
            })
            st.dataframe(example_after, use_container_width=True, hide_index=True)
