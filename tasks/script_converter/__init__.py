"""
tasks/script_converter/
Script Conversion — script-to-IPA (and script-to-script) transcoding pipelines.

Self-contained subpackage: nothing here imports from, or is imported by, any other
tasks/*.py module. Ported from the standalone Orthographizer app.

To add a new source script/language pipeline (e.g. Lao-script Jeh -> IPA):
  1. Add pipelines/<name>.py with build_pipeline()/run_pipeline() (see
     pipelines/registry.py's module docstring for the interface).
  2. Add an entry to pipelines/registry.py's PIPELINES dict, including
     source_script_ranges (Unicode codepoint ranges for the source script).
No changes to processors/ or app.py's screen are needed -- both are driven by the
registry entry's metadata.
"""
