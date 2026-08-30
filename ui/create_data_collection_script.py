"""
ui/create_data_collection_script.py
Screen for creating SpeechRecorder data collection scripts.
"""

import base64

import streamlit as st
import streamlit.components.v1 as components

from tasks import generate_script
from ui.navigation import Screen, navigate_to, go_back_to_menu


SPEECHRECORDER_INSTRUCTIONS = """
**Loading the script into SpeechRecorder:**

1. Click **Copy XML Script to Clipboard** (or use **Download XML Script**)
2. Open [SpeechRecorder](https://www.bas.uni-muenchen.de/Bas/software/speechrecorder/)
3. Open your project or start a new one
4. Go to **Script > Edit Script XML Source**
5. Delete existing content
6. Paste the code (or open the downloaded file)
7. Press OK
8. You're ready to record!

*Note: Large scripts may cause SpeechRecorder to pause briefly while loading.*
"""


def render_copy_to_clipboard_button(text: str, *, key: str):
    """A green 'Copy XML Script to Clipboard' button (via an HTML component).

    `key` must be unique per rendered button on a page - it namespaces the
    element ids in the injected script.
    """
    key = "".join(c if c.isalnum() else "_" for c in key)
    text_b64 = base64.b64encode(text.encode("utf-8")).decode("ascii")
    btn_id = f"copyBtn_{key}"
    components.html(
        f"""
        <script>
        function copyScript_{key}() {{
            // atob() yields one char per byte; decode those bytes back through
            // UTF-8 so non-ASCII scripts (e.g. Lao) reach the clipboard intact.
            const bytes = Uint8Array.from(atob("{text_b64}"), c => c.charCodeAt(0));
            const text = new TextDecoder("utf-8").decode(bytes);
            navigator.clipboard.writeText(text).then(function() {{
                const b = document.getElementById('{btn_id}');
                b.innerText = 'Copied!';
                b.style.backgroundColor = '#1B5E20';
                setTimeout(function() {{
                    b.innerText = 'Copy XML Script to Clipboard';
                    b.style.backgroundColor = '#2E7D32';
                }}, 2000);
            }});
        }}
        </script>
        <button id="{btn_id}" onclick="copyScript_{key}()" style="
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


def render_script_output(script: str, *, filename: str, key: str):
    """Shared 'here is your SpeechRecorder XML' block: instructions, a
    copy/download row, and the XML preview. Callers add their own nav buttons."""
    st.markdown(SPEECHRECORDER_INSTRUCTIONS)
    st.markdown("")

    copy_col, dl_col = st.columns(2)
    with copy_col:
        render_copy_to_clipboard_button(script, key=key)
    with dl_col:
        st.download_button(
            "Download XML Script",
            data=script.encode("utf-8"),
            file_name=filename,
            mime="application/xml",
            use_container_width=True,
            key=f"dl_{key}",
        )

    st.markdown("---")
    st.markdown("**Generated XML:**")
    st.code(script, language="xml")


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
            "How many **separate recording files** should each item get? "
            "Leave this at **1** if your participant will just say each word "
            "several times within one recording. Raise it only when you want "
            "each repetition captured as its own file."
        )

        num_tokens = st.number_input(
            "Number of tokens (separate recording files per item)",
            min_value=1,
            max_value=9,
            value=1,
            step=1,
            format="%d",
            help=(
                "Each token is one more copy of every prompt in the script, so "
                "the recorder makes that many files per item. Keep it at 1 for "
                "repetitions within a single file."
            ),
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

            if st.button("Return to Main Menu", use_container_width=True):
                del st.session_state._generated_script
                go_back_to_menu()

            render_script_output(
                st.session_state._generated_script,
                filename="speechrecorder_script.xml",
                key="custom",
            )
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
