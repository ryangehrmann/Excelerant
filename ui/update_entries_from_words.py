"""
ui/update_entries_from_words.py
Screen for checking database formatting and updating entries from words.
"""

import pandas as pd
import streamlit as st

from tasks import FORMATTING_REQUIRED_COLUMNS, detect_columns, check_database_formatting, export_database
from ui.navigation import Screen, navigate_to, go_back_to_menu


def screen_update_entries_from_words():
    """Screen for checking database formatting and updating entries from words."""

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

    st.title("Check Database Formatting & Update Entries")
    st.markdown("---")

    # Two-column layout
    config_col, output_col = st.columns([1, 2])

    df = st.session_state.database
    columns = list(df.columns)

    with config_col:
        st.subheader("Column Detection")

        # Detect columns
        detection = detect_columns(df)

        if detection.success:
            st.success("All required columns found!")

            # Show detected columns
            st.markdown("**Detected columns:**")
            for req_col, actual_col in detection.column_mapping.items():
                if req_col == actual_col:
                    st.text(f"  {req_col}")
                else:
                    st.text(f"  {req_col} (from '{actual_col}')")

            if detection.normalized_columns:
                st.info(f"Column names will be normalized to lowercase: {', '.join(detection.normalized_columns)}")

            st.markdown("---")

            # Categorical columns selection
            st.markdown("**Additional Categorical Columns (Optional)**")
            st.caption(
                "If your data has multiple speakers or multiple tokens of the same word list item, "
                "select those columns here. They will be included in uniqueness checks and grouping."
            )

            # Get available columns (excluding required ones)
            available_cat_cols = [col for col in columns if col.lower() not in
                                  [r.lower() for r in FORMATTING_REQUIRED_COLUMNS]]

            categorical_columns = st.multiselect(
                "Select categorical columns",
                options=available_cat_cols,
                default=[],
                help="Columns like 'speaker', 'token', etc.",
                key="cat_cols_detected",
            )

            st.markdown("---")

            # Process button
            process_clicked = st.button(
                "Check Formatting & Update Entries",
                type="primary",
                use_container_width=True,
            )

            if process_clicked:
                st.session_state._formatting_check_params = {
                    "column_mapping": detection.column_mapping,
                    "categorical_columns": categorical_columns if categorical_columns else None,
                }
                st.rerun()

        else:
            st.warning(f"Missing required columns: {', '.join(detection.missing_columns)}")

            st.markdown("**Please map the missing columns:**")

            # Build column mapping with user input for missing columns
            user_mapping = {}

            for req_col in FORMATTING_REQUIRED_COLUMNS:
                if req_col in detection.column_mapping:
                    # Already found
                    actual_col = detection.column_mapping[req_col]
                    if req_col == actual_col:
                        st.text(f"  {req_col} - found")
                    else:
                        st.text(f"  {req_col} - found (as '{actual_col}')")
                    user_mapping[req_col] = actual_col
                else:
                    # Need user to select
                    selected = st.selectbox(
                        f"Select column for '{req_col}'",
                        options=["-none-"] + columns,
                        key=f"col_map_{req_col}",
                    )
                    if selected != "-none-":
                        user_mapping[req_col] = selected

            # Check if all columns are now mapped
            all_mapped = len(user_mapping) == len(FORMATTING_REQUIRED_COLUMNS)

            st.markdown("---")

            # Categorical columns selection
            st.markdown("**Additional Categorical Columns (Optional)**")
            st.caption(
                "If your data has multiple speakers or multiple tokens of the same word list item, "
                "select those columns here. They will be included in uniqueness checks and grouping."
            )

            # Get available columns (excluding required ones and already mapped ones)
            mapped_cols = set(user_mapping.values())
            available_cat_cols = [col for col in columns if col not in mapped_cols and
                                  col.lower() not in [r.lower() for r in FORMATTING_REQUIRED_COLUMNS]]

            categorical_columns = st.multiselect(
                "Select categorical columns",
                options=available_cat_cols,
                default=[],
                help="Columns like 'speaker', 'token', etc.",
                key="cat_cols_manual",
            )

            st.markdown("---")

            process_clicked = st.button(
                "Check Formatting & Update Entries",
                type="primary",
                use_container_width=True,
                disabled=not all_mapped,
            )

            if not all_mapped:
                st.caption("Please select a column for each required field.")

            if process_clicked and all_mapped:
                st.session_state._formatting_check_params = {
                    "column_mapping": user_mapping,
                    "categorical_columns": categorical_columns if categorical_columns else None,
                }
                st.rerun()

        st.markdown("---")

        if st.button("Back to Main Menu", use_container_width=True):
            # Clean up session state
            for key in ["_formatting_check_params", "_formatting_check_result"]:
                if key in st.session_state:
                    del st.session_state[key]
            go_back_to_menu()

    # === OUTPUT COLUMN ===
    with output_col:
        st.subheader("Output")

        # Process if triggered
        if "_formatting_check_params" in st.session_state:
            params = st.session_state._formatting_check_params
            del st.session_state._formatting_check_params

            with st.spinner("Checking database formatting..."):
                result = check_database_formatting(
                    df=df,
                    column_mapping=params["column_mapping"],
                    categorical_columns=params.get("categorical_columns"),
                )

            if result.success:
                st.session_state._formatting_check_result = result
                st.session_state._scroll_to_top = True
                st.session_state.database = result.df
                st.session_state.database_validated = True
                st.rerun()
            else:
                # Store error result for display
                st.session_state._formatting_check_result = result
                st.rerun()

        # Display result if available
        if "_formatting_check_result" in st.session_state:
            result = st.session_state._formatting_check_result

            if result.success:
                st.success("Database formatting validated and entries updated!")

                # Show summary
                cat_cols = result.summary.get('categorical_columns', [])
                cat_cols_text = f"- Categorical columns: {', '.join(cat_cols)}" if cat_cols else ""

                summary_text = f"""
                **Summary:**
                - Total rows: {result.summary.get('total_rows', 'N/A')}
                - Unique indices: {result.summary.get('unique_indices', 'N/A')}
                - Auto-fixes applied: {result.summary.get('auto_fixes_count', 0)}
                """
                if cat_cols_text:
                    summary_text += f"\n                {cat_cols_text}"

                st.markdown(summary_text)

                # Show auto-fixes if any
                if result.auto_fixes_applied:
                    with st.expander("Auto-fixes applied", expanded=False):
                        st.markdown(
                            "The following sub_index sequences were renumbered to start at 1:"
                        )
                        for fix in result.auto_fixes_applied[:20]:
                            st.text(f"  {fix}")
                        if len(result.auto_fixes_applied) > 20:
                            st.text(f"  ... and {len(result.auto_fixes_applied) - 20} more")

                st.markdown("---")

                # Buttons row
                btn_col1, btn_col2 = st.columns(2)

                with btn_col1:
                    # Download updated database
                    st.download_button(
                        label="Download Updated Database",
                        data=export_database(result.df),
                        file_name="database_formatted.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        type="primary",
                        use_container_width=True,
                    )

                with btn_col2:
                    if st.button("Return to Main Menu", use_container_width=True, key="return_after_format"):
                        for key in ["_formatting_check_params", "_formatting_check_result"]:
                            if key in st.session_state:
                                del st.session_state[key]
                        go_back_to_menu()

                st.markdown("---")

                st.markdown("**Updated Database Preview:**")
                # Show key columns: index, sub_index, word, entry_orig, entry, gloss
                preview_cols = []
                col_priority = ['index', 'sub_index', 'word', 'entry_orig', 'entry', 'gloss']
                for col in col_priority:
                    if col in result.df.columns:
                        preview_cols.append(col)

                if preview_cols:
                    st.dataframe(result.df[preview_cols].head(20), use_container_width=True)
                else:
                    st.dataframe(result.df.head(20), use_container_width=True)

            else:
                # Show error
                error = result.error

                st.error(f"**Validation Error:** {error.message}")

                st.markdown("---")

                st.markdown("**Details:**")
                for detail in error.details:
                    st.text(f"  {detail}")

                st.markdown("---")

                st.markdown("**Recommendation:**")
                st.info(error.recommendation)

                st.markdown("---")

                if st.button("Clear Database & Start Over", type="primary", use_container_width=True):
                    # Clean up session state
                    for key in ["_formatting_check_params", "_formatting_check_result"]:
                        if key in st.session_state:
                            del st.session_state[key]
                    st.session_state.database = None
                    st.session_state.database_validated = False
                    st.session_state.database_filename = None
                    st.session_state.database_sheet_name = None
                    st.session_state.selected_task = None
                    navigate_to(Screen.UPLOAD_DATABASE)

        else:
            # Initial state - show instructions
            st.info("Click **Check Formatting & Update Entries** to validate your database and reconstruct entries from words.")

            st.markdown("---")

            st.markdown("**About This Task**")
            st.markdown(
                """
                This task validates your database formatting and reconstructs entries from individual words.

                **Validation checks:**
                - No blank values in index, sub_index, entry, or word columns
                - Index values must be integers
                - Sub_index values must be integers
                - Entry and word values must be strings
                - Each index + sub_index (+ categorical columns) combination must be unique
                - Sub_indices must be sequential (1, 2, 3...) within each group

                **Categorical columns:**
                If your data has multiple speakers or multiple tokens of the same word list item,
                select those columns. They will be included in uniqueness checks and used for
                grouping when reconstructing entries.

                **Auto-fix:**
                If sub_indices are unique but don't start at 1 or have gaps, they will be
                automatically renumbered (e.g., 3, 5, 7 becomes 1, 2, 3).

                **Output:**
                - Original 'entry' column is preserved as 'entry_orig'
                - New 'entry' column is created by joining words in sub_index order per group
                """
            )

            st.markdown("---")

            st.markdown("**Example:**")

            example_before = pd.DataFrame({
                'index': [1, 1, 1, 2, 2],
                'sub_index': [1, 2, 3, 1, 2],
                'word': ['the', 'big', 'dog', 'a', 'cat'],
                'entry': ['the big dog', 'the big dog', 'the big dog', 'a cat', 'a cat'],
                'gloss': ['animal', 'animal', 'animal', 'animal', 'animal'],
            })
            st.markdown("**Before:**")
            st.dataframe(example_before, use_container_width=True, hide_index=True)

            example_after = pd.DataFrame({
                'index': [1, 1, 1, 2, 2],
                'sub_index': [1, 2, 3, 1, 2],
                'word': ['the', 'big', 'dog', 'a', 'cat'],
                'entry_orig': ['the big dog', 'the big dog', 'the big dog', 'a cat', 'a cat'],
                'entry': ['the big dog', 'the big dog', 'the big dog', 'a cat', 'a cat'],
                'gloss': ['animal', 'animal', 'animal', 'animal', 'animal'],
            })
            st.markdown("**After (entry reconstructed from words):**")
            st.dataframe(example_after[['index', 'sub_index', 'word', 'entry_orig', 'entry']], use_container_width=True, hide_index=True)
