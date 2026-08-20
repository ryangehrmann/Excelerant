"""
ui/create_data_collection_script.py
Screen for creating SpeechRecorder data collection scripts.
"""

import base64

import streamlit as st
import streamlit.components.v1 as components

from tasks import generate_script
from ui.navigation import Screen, navigate_to, go_back_to_menu


def screen_create_data_collection_script():
    """Screen for creating SpeechRecorder data collection scripts."""

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

    st.title("Create Data Collection Script")
    st.markdown("---")

    # Two-column layout
    config_col, output_col = st.columns([1, 2])

    df = st.session_state.database
    columns = list(df.columns)

    # Build column options with "-none-" for optional fields
    optional_columns = ["-none-"] + columns

    with config_col:
        st.subheader("Column Mapping")

        # Required columns
        st.markdown("**Required**")

        # Index column - default to "index"
        index_default = columns.index("index") if "index" in columns else 0
        index_col = st.selectbox(
            "Index column",
            options=columns,
            index=index_default,
            help="Column containing unique index numbers for each entry",
        )

        # Primary gloss column - default to "gloss"
        gloss_default = columns.index("gloss") if "gloss" in columns else 0
        primary_gloss_col = st.selectbox(
            "Primary gloss column",
            options=columns,
            index=gloss_default,
            help="Column containing the main gloss/meaning shown in prompts",
        )

        st.markdown("")
        st.markdown("**Optional**")

        # Secondary gloss column
        secondary_gloss_col = st.selectbox(
            "Secondary gloss column",
            options=optional_columns,
            index=0,
            help="Additional gloss information (e.g., vernacular gloss)",
        )

        # Extra column
        extra_col = st.selectbox(
            "Extra information column",
            options=optional_columns,
            index=0,
            help="Any additional information to show in prompts",
        )

        st.markdown("---")
        st.subheader("Token Repetition")

        st.markdown(
            "How many times should each item be recorded? "
            "Multiple tokens allow for repetition analysis."
        )

        num_tokens = st.number_input(
            "Number of tokens",
            min_value=1,
            max_value=9,
            value=1,
            step=1,
            format="%d",
        )

        st.markdown("---")
        st.subheader("Sentence Frames")

        using_frames = st.selectbox(
            "Use sentence frames?",
            options=["No", "Yes"],
            index=0,
            help="Include a carrier sentence/frame in prompts",
        )

        frame_col = None
        tokens_in_frame = []

        if using_frames == "Yes":
            frame_col = st.selectbox(
                "Frame column",
                options=columns,
                index=0,
                help="Column containing the sentence frame",
            )

            if num_tokens > 1:
                all_in_frame = st.selectbox(
                    "Apply frame to all tokens?",
                    options=["Yes", "No"],
                    index=0,
                )

                if all_in_frame == "Yes":
                    tokens_in_frame = list(range(1, num_tokens + 1))
                else:
                    tokens_in_frame = st.multiselect(
                        "Select which tokens use the frame",
                        options=list(range(1, num_tokens + 1)),
                        default=[1],
                    )
            else:
                tokens_in_frame = [1]

        st.markdown("---")

        generate_clicked = st.button(
            "Generate Script",
            type="primary",
            use_container_width=True,
        )

        st.markdown("")

        if st.button("Back to Main Menu", use_container_width=True):
            go_back_to_menu()

    with output_col:
        st.subheader("Output")

        if generate_clicked:
            # Convert "-none-" selections to None
            sec_gloss = None if secondary_gloss_col == "-none-" else secondary_gloss_col
            extra = None if extra_col == "-none-" else extra_col
            frame = frame_col if using_frames == "Yes" else None

            with st.spinner("Generating XML script..."):
                result = generate_script(
                    df=df,
                    index_col=index_col,
                    primary_gloss_col=primary_gloss_col,
                    secondary_gloss_col=sec_gloss,
                    frame_col=frame,
                    extra_col=extra,
                    num_tokens=num_tokens,
                    tokens_in_frame=tokens_in_frame,
                )

            if not result.success:
                st.error(f"**Error:** {result.error}")

                st.markdown("---")

                if st.button("Clear Database & Start Over", type="primary", use_container_width=True):
                    if "_generated_script" in st.session_state:
                        del st.session_state._generated_script
                    st.session_state.database = None
                    st.session_state.database_validated = False
                    st.session_state.database_filename = None
                    st.session_state.database_sheet_name = None
                    st.session_state.selected_task = None
                    navigate_to(Screen.UPLOAD_DATABASE)
            else:
                # Store result in session state and rerun to scroll to top
                st.session_state._generated_script = result.script
                st.session_state._scroll_to_top = True
                st.rerun()

        # Display script if available
        if "_generated_script" in st.session_state and st.session_state._generated_script:
            st.success("Script generated successfully!")

            st.markdown(
                """
                **Instructions:**

                1. Click **Copy to Clipboard** below
                2. Open [SpeechRecorder](https://www.bas.uni-muenchen.de/Bas/software/speechrecorder/)
                3. Open your project or start a new one
                4. Go to **Script > Edit Script XML Source**
                5. Delete existing content
                6. Paste the code
                7. Press OK
                8. You're ready to record!

                *Note: Large scripts may cause SpeechRecorder to pause briefly while loading.*
                """
            )

            st.markdown("")

            # Buttons row: Copy to Clipboard (green) | Return to Main Menu
            btn_col1, btn_col2 = st.columns(2)

            with btn_col1:
                # Encode script as base64 to avoid escaping issues
                script_b64 = base64.b64encode(
                    st.session_state._generated_script.encode('utf-8')
                ).decode('utf-8')

                components.html(
                    f"""
                    <script>
                    function copyScript() {{
                        const text = atob("{script_b64}");
                        navigator.clipboard.writeText(text).then(function() {{
                            document.getElementById('copyBtn').innerText = 'Copied!';
                            document.getElementById('copyBtn').style.backgroundColor = '#1B5E20';
                            setTimeout(function() {{
                                document.getElementById('copyBtn').innerText = 'Copy XML Script to Clipboard';
                                document.getElementById('copyBtn').style.backgroundColor = '#2E7D32';
                            }}, 2000);
                        }});
                    }}
                    </script>
                    <button id="copyBtn" onclick="copyScript()" style="
                        background-color: #2E7D32;
                        color: white;
                        border: none;
                        border-radius: 0.5rem;
                        padding: 0.6rem 1rem;
                        font-size: 16px;
                        font-weight: 500;
                        cursor: pointer;
                        width: 100%;
                    ">Copy XML Script to Clipboard</button>
                    """,
                    height=45,
                )

            with btn_col2:
                if st.button("Return to Main Menu", use_container_width=True):
                    # Clear the generated script when returning
                    if "_generated_script" in st.session_state:
                        del st.session_state._generated_script
                    go_back_to_menu()

            st.markdown("---")

            st.markdown("**Generated XML:**")
            st.code(st.session_state._generated_script, language="xml")
        else:
            st.info(
                "Configure your column mappings and settings in the left panel, "
                "then click **Generate Script** to create your XML."
            )

            st.markdown("---")

            st.markdown("**About SpeechRecorder Scripts**")
            st.markdown(
                """
                This task generates XML scripts for
                [SpeechRecorder](http://www.speechrecorder.org/),
                a tool for collecting speech recordings.

                The script will contain prompts for each entry in your database,
                showing:
                - Primary gloss (the main meaning/translation)
                - Index number with optional secondary gloss
                - Sentence frame (if configured)
                - Extra information (if configured)

                Each prompt element is separated by a visual divider (`---`).
                """
            )
