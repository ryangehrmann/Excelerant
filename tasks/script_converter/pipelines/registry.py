"""
pipelines/registry.py
Registry of available transcoding pipelines.
Each entry maps a display label to metadata and the module that implements it.

To add a new pipeline (e.g. Lao-script Jeh -> IPA):
  1. Create pipelines/<name>.py with build_pipeline() and run_pipeline()
     (see pipelines/brao_khmer_ipa.py for the interface).
  2. Add an entry to PIPELINES below, including source_script_ranges — a list
     of (start, end) Unicode codepoint ranges for the source script. This
     drives entry-column detection/validation in processors/xlsx_input.py and
     source-token detection in processors/text_input.py, so no other code
     needs to change to support a new source script.
The Excelerant Script Conversion screen auto-discovers pipelines from this dict.

Unicode block reference for common Mainland Southeast Asian scripts:
  Khmer: 0x1780-0x17FF   Lao: 0x0E80-0x0EFF   Thai: 0x0E00-0x0E7F
"""

PIPELINES = {
    "Brao (Khmer script) → IPA": {
        "source_lang": "Brao",
        "source_script": "Khmer",
        "source_script_ranges": [(0x1780, 0x17FF)],
        "target": "IPA",
        "module": "tasks.script_converter.pipelines.brao_khmer_ipa",
    },
    "Brao (Khmer script) → Lao": {
        "source_lang": "Brao",
        "source_script": "Khmer",
        "source_script_ranges": [(0x1780, 0x17FF)],
        "target": "Lao",
        "module": "tasks.script_converter.pipelines.brao_khmer_lao",
    },
}
