"""
Create Data Collection Script Task
==================================

Generates XML scripts for SpeechRecorder data collection sessions.

The script creates prompts with:
- Primary gloss (required; rows with a blank primary gloss are skipped)
- Secondary gloss (optional)
- Sentence frame (optional)
- Extra information (optional)

Supports multiple token repetitions and selective frame application.
"""

import pandas as pd
from dataclasses import dataclass, field


@dataclass
class ScriptResult:
    """Result of script generation."""
    success: bool
    script: str | None = None
    error: str | None = None
    # Index values of rows left out because their primary gloss was blank
    skipped_indices: list[str] = field(default_factory=list)


def _is_blank(value) -> bool:
    """True for NaN/None cells and strings that are empty or only whitespace."""
    return pd.isna(value) or str(value).strip() == ""


def _format_index(value) -> str:
    """Render an index cell as text, dropping the '.0' pandas adds to whole numbers."""
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def assemble_prompt_dict(
    df: pd.DataFrame,
    index_col: str,
    primary_gloss_col: str,
    secondary_gloss_col: str | None,
    frame_col: str | None,
    extra_col: str | None,
) -> tuple[dict | None, str | None]:
    """
    Build a dictionary of prompts from the dataframe.

    Args:
        df: DataFrame with the lexical data
        index_col: Column name for index numbers
        primary_gloss_col: Column name for primary glosses
        secondary_gloss_col: Column name for secondary glosses (or None)
        frame_col: Column name for sentence frames (or None)
        extra_col: Column name for extra info (or None)

    Returns:
        Tuple of (prompt_dict, error_message). If successful, error is None.
    """
    # Ensure that all index numbers are unique
    if df[index_col].duplicated().any():
        duplicate_values = df[index_col][df[index_col].duplicated()].unique()
        error_msg = (
            "Your index column contains duplicate values. Each word list item must have "
            "a unique index number. Please fix this in your Excel file, then clear the "
            f"database and re-upload. Duplicate values: {', '.join(map(str, duplicate_values))}"
        )
        return None, error_msg

    prompt_dict = {}

    for _, row in df.iterrows():
        # Nothing to prompt the speaker with; generate_script reports these
        if _is_blank(row[primary_gloss_col]):
            continue

        row_dict = {}

        # Add index
        row_dict['index'] = str(row[index_col])

        # Add primary gloss
        row_dict['primary_gloss'] = str(row[primary_gloss_col])

        # Add secondary_gloss
        if secondary_gloss_col and pd.notna(row[secondary_gloss_col]):
            row_dict['secondary_gloss'] = str(row[secondary_gloss_col])
        else:
            row_dict['secondary_gloss'] = ''

        # Add frame if specified
        if frame_col and pd.notna(row[frame_col]):
            row_dict['frame'] = str(row[frame_col])
        else:
            row_dict['frame'] = ''

        # Add extra if specified
        if extra_col and pd.notna(row[extra_col]):
            row_dict['extra'] = str(row[extra_col])
        else:
            row_dict['extra'] = ''

        # Add row_dict to prompt_dict, keyed by index
        prompt_dict[str(row[index_col])] = row_dict

    return prompt_dict, None


def build_prompt(
    index: str,
    token_num: int,
    tokens_in_frame: list[int],
    prompt_dict: dict,
) -> str:
    """
    Build a single XML prompt for one item.

    Args:
        index: The index value for this item
        token_num: Which token number (for repetitions)
        tokens_in_frame: List of token numbers that should include frame
        prompt_dict: Dictionary of all prompts

    Returns:
        XML string for this prompt
    """
    # Get data for this index from prompt_dict
    primary_gloss = prompt_dict[index]['primary_gloss']
    secondary_gloss = prompt_dict[index]['secondary_gloss']
    frame = prompt_dict[index]['frame']
    extra = prompt_dict[index]['extra']

    # Set frame to '' if this is not a token in frame
    if token_num not in tokens_in_frame:
        frame = ''

    # Update secondary_gloss to have index at the front of the string
    # We put index and secondary gloss on the same prompt row to save space
    secondary_gloss = (str(index) + ' ' + secondary_gloss).strip()

    # XML code at the head of a prompt
    item_head = """      <recording itemcode="INDEX">
        <recprompt>
          <mediaitem>
            <promptdoc>
              <body>
                <p>
"""

    # Replace INDEX with actual index & token_num
    item_head = item_head.replace('INDEX', '_' + index + '_' + str(token_num))

    # XML code at the tail of a prompt
    item_tail = """                </p>
              </body>
            </promptdoc>
          </mediaitem>
        </recprompt>
      </recording>
"""

    # XML code for the prompt itself
    item_content = """                  <text>REPLACE</text>
                  <br/>
"""

    # Build this prompt from prompt_dict
    my_content = []

    for x in [primary_gloss, secondary_gloss, frame, extra]:
        if x != '':
            my_content.append(item_content.replace('REPLACE', x))

    # XML code for blank lines to add between prompts
    blank_line = """                  <text>---</text>
                  <br/>
"""

    # Add blank lines between prompts
    prompt_parts = []
    for x in my_content:
        prompt_parts.append(x)
        prompt_parts.append(blank_line)

    # Remove last blank line
    if prompt_parts:
        prompt_parts = prompt_parts[:-1]

    prompt = ''.join(prompt_parts)

    # Add the head and tail to the prompt
    prompt = item_head + prompt + item_tail

    return prompt


def build_script(prompts: str) -> str:
    """
    Assemble the complete XML script from prompts.

    Args:
        prompts: Concatenated prompt XML strings

    Returns:
        Complete XML script
    """
    script_head = """<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<!DOCTYPE script SYSTEM "SpeechRecPrompts_4.dtd">
<script id="">
  <recordingscript>
    <section>
"""

    script_tail = """    </section>
  </recordingscript>
</script>"""

    return script_head + prompts + script_tail


def generate_script(
    df: pd.DataFrame,
    index_col: str,
    primary_gloss_col: str,
    secondary_gloss_col: str | None,
    frame_col: str | None,
    extra_col: str | None,
    num_tokens: int,
    tokens_in_frame: list[int],
) -> ScriptResult:
    """
    Generate a complete SpeechRecorder XML script.

    Args:
        df: DataFrame with lexical data
        index_col: Column name for index numbers
        primary_gloss_col: Column name for primary glosses
        secondary_gloss_col: Column name for secondary glosses (or None)
        frame_col: Column name for sentence frames (or None)
        extra_col: Column name for extra info (or None)
        num_tokens: Number of token repetitions (1-9)
        tokens_in_frame: List of token numbers that should include frame

    Returns:
        ScriptResult with success status and script or error
    """
    # Build the prompt dictionary
    prompt_dict, error = assemble_prompt_dict(
        df,
        index_col,
        primary_gloss_col,
        secondary_gloss_col,
        frame_col,
        extra_col,
    )

    if error:
        return ScriptResult(success=False, error=error)

    skipped_indices = [
        _format_index(row[index_col])
        for _, row in df.iterrows()
        if _is_blank(row[primary_gloss_col])
    ]

    if not prompt_dict:
        return ScriptResult(
            success=False,
            error=f"Every row has a blank '{primary_gloss_col}' cell, so there is nothing to prompt with.",
            skipped_indices=skipped_indices,
        )

    # Build all prompts
    prompt_list = []

    for token_num in range(1, num_tokens + 1):
        for p in prompt_dict:
            prompt_list.append(
                build_prompt(p, token_num, tokens_in_frame, prompt_dict)
            )

    # Convert prompt_list to string
    prompts = ''.join(prompt_list)

    # Build final script
    script = build_script(prompts)

    return ScriptResult(success=True, script=script, skipped_indices=skipped_indices)
