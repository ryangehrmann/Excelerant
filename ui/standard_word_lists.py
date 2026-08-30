"""
ui/standard_word_lists.py
The Collect Data "standard word list" path: a catalog of bundled word list
tools, then a per-tool page (tailored to the chosen recording platform) with
three actions - download the spreadsheet, download the documentation, or
generate the import file for the chosen platform.
"""

import streamlit as st

from tasks import (
    FRAME_PLACEHOLDER,
    available_gloss_languages,
    documentation_html,
    generate_tool_prompts_list,
    generate_tool_script,
    get_word_list_tool,
    list_word_list_tools,
    load_word_list,
    read_wordlist_bytes,
)
from ui.create_data_collection_script import render_script_output
from ui.navigation import Screen, navigate_to


_PLATFORM_LABEL = {
    "speechrecorder": "SpeechRecorder (computer)",
    "prompts": "Prompts (Android)",
}


def screen_standard_word_lists():
    """Route between the tool catalog and a single tool's detail page."""
    selected_id = st.session_state.get("selected_word_list_tool")
    tool = get_word_list_tool(selected_id) if selected_id else None

    if tool is None:
        _render_tool_catalog()
        return

    # A tool is picked but no platform yet - send them to the platform fork.
    if st.session_state.get("collection_target") not in _PLATFORM_LABEL:
        navigate_to(Screen.COLLECT_PLATFORM)
        return

    _render_tool_detail(tool)


def _clear_tool_output():
    for key in (
        "_swl_script", "_swl_script_tool_id",
        "_swl_prompts", "_swl_prompts_tool_id",
    ):
        st.session_state.pop(key, None)


def _render_tool_catalog():
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.markdown("---")
        st.image("assets/excelerant_banner.png", use_container_width=True)
        st.markdown("---")

        st.markdown(
            """
            ### Standard word lists

            Ready-made lists - no spreadsheet needed. Pick one, then choose
            your recording platform.
            """
        )

        st.markdown("")

        tools = list_word_list_tools()

        if not tools:
            st.info("No standard word list tools are installed yet.")
        else:
            for tool in tools:
                if st.button(tool.name, key=f"swl_{tool.id}", use_container_width=True, type="primary"):
                    st.session_state.selected_word_list_tool = tool.id
                    _clear_tool_output()
                    navigate_to(Screen.COLLECT_PLATFORM)
                if tool.summary:
                    st.caption(tool.summary)
                st.markdown("")

        st.markdown("---")

        if st.button("← Back", use_container_width=True):
            navigate_to(Screen.COLLECT_LEXICAL_DATA_HUB)


def _render_tool_detail(tool):
    target = st.session_state.get("collection_target")
    is_sr = target == "speechrecorder"

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.markdown("---")

        nav1, nav2 = st.columns(2)
        with nav1:
            if st.button("← All word lists", use_container_width=True):
                st.session_state.selected_word_list_tool = None
                _clear_tool_output()
                navigate_to(Screen.STANDARD_WORD_LISTS)
        with nav2:
            if st.button("Change platform", use_container_width=True):
                navigate_to(Screen.COLLECT_PLATFORM)

        st.title(tool.name)

        try:
            df = load_word_list(tool)
        except Exception as e:  # noqa: BLE001
            st.error(f"Could not read this tool's word list: {e}")
            return

        st.caption(f"{len(df):,} items · recording with **{_PLATFORM_LABEL.get(target, target)}**")
        st.markdown("---")

        if tool.description:
            st.markdown(tool.description)
        elif tool.summary:
            st.markdown(tool.summary)

        st.markdown("---")

        # ── Gloss language ─────────────────────────────────────────────────
        languages = available_gloss_languages(tool, df)
        if not languages:
            st.error(
                "This tool has no usable gloss columns - its `tool.toml` and "
                "`wordlist` don't line up."
            )
            return

        label_to_col = {g.label: g.column for g in languages}

        if len(languages) == 1:
            primary_label = languages[0].label
            st.markdown(f"**Gloss language:** {primary_label}")
        else:
            primary_label = st.selectbox(
                "Primary gloss language",
                options=[g.label for g in languages],
                index=0,
                key=f"swl_primary_{tool.id}",
                help="The main text shown for each prompt.",
            )
        primary_col = label_to_col[primary_label]

        secondary_col = None
        if len(languages) >= 2:
            secondary_choices = ["— none —"] + [
                g.label for g in languages if g.label != primary_label
            ]
            secondary_label = st.selectbox(
                "Secondary gloss language (optional)",
                options=secondary_choices,
                index=0,
                key=f"swl_secondary_{tool.id}",
                help="A second gloss shown alongside the first.",
            )
            if secondary_label != "— none —":
                secondary_col = label_to_col[secondary_label]

        # ── SpeechRecorder-only options ───────────────────────────────────
        num_tokens = int(tool.recommended_tokens)
        sentence_frame = ""
        if is_sr:
            num_tokens = st.number_input(
                "Number of tokens (separate recording files per item)",
                min_value=1,
                max_value=9,
                value=int(tool.recommended_tokens),
                step=1,
                format="%d",
                key=f"swl_tokens_{tool.id}",
                help=(
                    "How many **separate recording files** to make for each "
                    "item. Leave this at **1** if your participant will simply "
                    "say each word several times within one recording. Raise it "
                    "only when you want each repetition captured as its own file."
                ),
            )
            sentence_frame = st.text_input(
                "Sentence frame (optional)",
                placeholder=f"I will say {FRAME_PLACEHOLDER} now",
                help=(
                    f"A carrier sentence for every prompt. Put "
                    f"`{FRAME_PLACEHOLDER}` (three underscores) where the word "
                    f"goes. Leave blank for none."
                ),
                key=f"swl_frame_{tool.id}",
            ).strip()
            if sentence_frame and FRAME_PLACEHOLDER in sentence_frame:
                example = str(df[primary_col].iloc[0])
                st.caption("Preview: " + sentence_frame.replace(FRAME_PLACEHOLDER, f"**{example}**"))

        st.markdown("---")

        # ── The three actions ─────────────────────────────────────────────
        st.download_button(
            "Word list spreadsheet",
            data=read_wordlist_bytes(tool),
            file_name=tool.wordlist_download_name,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
            key=f"swl_dl_wl_{tool.id}",
        )

        if tool.documentation_path is not None:
            st.download_button(
                "Word list documentation",
                data=documentation_html(tool).encode("utf-8"),
                file_name=f"{tool.id}_documentation.html",
                mime="text/html",
                use_container_width=True,
                key=f"swl_dl_doc_{tool.id}",
            )

        if is_sr:
            _render_sr_generate(tool, primary_col, secondary_col, num_tokens, sentence_frame)
        else:
            _render_prompts_generate(tool, primary_col, secondary_col)


def _render_sr_generate(tool, primary_col, secondary_col, num_tokens, sentence_frame):
    if st.button(
        "Generate SpeechRecorder script",
        type="primary",
        use_container_width=True,
        key=f"swl_gen_sr_{tool.id}",
    ):
        with st.spinner("Generating XML script..."):
            result = generate_tool_script(
                tool,
                int(num_tokens),
                primary_gloss_column=primary_col,
                secondary_gloss_column=secondary_col,
                sentence_frame=sentence_frame,
            )
        if not result.success:
            st.error(f"**Error:** {result.error}")
        else:
            st.session_state._swl_script = result.script
            st.session_state._swl_script_tool_id = tool.id
            st.rerun()

    if (
        st.session_state.get("_swl_script")
        and st.session_state.get("_swl_script_tool_id") == tool.id
    ):
        render_script_output(
            st.session_state._swl_script,
            filename=f"{tool.id}_speechrecorder_script.xml",
            key=f"swl_{tool.id}",
        )


def _render_prompts_generate(tool, primary_col, secondary_col):
    if st.button(
        "Generate Prompts list",
        type="primary",
        use_container_width=True,
        key=f"swl_gen_pr_{tool.id}",
    ):
        with st.spinner("Building prompt list..."):
            result = generate_tool_prompts_list(
                tool,
                primary_gloss_column=primary_col,
                secondary_gloss_column=secondary_col,
            )
        if not result.success:
            st.error(f"**Error:** {result.error}")
        else:
            st.session_state._swl_prompts = result
            st.session_state._swl_prompts_tool_id = tool.id
            st.rerun()

    if (
        st.session_state.get("_swl_prompts")
        and st.session_state.get("_swl_prompts_tool_id") == tool.id
    ):
        result = st.session_state._swl_prompts
        st.success(f"Prompt list generated - {len(result.dataframe):,} prompts.")

        st.markdown(
            "Copy the file onto the Android device, open **Prompts**, tap "
            "**Import Prompt List…**, and pick it."
        )

        dl1, dl2 = st.columns(2)
        with dl1:
            st.download_button(
                "Download prompts.csv",
                data=result.csv_text.encode("utf-8"),
                file_name=f"{tool.id}_prompts.csv",
                mime="text/csv",
                type="primary",
                use_container_width=True,
                key=f"swl_dl_pr_csv_{tool.id}",
            )
        with dl2:
            st.download_button(
                "Download prompts.xlsx",
                data=result.xlsx_bytes,
                file_name=f"{tool.id}_prompts.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
                key=f"swl_dl_pr_xlsx_{tool.id}",
            )
        st.dataframe(result.dataframe, use_container_width=True, height=240)
