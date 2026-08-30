"""
ui/upload_database.py
Shared lexical-database upload/validation screen.
"""

import streamlit as st

from tasks import (
    REQUIRED_COLUMNS,
    COLLECT_REQUIRED_COLUMNS,
    find_valid_sheets,
    load_sheet,
    validate_database,
)
from ui.navigation import Screen, navigate_to, proceed_after_upload


def screen_upload_database():
    """Database upload and validation screen."""

    # The Collect Lexical Data flow runs before transcription, so it only needs
    # index + gloss; every other mode needs the full index/entry/gloss database.
    required_columns = (
        COLLECT_REQUIRED_COLUMNS
        if st.session_state.get("analysis_mode") == "collect"
        else REQUIRED_COLUMNS
    )

    # Add vertical divider CSS for this screen
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

    st.title("Upload Lexical Database")
    st.markdown("---")

    # Two-column layout (1/3 left, 2/3 right) - matching main menu
    config_col, right_col = st.columns([1, 2])

    with config_col:
        st.subheader("Upload")

        if st.session_state.get("analysis_mode") in ("phonological", "collect", "manage"):
            if st.button("Load an Example Database", use_container_width=True):
                example_path = "example_data/example_data.xlsx"
                valid_sheets = find_valid_sheets(example_path, required_columns)

                if not valid_sheets:
                    st.error("Could not find a valid sheet in the example database.")
                else:
                    result = load_sheet(example_path, valid_sheets[0], required_columns)

                    if not result.success:
                        st.error(f"Error loading example database: {result.error}")
                    else:
                        validation = validate_database(result.df, required_columns)

                        if not validation.valid:
                            st.error("The example database failed validation.")
                        else:
                            st.session_state.database = result.df
                            st.session_state.database_validated = True
                            st.session_state.database_filename = "example_data.xlsx"
                            st.session_state.database_sheet_name = valid_sheets[0]

                            st.success("Example database loaded!")
                            proceed_after_upload()

            st.markdown("*— or upload your own —*")

        uploaded_file = st.file_uploader(
            "Select your spreadsheet file",
            type=["xlsx", "xls", "ods"],
            help="Supported formats: .xlsx, .xls, .ods"
        )

        if uploaded_file is not None:
            # Find valid sheets
            valid_sheets = find_valid_sheets(uploaded_file, required_columns)

            if len(valid_sheets) == 0:
                required_list = ", ".join(f"`{c}`" for c in required_columns)
                st.error(
                    "**No valid sheets found.**\n\n"
                    "Your spreadsheet must have at least one sheet with these "
                    f"columns: {required_list}\n\n"
                    "Please edit your file and re-upload."
                )

            elif len(valid_sheets) == 1:
                # Auto-select the only valid sheet
                sheet_name = valid_sheets[0]
                st.success(f"Found valid sheet: **{sheet_name}**")

                result = load_sheet(uploaded_file, sheet_name, required_columns)

                if not result.success:
                    st.error(f"Error loading sheet: {result.error}")
                else:
                    df = result.df
                    st.session_state._temp_df = df
                    st.session_state._temp_filename = uploaded_file.name
                    st.session_state._temp_sheet = sheet_name

                    st.markdown(f"**Rows:** {len(df):,} · **Columns:** {len(df.columns)}")

                    # Validate the data
                    validation = validate_database(df, required_columns)

                    if not validation.valid:
                        st.error("**Validation errors found.**")

                        for col_name, issues in validation.errors.items():
                            with st.expander(f"Issues in '{col_name}' column ({len(issues)} errors)", expanded=True):
                                if col_name == "index":
                                    st.markdown("All values in the `index` column must be integers.")
                                else:
                                    st.markdown(f"All values in the `{col_name}` column must be non-empty strings.")

                                st.markdown("**Problematic rows:**")
                                for issue in issues[:20]:  # Show max 20
                                    st.text(f"  {issue}")
                                if len(issues) > 20:
                                    st.text(f"  ... and {len(issues) - 20} more")

                        st.markdown("---")
                        st.info("Please fix these issues in your Excel file, then upload the corrected file above.")
                    else:
                        st.success("Data validation passed")

                        st.markdown("---")

                        if st.button("Load Database", type="primary", use_container_width=True):
                            st.session_state.database = df
                            st.session_state.database_validated = True
                            st.session_state.database_filename = uploaded_file.name
                            st.session_state.database_sheet_name = sheet_name

                            # Clean up temp state
                            for key in ["_temp_df", "_temp_filename", "_temp_sheet"]:
                                if key in st.session_state:
                                    del st.session_state[key]

                            st.success("Database loaded!")
                            proceed_after_upload()

            else:
                # Multiple valid sheets - user must choose
                st.info(f"Found {len(valid_sheets)} sheets with required columns. Please select one:")

                # Add placeholder option
                sheet_options = ["- Select a sheet -"] + valid_sheets

                selected_sheet = st.selectbox(
                    "Select sheet",
                    options=sheet_options,
                    index=0,
                    help="Choose the sheet containing your lexical data"
                )

                # Only validate if user has selected a real sheet (not placeholder)
                if selected_sheet != "- Select a sheet -":
                    result = load_sheet(uploaded_file, selected_sheet, required_columns)

                    if not result.success:
                        st.error(f"Error loading sheet: {result.error}")
                    else:
                        df = result.df
                        st.session_state._temp_df = df
                        st.session_state._temp_filename = uploaded_file.name
                        st.session_state._temp_sheet = selected_sheet

                        st.markdown(f"**Rows:** {len(df):,} · **Columns:** {len(df.columns)}")

                        # Validate the data
                        validation = validate_database(df, required_columns)

                        if not validation.valid:
                            st.error("**Validation errors found.**")

                            for col_name, issues in validation.errors.items():
                                with st.expander(f"Issues in '{col_name}' column ({len(issues)} errors)", expanded=True):
                                    if col_name == "index":
                                        st.markdown("All values in the `index` column must be integers.")
                                    else:
                                        st.markdown(f"All values in the `{col_name}` column must be non-empty strings.")

                                    st.markdown("**Problematic rows:**")
                                    for issue in issues[:20]:  # Show max 20
                                        st.text(f"  {issue}")
                                    if len(issues) > 20:
                                        st.text(f"  ... and {len(issues) - 20} more")

                            st.markdown("---")
                            st.info("Please fix these issues in your Excel file, then upload the corrected file above.")
                        else:
                            st.success("Data validation passed")

                            st.markdown("---")

                            if st.button("Load Database", type="primary", use_container_width=True):
                                st.session_state.database = df
                                st.session_state.database_validated = True
                                st.session_state.database_filename = uploaded_file.name
                                st.session_state.database_sheet_name = selected_sheet

                                # Clean up temp state
                                for key in ["_temp_df", "_temp_filename", "_temp_sheet"]:
                                    if key in st.session_state:
                                        del st.session_state[key]

                                st.success("Database loaded!")
                                proceed_after_upload()

        st.markdown("---")

        if st.button("Back to Welcome"):
            navigate_to(Screen.WELCOME)

    with right_col:
        st.subheader("Information")

        if uploaded_file is None:
            header_row = " | ".join(required_columns)
            divider_row = " | ".join("---" for _ in required_columns)
            example_row1 = " | ".join(
                {"index": "1", "entry": "word1", "gloss": "meaning1"}.get(c, "…")
                for c in required_columns
            )
            example_row2 = " | ".join(
                {"index": "2", "entry": "word2", "gloss": "meaning2"}.get(c, "…")
                for c in required_columns
            )
            st.info(
                "**Required Format:**\n\n"
                "Your spreadsheet must contain at least one sheet with these columns:\n\n"
                f"| {header_row} |\n| {divider_row} |\n"
                f"| {example_row1} |\n| {example_row2} |\n\n"
                "Additional columns are allowed and will be preserved.\n\n"
                "**Supported file types:**\n"
                "- Excel (.xlsx, .xls)\n"
                "- OpenDocument (.ods)"
            )
        elif "_temp_df" in st.session_state:
            df = st.session_state._temp_df

            st.markdown(f"**File:** `{st.session_state._temp_filename}`")
            st.markdown(f"**Sheet:** `{st.session_state._temp_sheet}`")

            st.markdown("---")

            with st.expander("Columns", expanded=False):
                for col in df.columns:
                    marker = "*" if col in required_columns else "-"
                    st.text(f"{marker} {col}")

            with st.expander("Data Preview", expanded=True):
                st.dataframe(df.head(10), use_container_width=True, height=300)
