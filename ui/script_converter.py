"""
ui/script_converter.py
Script Conversion screen: transcode text from a national/practical
orthography to IPA (and other scripts) using a fixed pipeline for a
specific language. Ported from the standalone Orthographizer app.
"""

import importlib

import pandas as pd
import streamlit as st

from tasks import (
    SCRIPT_CONVERTER_PIPELINES,
    load_xlsx,
    detect_entry_column,
    detect_index_column,
    validate_entry_column,
    prepare_df,
    FIXED_COLS,
    write_xlsx,
    find_unknown_chars,
    read_text_file,
    build_ipa_only_docx,
    build_interlinear_html,
)
from ui.navigation import Screen, navigate_to


@st.cache_resource(show_spinner="Loading pipeline…")
def _get_script_converter_pipeline(module_path: str):
    mod = importlib.import_module(module_path)
    return mod.build_pipeline(), mod.run_pipeline


def _format_unicode_ranges(ranges: list[tuple[int, int]]) -> str:
    return ", ".join(f"U+{lo:04X}–U+{hi:04X}" for lo, hi in ranges)


def screen_script_converter():
    """Script Conversion: transcode text from a national/practical orthography
    to IPA (and other scripts) using a fixed pipeline for a specific language.

    Deliberately kept as one self-contained wizard-style screen (not the
    config/output two-column layout used by database-driven tasks) since it
    doesn't operate on st.session_state.database at all -- it has its own
    upload flow that accepts more flexible input than Excelerant's shared
    lexical database format.
    """

    st.title("Script Conversion")
    st.caption(
        "Transcode text from a national/practical orthography to IPA (and other "
        "scripts) using a fixed pipeline for a specific language."
    )

    if st.button("← Back", key="sc_back"):
        navigate_to(Screen.ORTHOGRAPHY_HUB)

    st.markdown("---")

    # ── Pipeline selection ──────────────────────────────────────────────
    st.subheader("1 · Transcoding pipeline")
    pipeline_label = st.selectbox(
        "Select transcoding pipeline",
        options=list(SCRIPT_CONVERTER_PIPELINES.keys()),
        help="Choose the source language/script and transcoding target.",
        key="sc_pipeline_select",
    )
    pipeline_meta = SCRIPT_CONVERTER_PIPELINES[pipeline_label]
    script_ranges = pipeline_meta["source_script_ranges"]
    script_label = pipeline_meta["source_script"]

    (flat_dict, segments_dict), run_pipeline = _get_script_converter_pipeline(
        pipeline_meta["module"]
    )

    st.info(
        f"**Source:** {pipeline_meta['source_lang']} ({pipeline_meta['source_script']} script)  "
        f"→  **Target:** {pipeline_meta['target']}"
    )

    # ── File type selection ──────────────────────────────────────────────
    st.subheader("2 · Upload file")
    file_type = st.radio(
        "What kind of file are you uploading?",
        options=["Dictionary / word list (.xlsx)", "Text file (.txt or .docx)"],
        horizontal=True,
        key="sc_file_type",
    )

    if file_type == "Dictionary / word list (.xlsx)":
        _screen_script_converter_xlsx(run_pipeline, flat_dict, segments_dict, script_ranges, script_label)
    else:
        _screen_script_converter_text(run_pipeline, flat_dict, segments_dict, script_ranges, script_label)


def _screen_script_converter_xlsx(run_pipeline, flat_dict, segments_dict, script_ranges, script_label):
    """PATH A: xlsx dictionary / word list."""

    uploaded = st.file_uploader(
        "Upload your .xlsx file",
        type=["xlsx"],
        key="sc_xlsx_uploader",
    )

    if uploaded is None:
        return

    # Size check
    uploaded.seek(0, 2)
    size_mb = uploaded.tell() / (1024 * 1024)
    uploaded.seek(0)
    if size_mb > 50:
        st.warning(f"File is {size_mb:.1f} MB — large files may take a while to process.")

    # Load
    with st.spinner("Reading file…"):
        df, err = load_xlsx(uploaded)

    if err:
        st.error(err)
        return

    st.success(f"File loaded — {len(df):,} rows, {len(df.columns)} columns.")

    # ── Entry column detection ───────────────────────────────────────
    entry_col = detect_entry_column(df)

    if entry_col is None:
        st.warning(
            "Could not find a column named **entry_ortho**. "
            f"Please select the column that contains the {script_label}-script entries."
        )
        entry_col = st.selectbox(
            f"{script_label}-script entry column",
            options=list(df.columns),
            key="sc_entry_col_select",
        )

    # Warn if column doesn't look like the expected script
    warn = validate_entry_column(df, entry_col, script_ranges, script_label)
    if warn:
        st.warning(warn)

    # ── Index column detection ───────────────────────────────────────
    idx_info = detect_index_column(df)
    index_col = None
    generate_index = False

    if idx_info["found"]:
        index_col = idx_info["found"]
        st.info(f"Using **{index_col}** as the index column.")
    elif idx_info["needs_user_input"] and idx_info["candidate"]:
        candidate = idx_info["candidate"]
        use_candidate = st.radio(
            f"The column **{candidate!r}** looks like it might be an index "
            f"(mostly integers). Use it as the index?",
            options=["Yes, use it as the index", "No, generate a new index"],
            key="sc_index_radio",
        )
        if use_candidate.startswith("Yes"):
            index_col = candidate
        else:
            generate_index = True
    else:
        st.info("No index column found — a sequential index will be created.")
        generate_index = True

    # ── Process button ───────────────────────────────────────────────
    if st.button("Process", type="primary", key="sc_process_xlsx"):

        with st.spinner("Preparing data…"):
            df_ready = prepare_df(
                df,
                entry_col=entry_col,
                index_col=index_col,
                generate_index=generate_index,
            )

        progress_bar = st.progress(0, text="Transcoding entries…")
        total = len(df_ready)

        rows = []
        extra_cols = [c for c in df_ready.columns if c not in ("entry_ortho", "index")]
        errors = []

        for i, (_, row) in enumerate(df_ready.iterrows()):
            idx = row.get("index", i)
            entry_ortho = row.get("entry_ortho", "")
            extra = {col: row.get(col, "") for col in extra_cols}

            try:
                ipa, syllables = run_pipeline(entry_ortho, flat_dict, segments_dict)
            except Exception as e:
                errors.append(str(e))
                syllables = []
                ipa = None

            if not syllables:
                rows.append({
                    "index": idx, "sub_index": 0,
                    "entry_ortho": entry_ortho, "entry": ipa or "",
                    "word_lao": "", "word": "",
                    "P": "", "R": "", "C": "", "M": "", "V": "", "F": "", "T": "",
                    "ambiguous": False,
                    **extra,
                })
            else:
                for sub_idx, syl in enumerate(syllables):
                    rows.append({
                        "index": idx, "sub_index": sub_idx,
                        "entry_ortho": entry_ortho, "entry": ipa or "",
                        "word_lao": syl.get("word_lao", ""),
                        "word": "",
                        "P": syl.get("P", ""), "R": syl.get("R", ""),
                        "C": syl.get("C", ""), "M": syl.get("M", ""),
                        "V": syl.get("V", ""), "F": syl.get("F", ""),
                        "T": syl.get("T", ""),
                        "ambiguous": syl.get("ambiguous", False),
                        **extra,
                    })

            if (i + 1) % max(1, total // 100) == 0 or i == total - 1:
                progress_bar.progress((i + 1) / total, text=f"Transcoding… {i + 1:,}/{total:,}")

        progress_bar.empty()

        output_df = pd.DataFrame(rows)
        final_extra = [c for c in output_df.columns if c not in FIXED_COLS]
        output_df = output_df[FIXED_COLS + final_extra]

        n_ambiguous = int(output_df["ambiguous"].sum())
        ambig_rate = n_ambiguous / max(len(output_df), 1)

        unknown_df = find_unknown_chars(
            df_ready["entry_ortho"],
            segments_dict.get("conv_dict", flat_dict),
        )

        col1, col2, col3 = st.columns(3)
        col1.metric("Entries processed", f"{total:,}")
        col2.metric("Output rows", f"{len(output_df):,}")
        col3.metric("Ambiguous", f"{n_ambiguous:,}")

        if errors:
            st.warning(f"{len(errors)} entries raised errors during processing.")
            with st.expander("Show errors"):
                st.write(errors[:50])

        if not unknown_df.empty:
            st.warning(f"{len(unknown_df)} character(s) not found in the conversion table:")
            st.dataframe(unknown_df, use_container_width=False)

        if ambig_rate > 0.30:
            st.warning(
                f"{ambig_rate:.0%} of output rows are flagged as ambiguous. "
                "You may want to review the conversion table."
            )

        with st.spinner("Formatting output file…"):
            xlsx_bytes = write_xlsx(output_df)

        base_name = uploaded.name.rsplit(".", 1)[0]
        st.download_button(
            label="⬇️  Download output (.xlsx)",
            data=xlsx_bytes,
            file_name=f"{base_name}_converted.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="sc_download_xlsx",
        )


def _screen_script_converter_text(run_pipeline, flat_dict, segments_dict, script_ranges, script_label):
    """PATH B: text file (.txt or .docx)."""

    uploaded = st.file_uploader(
        "Upload your text file",
        type=["txt", "docx"],
        key="sc_text_uploader",
    )

    if uploaded is None:
        return

    # Clear cached results when a new file is uploaded
    if st.session_state.get("sc_text_source_name") != uploaded.name:
        st.session_state.pop("sc_text_results", None)
        st.session_state["sc_text_source_name"] = uploaded.name

    # Size check
    uploaded.seek(0, 2)
    size_mb = uploaded.tell() / (1024 * 1024)
    uploaded.seek(0)
    if size_mb > 20:
        st.warning(f"File is {size_mb:.1f} MB — this may take a moment to process.")

    with st.spinner("Reading file…"):
        paragraphs, err = read_text_file(uploaded, uploaded.name, script_ranges)

    if err:
        st.error(err)
        return

    n_paragraphs = sum(1 for p in paragraphs if p)
    n_source_script_tokens = sum(1 for p in paragraphs for t, k in p if k and t.strip())

    if n_source_script_tokens == 0:
        st.warning(
            f"No {script_label} text was detected in the uploaded file. "
            f"Make sure the file contains characters in the {script_label} "
            f"Unicode block(s): {_format_unicode_ranges(script_ranges)}."
        )
        return

    st.success(
        f"File loaded — {n_paragraphs:,} paragraph(s), "
        f"{n_source_script_tokens:,} {script_label} token(s) found."
    )

    if st.button("Process", type="primary", key="sc_process_text"):
        with st.spinner("Transcoding…"):
            ipa_bytes = build_ipa_only_docx(paragraphs, run_pipeline, flat_dict, segments_dict)
            interlinear_bytes = build_interlinear_html(paragraphs, run_pipeline, flat_dict, segments_dict)
        base_name = uploaded.name.rsplit(".", 1)[0]
        st.session_state["sc_text_results"] = {
            "ipa_bytes": ipa_bytes,
            "interlinear_bytes": interlinear_bytes,
            "base_name": base_name,
        }

    if "sc_text_results" in st.session_state:
        import io, zipfile
        r = st.session_state["sc_text_results"]
        ipa_bytes = r["ipa_bytes"]
        interlinear_bytes = r["interlinear_bytes"]
        base_name = r["base_name"]

        zip_buf = io.BytesIO()
        with zipfile.ZipFile(zip_buf, "w") as zf:
            zf.writestr(f"{base_name}_ipa.docx", ipa_bytes)
            zf.writestr(f"{base_name}_interlinear.html", interlinear_bytes)
        zip_bytes = zip_buf.getvalue()

        st.success("Done! Download your output files below.")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.download_button(
                label="⬇️  IPA-only (.docx)",
                data=ipa_bytes,
                file_name=f"{base_name}_ipa.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                key="sc_dl_ipa",
            )
        with col2:
            st.download_button(
                label="⬇️  Interlinear (.html)",
                data=interlinear_bytes,
                file_name=f"{base_name}_interlinear.html",
                mime="text/html",
                key="sc_dl_interlinear",
            )
        with col3:
            st.download_button(
                label="⬇️  Both (.zip)",
                data=zip_bytes,
                file_name=f"{base_name}_converted.zip",
                mime="application/zip",
                key="sc_dl_both",
            )
        st.caption("Ambiguous sequences are highlighted in red and wrapped in { }.")
