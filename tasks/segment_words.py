"""
Segment Words Task
==================

Breaks individual words into phonological columns: P, R, C, M, V, F, T
(Presyllable onset, presyllable Rime, main syllable Consonant onset,
 Medial, Vowel, Final/coda, Tone/register)

Processing pipeline:
1. Validate word column exists and has no NaN
2. Clean word column (normalize whitespace, remove punctuation)
3. Check each word for non-IPA characters -> mark as 'error'
4. Check each word for Chao number issues -> mark as 'error'
5. Extract tones (T column) for non-error rows
6. Split around vowels for non-error rows
7. Process onsets for non-error rows
8. Build summary and return result
"""

import re
import pandas as pd
import string
from collections import Counter
from dataclasses import dataclass, field


# =============================================================================
# Result dataclass
# =============================================================================

@dataclass
class SegmentationResult:
    """Result of the segment words operation."""
    success: bool
    df: pd.DataFrame | None = None
    error: str | None = None
    cleaning_report: dict = field(default_factory=dict)
    summary: dict = field(default_factory=dict)


# =============================================================================
# IPA character inventories
# =============================================================================

IPA_CONSONANTS = [
    'p','b','t','d','ʈ','ɖ','c','ɟ','k','g','q','ɢ','ʔ',
    'm','ɱ','n','ɳ','ɲ','ŋ','ɴ',
    'ʙ','r','ʀ',
    'ⱱ','ɾ','ɽ',
    'ɸ','β','f','v','θ','ð','s','z','ʃ','ʒ','ʂ','ʐ','ç','ʝ','x','ɣ','χ','ʁ','ħ','ʕ','h','ɦ',
    'ɬ','ɮ',
    'ʋ','ɹ','ɻ','j','ɰ',
    'l','ɭ','ʎ','ʟ',
    'ɘ','ɚ','ɝ','ɞ','ɟ',
    'ɓ','ɗ','ʄ','ɠ','ʛ',
    'ʍ','w','ɥ','ʜ','ʢ','ʡ','ɕ','ʑ','ɺ','ɧ',
    'ƈ','ȡ','ƙ','ƙ','ƴ','ƴ','ƥ','ʠ','ᶑ','ƭ','ȶ','ʇ','ⱳ','ᶚ',
    '∅',  # placeholder consonant
]

IPA_VOWELS = [
    'i','ɪ','e','ɛ','æ','a',
    'y','ʏ','ø','œ','ɶ',
    'ɨ','ɘ','ə','ɜ','ɐ',
    'ʉ','ɵ','ɞ',
    'ɯ','ɤ','ʌ','ɑ',
    'u','ʊ','o','ɔ','ɒ',
    'ɿ',  # apical fricated vowel (Sinitic)
]

IPA_DIACRITICS = [
    'ʰ','ʷ','ʲ','ˠ','ˤ','ʽ','ʼ','ͅ','ʻ','̥','̊','̬','̪','̺','̻','̼',
    '̣','᷂','ᵐ','ᶬ','ⁿ','ᶯ','ᶮ','ᵑ','ᶰ','ˀ','ˁ','ˑ','ː','̤','̰','̃','̩',
]

IPA_TONES = [
    '¹','²','³','⁴','⁵','⁶','⁷','⁸','⁹','⁰',
    '˥','˦','˧','˨','˩',
    'ᴴ','ᴸ',
]

ALL_IPA_CHARS = set(IPA_CONSONANTS + IPA_VOWELS + IPA_DIACRITICS + IPA_TONES)

# Phonological inventory sets for onset processing
AFFRICATES = {
    'pɸ','bβ','pf','bv','tθ','t̪θ','dð','d̪ð','ts','dz','tɬ','dɮ',
    'tʃ','dʒ','ʈʂ','ɖʐ','tɕ','ȶɕ','dʑ','ȡʑ','cç','ɟʝ','kx','gɣ',
    'qχ','ɢʁ',
}

CAN_ASPIRATE = {
    'p','t̪','t','ʈ','ȶ','c','k','q','s','pɸ','pf','tθ','t̪θ',
    'ts','tɬ','tʃ','ʈʂ','tɕ','ȶɕ','cç','kx','qχ',
}

NASALS = {'m','n̪','n','ɳ','ȵ','ɲ','ŋ','ɴ', 'ᵐ','ⁿ','ᶮ','ᵑ','ᶰ'}

MEDIALS = {'r','ɾ','ɹ','l','j','w'}

VOWELS_SET = {
    'i','ɪ','e','ɛ','æ','a','y','ʏ','ø','œ','ɶ','ɨ','ɘ','ə','ɜ',
    'ɵ','ɐ','ʉ','ɯ','ɤ','ʌ','ɑ','u','ʊ','o','ɔ','ɒ','ɿ',
}

CONS_RIMES = NASALS | {'r','ɾ','ɹ','l'}

ASPIRATION_MARKERS = {'ʰ','h'}
GLOTTAL_MARKERS = {'ˀ','ʔ'}

BASE_VOWELS_STR = 'iɪeɛæayʏøœɶɨɘəɜɵɐʉɯɤʌɑuʊoɔɒɿ'


# =============================================================================
# Cleaning function
# =============================================================================

def clean_transcription_column(df: pd.DataFrame, col: str) -> tuple[pd.DataFrame, dict]:
    """
    Clean a transcription column by normalizing whitespace and removing punctuation.

    Creates '{col}_orig' only if changes were made.

    Args:
        df: DataFrame to clean
        col: Column name to clean

    Returns:
        Tuple of (cleaned DataFrame, cleaning report dict)
    """
    df = df.copy()
    report = {
        "punctuation_removed": {},
        "whitespace_changes": 0,
        "changes_made": False,
    }

    original = df[col].copy()
    df[col] = df[col].astype(str)

    # Normalize Unicode whitespace
    unicode_spaces = [
        '\u00A0', '\u2000', '\u2001', '\u2002', '\u2003', '\u2004',
        '\u2005', '\u2006', '\u2007', '\u2008', '\u2009', '\u200A',
        '\u202F', '\u205F', '\u3000',
    ]
    for uspace in unicode_spaces:
        df[col] = df[col].str.replace(uspace, ' ', regex=False)

    # Count and remove punctuation
    all_text = ' '.join(df[col].dropna().astype(str))
    punct_counter = Counter(char for char in all_text if char in string.punctuation)
    if punct_counter:
        report["punctuation_removed"] = dict(punct_counter.most_common())
    translator = str.maketrans('', '', string.punctuation)
    df[col] = df[col].str.translate(translator)

    # Insert spaces at tone-marked syllable boundaries
    # Tone marks mid-string indicate a syllable break; insert space after them
    tone_break_pattern = r'([¹²³⁴⁵⁶⁷⁸⁹⁰˥˦˧˨˩]+)(?=[^\s¹²³⁴⁵⁶⁷⁸⁹⁰˥˦˧˨˩])'
    tone_before = df[col].copy()
    df[col] = df[col].str.replace(tone_break_pattern, r'\1 ', regex=True)
    report["tone_breaks_inserted"] = int((tone_before != df[col]).sum())

    # Normalize multiple whitespace to single space
    ws_before = df[col].copy()
    df[col] = df[col].str.replace(r'\s+', ' ', regex=True)
    report["whitespace_changes"] = int((ws_before != df[col]).sum())

    # Strip
    df[col] = df[col].str.strip()

    changes_made = not df[col].equals(original.astype(str))
    report["changes_made"] = changes_made

    if changes_made:
        df[f'{col}_orig'] = original

    return df, report


# =============================================================================
# IPA validation
# =============================================================================

def check_ipa_characters(word_text: str) -> set[str]:
    """
    Check a single word for non-IPA characters.

    Args:
        word_text: The word string to check

    Returns:
        Set of unrecognized characters (empty if all valid)
    """
    word_chars = set(char for char in word_text if char != ' ')
    return word_chars - ALL_IPA_CHARS


def validate_chao_numbers(word_text: str) -> str | None:
    """
    Validate that a single word has at most one contiguous set of 1-3 Chao numbers.

    Args:
        word_text: The word string to check

    Returns:
        Error string if invalid, None if valid
    """
    chao_pattern = r'[¹²³⁴⁵⁶⁷⁸⁹⁰]+'
    chao_matches = re.findall(chao_pattern, word_text)

    if len(chao_matches) > 1:
        return (
            f"Multiple tone sequences in '{word_text}': "
            f"{', '.join(chao_matches)}"
        )

    if len(chao_matches) == 1 and len(chao_matches[0]) > 3:
        return (
            f"Tone sequence too long in '{word_text}': "
            f"'{chao_matches[0]}' ({len(chao_matches[0])} numbers, max 3)"
        )

    return None


# =============================================================================
# Tone extraction
# =============================================================================

def extract_tones(df: pd.DataFrame, word_col: str) -> tuple[pd.DataFrame, str | None]:
    """
    Extract tone and register transcriptions from word column to 'T' column.

    Handles Chao numbers, tone letters, and voice quality markers.

    Args:
        df: DataFrame containing word data
        word_col: Column name containing word transcriptions

    Returns:
        Tuple of (updated DataFrame with 'T' column, error string or None)
    """
    # Tone letter to Chao number mapping
    tone_map = {'˥': '¹', '˦': '²', '˧': '³', '˨': '⁴', '˩': '⁵'}

    df = df.copy()
    for lett, chao in tone_map.items():
        df[word_col] = df[word_col].str.replace(lett, chao, regex=False)

    has_tones = df[word_col].str.contains(r'[¹²³⁴⁵⁶⁷⁸⁹⁰]', na=False).any()

    if has_tones:
        # Extract tones from end of word
        df['T'] = df[word_col].str.extract(r'([¹²³⁴⁵⁶⁷⁸⁹⁰]+)$')[0]
        df[word_col] = df[word_col].str.replace(r'[¹²³⁴⁵⁶⁷⁸⁹⁰]+$', '', regex=True)

        # Handle voice quality markers
        has_vq = df[word_col].str.contains(r'[̤̰]', na=False).any()
        if has_vq:
            df.loc[df[word_col].str.contains('̤', na=False), 'T'] += '+br'
            df.loc[df[word_col].str.contains('̰', na=False), 'T'] += '+cr'
            df[word_col] = df[word_col].str.replace('[̤̰]', '', regex=True)
    else:
        # Check for voice quality symbols (register notation)
        has_breathy = df[word_col].str.contains('̤', na=False).any()
        has_creaky = df[word_col].str.contains('̰', na=False).any()

        if has_breathy and has_creaky:
            return df, (
                "Both breathy and creaky voice symbols found in dataset. "
                "Cannot interpret mixed tone/register transcription systems."
            )
        elif has_breathy and not has_creaky:
            df['T'] = df[word_col].str.contains('̤', na=False).map(
                {True: 'ᴸ', False: 'ᴴ'}
            )
        elif has_creaky and not has_breathy:
            df['T'] = df[word_col].str.contains('̰', na=False).map(
                {True: 'ᴴ', False: 'ᴸ'}
            )
        else:
            df['T'] = ''
            return df, None

        # Remove voice quality symbols from words
        df[word_col] = df[word_col].str.replace('[̤̰]', '', regex=True)

    return df, None


# =============================================================================
# Syllabic consonant preprocessing
# =============================================================================

def preprocess_syllabic_consonants(
    df: pd.DataFrame, word_col: str
) -> tuple[pd.DataFrame, dict]:
    """
    Convert syllabic consonants to temporary monographs using Unicode Private Use Area.

    Args:
        df: DataFrame containing word data
        word_col: Column name containing word transcriptions

    Returns:
        Tuple of (preprocessed DataFrame, reverse mapping dict)
    """
    all_text = ''.join(df[word_col].fillna('').astype(str))
    syllabic_pattern = r'(.̩)'
    syllabic_matches = set(re.findall(syllabic_pattern, all_text))

    if not syllabic_matches:
        return df.copy(), {}

    # Create mapping using Unicode Private Use Area
    syllabic_map = {}
    for i, syllabic_cons in enumerate(sorted(syllabic_matches)):
        placeholder = chr(0xE000 + i)
        syllabic_map[syllabic_cons] = placeholder

    df_temp = df.copy()
    for original, placeholder in syllabic_map.items():
        df_temp[word_col] = df_temp[word_col].str.replace(
            original, placeholder, regex=False
        )

    reverse_map = {v: k for k, v in syllabic_map.items()}
    return df_temp, reverse_map


def postprocess_syllabic_consonants(
    df: pd.DataFrame, word_col: str, reverse_map: dict
) -> pd.DataFrame:
    """Convert temporary monographs back to syllabic consonants."""
    if not reverse_map:
        return df.copy()

    df_restored = df.copy()
    for placeholder, original in reverse_map.items():
        df_restored[word_col] = df_restored[word_col].str.replace(
            placeholder, original, regex=False
        )
        if 'parts' in df_restored.columns:
            df_restored['parts'] = df_restored['parts'].apply(
                lambda parts_list: (
                    [part.replace(placeholder, original) for part in parts_list]
                    if isinstance(parts_list, list) else parts_list
                )
            )

    return df_restored


# =============================================================================
# Split around vowels
# =============================================================================

def split_around_vowels(
    df: pd.DataFrame, word_col: str
) -> tuple[pd.DataFrame, str | None]:
    """
    Split words around the right-most vowel complex into [onset, vowel, coda].

    Words with no vowels get 'error' in all segmentation columns instead
    of halting the pipeline.

    Args:
        df: DataFrame containing word data
        word_col: Column name containing word transcriptions

    Returns:
        Tuple of (updated DataFrame with 'parts' column, error string or None)
    """
    # Preprocess syllabic consonants
    df_temp, reverse_map = preprocess_syllabic_consonants(df, word_col)

    # Build vowel pattern including syllabic placeholders
    syllabic_placeholders = ''.join(reverse_map.keys()) if reverse_map else ''
    all_vowel_chars = BASE_VOWELS_STR + syllabic_placeholders
    vowel_pattern = re.compile(f'[{re.escape(all_vowel_chars)}]+[ː̃]*')

    def split_word(word_str):
        """Split word around the right-most vowel complex."""
        vowel_matches = list(vowel_pattern.finditer(word_str))
        if not vowel_matches:
            return None  # No vowels found
        rightmost = vowel_matches[-1]
        onset = word_str[:rightmost.start()] or 'ʔ'
        vowel = rightmost.group()
        coda = word_str[rightmost.end():] or '∅'
        return [onset, vowel, coda]

    df_temp['parts'] = df_temp[word_col].apply(split_word)

    # Words with no vowels -> mark for error
    no_vowel_mask = df_temp['parts'].isna()

    # Postprocess syllabic consonants
    df_final = postprocess_syllabic_consonants(df_temp, word_col, reverse_map)

    # Mark no-vowel words with error placeholder (will be caught later)
    if no_vowel_mask.any():
        # Set parts to a sentinel list so process_onsets will mark as error
        df_final.loc[no_vowel_mask, 'parts'] = df_final.loc[no_vowel_mask, word_col].apply(
            lambda _: ['error', 'error', 'error']
        )

    return df_final, None


# =============================================================================
# Onset processing helpers
# =============================================================================

def _update_markers(mystring: str) -> str:
    """Update aspiration and glottal markers to superscript."""
    mystring = mystring.replace('h', 'ʰ')
    mystring = mystring.replace('ʔ', 'ˀ')
    return mystring


def _write_segments(df, i, C, V, F, M='', P='', R=''):
    """Write segmentation data to DataFrame row."""
    df.loc[i, 'C'] = C
    df.loc[i, 'V'] = V
    df.loc[i, 'F'] = F
    if M: df.loc[i, 'M'] = M
    if P: df.loc[i, 'P'] = P
    if R: df.loc[i, 'R'] = R


def _convert_voiceless_to_preaspiration(df, parts_col='parts'):
    """Convert voicelessness markers to pre-aspiration in onset strings."""
    def transform_onset(onset):
        voiceless_markers = ['̥', '̊']
        for marker in voiceless_markers:
            if marker in onset:
                marker_pos = onset.find(marker)
                consonant = onset[marker_pos - 1]
                onset = onset[:marker_pos - 1] + onset[marker_pos + 1:]
                onset = 'ʰ' + consonant + onset
        return onset

    df[parts_col] = df[parts_col].apply(
        lambda parts_list: (
            [transform_onset(parts_list[0])] + parts_list[1:]
            if isinstance(parts_list, list) else parts_list
        )
    )
    return df


def _convert_voiceless_to_postaspiration(df, parts_col='parts'):
    """Convert voicelessness markers to post-aspiration in coda strings."""
    def transform_coda(coda):
        for marker in ['̥', '̊']:
            if marker in coda:
                coda = coda.replace(marker, 'ʰ')
        return coda

    df[parts_col] = df[parts_col].apply(
        lambda parts_list: (
            parts_list[:-1] + [transform_coda(parts_list[-1])]
            if isinstance(parts_list, list) else parts_list
        )
    )
    return df


def _convert_superscript_nasals_to_regular(df, parts_col='parts'):
    """Convert superscript nasal markers to regular nasals."""
    superscript_map = {'ᵐ': 'm', 'ⁿ': 'n', 'ᶮ': 'ɲ', 'ᵑ': 'ŋ'}

    def transform(s):
        for marker, regular in superscript_map.items():
            if marker in s:
                s = s.replace(marker, regular)
        return s

    df[parts_col] = df[parts_col].apply(
        lambda parts_list: (
            [transform(parts_list[0]), parts_list[1], transform(parts_list[2])]
            if isinstance(parts_list, list) else parts_list
        )
    )
    return df


# =============================================================================
# Presyllable split helpers (for long onsets)
# =============================================================================

def _parse_main_onset(onset):
    """
    Parse a main syllable onset (no presyllable) into (C, M).

    Returns (C, M) tuple or None if the onset cannot be parsed.
    """
    n = len(onset)

    if n == 0:
        return ('ʔ', '')
    if n == 1:
        return (onset, '')

    c1, c2 = onset[0], onset[1]

    if n == 2:
        if onset in AFFRICATES:
            return (onset, '')
        if c1 in CAN_ASPIRATE and c2 in ASPIRATION_MARKERS:
            return (c1 + _update_markers(c2), '')
        if c1 in ASPIRATION_MARKERS | GLOTTAL_MARKERS:
            return (_update_markers(c1) + c2, '')
        if c2 in MEDIALS:
            return (c1, c2)
        return None

    c3 = onset[2]

    if n == 3:
        if c2 == '͡':
            return (c1 + c3, '')
        if c1 + c2 in AFFRICATES and c3 in ASPIRATION_MARKERS:
            return (c1 + c2 + _update_markers(c3), '')
        if c1 + c2 in AFFRICATES and c3 in MEDIALS:
            return (c1 + c2, c3)
        if c1 in CAN_ASPIRATE and c2 in ASPIRATION_MARKERS and c3 in MEDIALS:
            return (c1 + _update_markers(c2), c3)
        if c1 in ASPIRATION_MARKERS | GLOTTAL_MARKERS and c3 in MEDIALS:
            return (_update_markers(c1) + c2, c3)
        return None

    c4 = onset[3]

    if n == 4:
        if c2 == '͡' and c4 in MEDIALS:
            return (c1 + c3, c4)
        if c2 == '͡' and c4 in ASPIRATION_MARKERS:
            return (c1 + c3 + _update_markers(c4), '')
        if c1 + c2 in AFFRICATES and c3 in ASPIRATION_MARKERS and c4 in MEDIALS:
            return (c1 + c2 + _update_markers(c3), c4)
        return None

    if n == 5:
        c5 = onset[4]
        if c2 == '͡' and c4 in ASPIRATION_MARKERS and c5 in MEDIALS:
            return (c1 + c3 + _update_markers(c4), c5)
        return None

    return None


def _try_presyllable_split(onset):
    """
    Try to split a long onset at an internal vowel into presyllable + main onset.

    Finds the leftmost vowel in the onset, treats it as a non-phonological
    transition vowel in the presyllable, and extracts P, R, C, M.

    Returns (P, R, C, M) if successful, None if cannot parse.
    """
    # Find leftmost vowel in onset
    vowel_pos = None
    for idx, ch in enumerate(onset):
        if ch in VOWELS_SET:
            vowel_pos = idx
            break

    if vowel_pos is None or vowel_pos == 0:
        return None

    # Extract presyllable onset
    p_str = onset[:vowel_pos]

    # Normalize aspiration/glottalization in presyllable onset
    if len(p_str) >= 2:
        if p_str[-1] in ASPIRATION_MARKERS:
            p_str = p_str[:-1] + _update_markers(p_str[-1])
        elif p_str[0] in ASPIRATION_MARKERS | GLOTTAL_MARKERS:
            p_str = _update_markers(p_str[0]) + p_str[1:]

    # Determine rime and main onset
    after_vowel = vowel_pos + 1
    if (after_vowel < len(onset)
            and onset[after_vowel] in CONS_RIMES
            and after_vowel + 1 < len(onset)):
        # Consonant rime available with chars remaining for main onset;
        # discard vowel as non-phonological transition
        r_str = onset[after_vowel]
        main_onset = onset[after_vowel + 1:]
    else:
        # Vowel is the rime
        r_str = onset[vowel_pos]
        main_onset = onset[after_vowel:]

    # Parse main onset
    result = _parse_main_onset(main_onset)
    if result is None:
        return None

    c_str, m_str = result
    return (p_str, r_str, c_str, m_str)


# =============================================================================
# Process onsets (the big phonological rules function)
# =============================================================================

def process_onsets(df: pd.DataFrame, parts_col: str = 'parts', word_col: str = 'word'):
    """
    Process onsets to identify presyllables, complex segments, and medials.

    Assigns values to P, R, C, M, V, F columns based on phonological rules.
    Unrecognizable onset patterns get 'error' in all columns.

    Args:
        df: DataFrame with 'parts' column containing [onset, vowel, coda] lists
        parts_col: Column name for the parts lists
        word_col: Column name for word transcriptions

    Returns:
        Updated DataFrame with P, R, C, M, V, F columns filled
    """
    df = df.copy()

    # Normalize voiceless markers
    df = _convert_voiceless_to_preaspiration(df, parts_col)
    df = _convert_voiceless_to_postaspiration(df, parts_col)
    df = _convert_superscript_nasals_to_regular(df, parts_col)

    # Initialize columns
    for col in ['P', 'R', 'C', 'M', 'V', 'F']:
        df[col] = ''

    # Calculate onset lengths
    df['_onset_len'] = df[parts_col].apply(
        lambda p: len(p[0]) if isinstance(p, list) else 0
    )

    # Use local references for the inventory sets
    affricates = AFFRICATES
    can_aspirate = CAN_ASPIRATE
    nasals = NASALS
    medials_set = MEDIALS
    vowels = VOWELS_SET
    cons_rimes = CONS_RIMES
    aspiration_markers = ASPIRATION_MARKERS
    glottal_markers = GLOTTAL_MARKERS

    # --- Length 1 onsets (vectorized) ---
    len1_mask = df['_onset_len'] == 1
    df.loc[len1_mask, 'C'] = df.loc[len1_mask, parts_col].str[0]
    df.loc[len1_mask, 'V'] = df.loc[len1_mask, parts_col].str[1]
    df.loc[len1_mask, 'F'] = df.loc[len1_mask, parts_col].str[2]

    # Track medials list from len-2 processing
    medial_seg = []

    # --- Length 2 onsets ---
    len2_indices = df[df['_onset_len'] == 2].index
    for i in len2_indices:
        onset, vowel, coda = df.loc[i, parts_col]
        char1, char2 = onset[0], onset[1]

        if onset in affricates:
            _write_segments(df, i, onset, vowel, coda)
        elif char1 in can_aspirate and char2 in aspiration_markers:
            char2 = _update_markers(char2)
            _write_segments(df, i, char1 + char2, vowel, coda)
        elif char1 in aspiration_markers | glottal_markers:
            char1 = _update_markers(char1)
            _write_segments(df, i, char1 + char2, vowel, coda)
        elif char2 in medials_set:
            medial_seg.append(char1 + char2)
            _write_segments(df, i, char1, vowel, coda, M=char2)
        elif char1 in nasals:
            _write_segments(df, i, char2, vowel, coda, P='ʔ', R=char1)
        elif char1 in vowels:
            _write_segments(df, i, char2, vowel, coda, P='ʔ', R=char1)
        else:
            # cons + cons default
            _write_segments(df, i, char2, vowel, coda, P=char1, R='a')

    # Update medials from 2-segment onsets
    medials_list = list(set([x[-1] for x in medial_seg])) if medial_seg else []

    # --- Length 3 onsets ---
    len3_indices = df[df['_onset_len'] == 3].index
    for i in len3_indices:
        onset, vowel, coda = df.loc[i, parts_col]
        char1, char2, char3 = onset[0], onset[1], onset[-1]

        if char2 == '͡':
            # Tied affricate
            _write_segments(df, i, char1 + char3, vowel, coda)
        elif char3 in ['h', 'ʰ'] and char1 + char2 in affricates:
            char3 = _update_markers(char3)
            _write_segments(df, i, char1 + char2 + char3, vowel, coda)
        elif char1 + char2 in affricates and char3 in medials_set:
            _write_segments(df, i, char1 + char2, vowel, coda, M=char3)
        elif char1 in nasals and char2 + char3 in affricates:
            _write_segments(df, i, char2 + char3, vowel, coda, P='ʔ', R=char1)
        elif (char1 in can_aspirate and char2 in aspiration_markers
              and char3 in medials_set):
            char2 = _update_markers(char2)
            _write_segments(df, i, char1 + char2, vowel, coda, M=char3)
        elif (char1 in nasals and char2 in can_aspirate
              and char3 in aspiration_markers):
            char3 = _update_markers(char3)
            _write_segments(df, i, char2 + char3, vowel, coda, P='ʔ', R=char1)
        elif (char1 in aspiration_markers | glottal_markers
              and char2 + char3 in medial_seg):
            char1 = _update_markers(char1)
            _write_segments(df, i, char1 + char2, vowel, coda, M=char3)
        elif (char1 in nasals
              and char2 in aspiration_markers | glottal_markers):
            char2 = _update_markers(char2)
            _write_segments(df, i, char2 + char3, vowel, coda, P='ʔ', R=char1)
        elif (not any(x in vowels for x in [char1, char2, char3])
              and char1 in nasals and char3 in medials_set):
            _write_segments(df, i, char2, vowel, coda,
                            M=char3, P='ʔ', R=char1)
        elif char2 in vowels:
            _write_segments(df, i, char3, vowel, coda, P=char1, R=char2)
        elif char2 in cons_rimes:
            _write_segments(df, i, char3, vowel, coda, P=char1, R=char2)
        elif (not any(x in vowels for x in [char1, char2, char3])
              and char1 in can_aspirate and char2 in aspiration_markers):
            char2 = _update_markers(char2)
            _write_segments(df, i, char3, vowel, coda,
                            P=char1 + char2, R='a')
        elif (not any(x in vowels for x in [char1, char2, char3])
              and char2 in aspiration_markers | glottal_markers):
            char2 = _update_markers(char2)
            _write_segments(df, i, char2 + char3, vowel, coda,
                            P=char1, R='a')
        else:
            _write_segments(df, i, 'error', 'error', 'error',
                            M='error', P='error', R='error')

    # --- Length 4 onsets ---
    len4_indices = df[df['_onset_len'] == 4].index
    for i in len4_indices:
        onset, vowel, coda = df.loc[i, parts_col]
        char1, char2, char3, char4 = onset[0], onset[1], onset[2], onset[3]

        if char2 == '͡' and char4 in medials_set:
            _write_segments(df, i, char1 + char3, vowel, coda, M=char4)
        elif char1 in nasals and char3 == '͡':
            _write_segments(df, i, char2 + char4, vowel, coda,
                            P='ʔ', R=char1)
        elif (char1 in nasals and char2 + char3 in affricates
              and char4 in medials_set):
            _write_segments(df, i, char2 + char4, vowel, coda,
                            P='ʔ', R=char1)
        elif (char1 in nasals and char2 + char3 in affricates
              and char4 in aspiration_markers):
            char4 = _update_markers(char4)
            _write_segments(df, i, char2 + char3 + char4, vowel, coda,
                            P='ʔ', R=char1)
        elif (char1 + char2 in affricates and char3 in aspiration_markers
              and char4 in medials_set):
            char3 = _update_markers(char3)
            _write_segments(df, i, char1 + char2 + char3, vowel, coda,
                            M=char4)
        elif (char1 in nasals and char2 in can_aspirate
              and char3 in aspiration_markers and char4 in medials_set):
            char3 = _update_markers(char3)
            _write_segments(df, i, char2 + char3, vowel, coda,
                            M=char4, P='ʔ', R=char1)
        elif (char1 in nasals
              and char2 in aspiration_markers | glottal_markers
              and char4 in medials_set):
            char2 = _update_markers(char2)
            _write_segments(df, i, char2 + char3, vowel, coda,
                            M=char4, P='ʔ', R=char1)
        elif (char2 in vowels | cons_rimes and char3 in can_aspirate
              and char4 in aspiration_markers):
            char4 = _update_markers(char4)
            _write_segments(df, i, char3 + char4, vowel, coda,
                            P=char1, R=char2)
        elif (char2 in vowels | cons_rimes
              and char3 in aspiration_markers | glottal_markers):
            char3 = _update_markers(char3)
            _write_segments(df, i, char3 + char4, vowel, coda,
                            P=char1, R=char2)
        elif (char1 in can_aspirate and char2 in aspiration_markers
              and char3 in vowels | cons_rimes):
            char2 = _update_markers(char2)
            _write_segments(df, i, char4, vowel, coda,
                            P=char1 + char2, R=char3)
        elif (char2 in vowels | cons_rimes and char4 in medials_set):
            _write_segments(df, i, char3, vowel, coda,
                            M=char4, P=char1, R=char2)
        elif char2 in vowels and char3 in cons_rimes:
            _write_segments(df, i, char4, vowel, coda, P=char1, R=char3)
        elif char2 in ['r', 'ɾ', 'ɹ', 'l'] and char3 in vowels:
            _write_segments(df, i, char4, vowel, coda, P=char1, R=char2)
        elif (not any(x in vowels for x in [char1, char2, char3, char4])
              and char1 in can_aspirate and char2 in aspiration_markers
              and char4 in medials_set):
            char2 = _update_markers(char2)
            _write_segments(df, i, char3, vowel, coda,
                            M=char4, P=char1 + char2, R='a')
        elif (not any(x in vowels for x in [char1, char2, char3, char4])
              and char2 in can_aspirate and char3 in aspiration_markers
              and char4 in medials_set):
            char3 = _update_markers(char3)
            _write_segments(df, i, char2 + char3, vowel, coda,
                            M=char4, P=char1, R='a')
        elif (not any(x in vowels for x in [char1, char2, char3, char4])
              and char1 in aspiration_markers | glottal_markers
              and char4 in medials_set):
            char1 = _update_markers(char1)
            _write_segments(df, i, char3, vowel, coda,
                            M=char4, P=char1 + char2, R='a')
        elif (not any(x in vowels for x in [char1, char2, char3, char4])
              and char2 in aspiration_markers | glottal_markers
              and char4 in medials_set):
            char2 = _update_markers(char2)
            _write_segments(df, i, char2 + char3, vowel, coda,
                            M=char4, P=char1, R='a')
        else:
            _write_segments(df, i, 'error', 'error', 'error',
                            M='error', P='error', R='error')

    # --- Length 5 onsets (only with aspiration/glottalization diacritics) ---
    len5_indices = df[df['_onset_len'] == 5].index
    for i in len5_indices:
        onset, vowel, coda = df.loc[i, parts_col]
        c1, c2, c3, c4, c5 = onset[0], onset[1], onset[2], onset[3], onset[4]

        if not any(c in aspiration_markers | glottal_markers for c in onset):
            _write_segments(df, i, 'error', 'error', 'error',
                            M='error', P='error', R='error')
            continue

        # Tied affricate (c1͡c3) + aspiration + medial
        if (c2 == '͡' and c4 in aspiration_markers
                and c5 in medials_set):
            c4 = _update_markers(c4)
            _write_segments(df, i, c1 + c3 + c4, vowel, coda, M=c5)
        # Nasal + tied affricate (c2͡c4) + aspiration
        elif (c1 in nasals and c3 == '͡'
              and c5 in aspiration_markers):
            c5 = _update_markers(c5)
            _write_segments(df, i, c2 + c4 + c5, vowel, coda,
                            P='ʔ', R=c1)
        # Nasal + affricate + aspiration + medial
        elif (c1 in nasals and c2 + c3 in affricates
              and c4 in aspiration_markers and c5 in medials_set):
            c4 = _update_markers(c4)
            _write_segments(df, i, c2 + c3 + c4, vowel, coda,
                            M=c5, P='ʔ', R=c1)
        # Nasal + pre-asp/glot + affricate + medial
        elif (c1 in nasals
              and c2 in aspiration_markers | glottal_markers
              and c3 + c4 in affricates and c5 in medials_set):
            c2 = _update_markers(c2)
            _write_segments(df, i, c2 + c3 + c4, vowel, coda,
                            M=c5, P='ʔ', R=c1)
        # Presyllable + aspirated consonant + medial
        elif (c2 in vowels | cons_rimes and c3 in can_aspirate
              and c4 in aspiration_markers and c5 in medials_set):
            c4 = _update_markers(c4)
            _write_segments(df, i, c3 + c4, vowel, coda,
                            M=c5, P=c1, R=c2)
        # Presyllable + pre-asp/glot + consonant + medial
        elif (c2 in vowels | cons_rimes
              and c3 in aspiration_markers | glottal_markers
              and c5 in medials_set):
            c3 = _update_markers(c3)
            _write_segments(df, i, c3 + c4, vowel, coda,
                            M=c5, P=c1, R=c2)
        # Presyllable + affricate + aspiration
        elif (c2 in vowels | cons_rimes and c3 + c4 in affricates
              and c5 in aspiration_markers):
            c5 = _update_markers(c5)
            _write_segments(df, i, c3 + c4 + c5, vowel, coda,
                            P=c1, R=c2)
        # Aspirated presyllable + rime + consonant + medial
        elif (c1 in can_aspirate and c2 in aspiration_markers
              and c3 in vowels | cons_rimes and c5 in medials_set):
            c2 = _update_markers(c2)
            _write_segments(df, i, c4, vowel, coda,
                            M=c5, P=c1 + c2, R=c3)
        # Aspirated presyllable + rime + affricate
        elif (c1 in can_aspirate and c2 in aspiration_markers
              and c3 in vowels | cons_rimes and c4 + c5 in affricates):
            c2 = _update_markers(c2)
            _write_segments(df, i, c4 + c5, vowel, coda,
                            P=c1 + c2, R=c3)
        # Aspirated presyllable + rime + aspirated consonant
        elif (c1 in can_aspirate and c2 in aspiration_markers
              and c3 in vowels | cons_rimes and c4 in can_aspirate
              and c5 in aspiration_markers):
            c2 = _update_markers(c2)
            c5 = _update_markers(c5)
            _write_segments(df, i, c4 + c5, vowel, coda,
                            P=c1 + c2, R=c3)
        # No vowels: aspirated presyllable + affricate + medial
        elif (not any(x in vowels for x in [c1, c2, c3, c4, c5])
              and c1 in can_aspirate and c2 in aspiration_markers
              and c3 + c4 in affricates and c5 in medials_set):
            c2 = _update_markers(c2)
            _write_segments(df, i, c3 + c4, vowel, coda,
                            M=c5, P=c1 + c2, R='a')
        # No vowels: consonant + aspirated affricate + medial
        elif (not any(x in vowels for x in [c1, c2, c3, c4, c5])
              and c2 + c3 in affricates and c4 in aspiration_markers
              and c5 in medials_set):
            c4 = _update_markers(c4)
            _write_segments(df, i, c2 + c3 + c4, vowel, coda,
                            M=c5, P=c1, R='a')
        # No vowels: pre-asp/glot + consonant + affricate + medial
        elif (not any(x in vowels for x in [c1, c2, c3, c4, c5])
              and c1 in aspiration_markers | glottal_markers
              and c3 + c4 in affricates and c5 in medials_set):
            c1 = _update_markers(c1)
            _write_segments(df, i, c3 + c4, vowel, coda,
                            M=c5, P=c1 + c2, R='a')
        else:
            # Try presyllable split as fallback
            split = _try_presyllable_split(onset)
            if split:
                P, R, C, M = split
                _write_segments(df, i, C, vowel, coda, M=M, P=P, R=R)
            else:
                _write_segments(df, i, 'error', 'error', 'error',
                                M='error', P='error', R='error')

    # --- Length 6 onsets (only with aspiration/glottalization diacritics) ---
    len6_indices = df[df['_onset_len'] == 6].index
    for i in len6_indices:
        onset, vowel, coda = df.loc[i, parts_col]
        c1, c2, c3, c4, c5, c6 = (onset[0], onset[1], onset[2],
                                    onset[3], onset[4], onset[5])

        if not any(c in aspiration_markers | glottal_markers for c in onset):
            _write_segments(df, i, 'error', 'error', 'error',
                            M='error', P='error', R='error')
            continue

        # Nasal + tied affricate (c2͡c4) + aspiration + medial
        if (c1 in nasals and c3 == '͡'
                and c5 in aspiration_markers and c6 in medials_set):
            c5 = _update_markers(c5)
            _write_segments(df, i, c2 + c4 + c5, vowel, coda,
                            M=c6, P='ʔ', R=c1)
        # Presyllable + tied affricate (c3͡c5) + aspiration
        elif (c2 in vowels | cons_rimes and c4 == '͡'
              and c6 in aspiration_markers):
            c6 = _update_markers(c6)
            _write_segments(df, i, c3 + c5 + c6, vowel, coda,
                            P=c1, R=c2)
        # Aspirated presyllable + rime + tied affricate (c4͡c6)
        elif (c1 in can_aspirate and c2 in aspiration_markers
              and c3 in vowels | cons_rimes and c5 == '͡'):
            c2 = _update_markers(c2)
            _write_segments(df, i, c4 + c6, vowel, coda,
                            P=c1 + c2, R=c3)
        # Presyllable + affricate + aspiration + medial
        elif (c2 in vowels | cons_rimes and c3 + c4 in affricates
              and c5 in aspiration_markers and c6 in medials_set):
            c5 = _update_markers(c5)
            _write_segments(df, i, c3 + c4 + c5, vowel, coda,
                            M=c6, P=c1, R=c2)
        # Aspirated presyllable + rime + affricate + medial
        elif (c1 in can_aspirate and c2 in aspiration_markers
              and c3 in vowels | cons_rimes and c4 + c5 in affricates
              and c6 in medials_set):
            c2 = _update_markers(c2)
            _write_segments(df, i, c4 + c5, vowel, coda,
                            M=c6, P=c1 + c2, R=c3)
        # Aspirated presyllable + rime + aspirated consonant + medial
        elif (c1 in can_aspirate and c2 in aspiration_markers
              and c3 in vowels | cons_rimes and c4 in can_aspirate
              and c5 in aspiration_markers and c6 in medials_set):
            c2 = _update_markers(c2)
            c5 = _update_markers(c5)
            _write_segments(df, i, c4 + c5, vowel, coda,
                            M=c6, P=c1 + c2, R=c3)
        else:
            # Try presyllable split as fallback
            split = _try_presyllable_split(onset)
            if split:
                P, R, C, M = split
                _write_segments(df, i, C, vowel, coda, M=M, P=P, R=R)
            else:
                _write_segments(df, i, 'error', 'error', 'error',
                                M='error', P='error', R='error')

    # --- Length > 6 onsets ---
    len_gt6_indices = df[df['_onset_len'] > 6].index
    for i in len_gt6_indices:
        onset, vowel, coda = df.loc[i, parts_col]

        if not any(c in aspiration_markers | glottal_markers for c in onset):
            _write_segments(df, i, 'error', 'error', 'error',
                            M='error', P='error', R='error')
            continue

        split = _try_presyllable_split(onset)
        if split:
            P, R, C, M = split
            _write_segments(df, i, C, vowel, coda, M=M, P=P, R=R)
        else:
            _write_segments(df, i, 'error', 'error', 'error',
                            M='error', P='error', R='error')

    # Remove temporary columns
    df = df.drop(columns=[col for col in ['parts', '_onset_len']
                           if col in df.columns])

    return df


# =============================================================================
# Main entry point
# =============================================================================

def segment_words(
    df: pd.DataFrame,
    word_col: str = 'word',
) -> SegmentationResult:
    """
    Break individual words into phonological columns P, R, C, M, V, F, T.

    Non-IPA characters and other issues cause 'error' in segmentation columns
    without blocking the entire pipeline.

    Args:
        df: DataFrame with a word column to segment
        word_col: Name of the column containing individual words

    Returns:
        SegmentationResult with processed DataFrame
    """
    df = df.copy()

    # Step 1: Validate word column exists
    if word_col not in df.columns:
        return SegmentationResult(
            success=False,
            error=f"Word column '{word_col}' not found in database.",
        )

    # Check for NaN
    nan_count = df[word_col].isna().sum()
    if nan_count > 0:
        return SegmentationResult(
            success=False,
            error=f"Found {nan_count} empty values in '{word_col}' column. "
                  f"All words must have values.",
        )

    # Step 2: Clean word column
    df, cleaning_report = clean_transcription_column(df, word_col)

    # Check for empty words after cleaning
    empty_mask = df[word_col] == ''
    if empty_mask.any():
        return SegmentationResult(
            success=False,
            error=f"After cleaning, {empty_mask.sum()} words became empty. "
                  f"Please check your data.",
        )

    # Step 2b: Re-explode words that were split at tone boundaries
    # Cleaning may have inserted spaces at internal tone marks
    has_space = df[word_col].str.contains(' ', na=False)
    tone_splits = int(has_space.sum())
    if tone_splits > 0:
        df = (df
              .assign(**{word_col: df[word_col].str.split()})
              .explode(word_col)
              .reset_index(drop=True))

    # Step 3: Pre-scan for non-IPA characters -> mark error rows
    error_mask = pd.Series(False, index=df.index)
    error_words = {}  # word -> reason

    for idx, row in df.iterrows():
        word_text = str(row[word_col])

        # Check IPA characters
        bad_chars = check_ipa_characters(word_text)
        if bad_chars:
            error_mask.at[idx] = True
            chars_str = ', '.join(f"'{c}'" for c in sorted(bad_chars))
            error_words[word_text] = f"non-IPA characters: {chars_str}"
            continue

        # Check Chao numbers
        chao_error = validate_chao_numbers(word_text)
        if chao_error:
            error_mask.at[idx] = True
            error_words[word_text] = chao_error

    # Initialize seg columns for error rows
    seg_cols = ['P', 'R', 'C', 'M', 'V', 'F', 'T']
    for col in seg_cols:
        df[col] = ''

    # Mark error rows
    for col in seg_cols:
        df.loc[error_mask, col] = 'error'

    # Step 5-7: Process non-error rows through the pipeline
    good_mask = ~error_mask
    if good_mask.any():
        df_good = df.loc[good_mask].copy()

        # Extract tones
        df_good, tone_error = extract_tones(df_good, word_col)
        if tone_error:
            # Mark all remaining as error if tone system is invalid
            for col in seg_cols:
                df.loc[good_mask, col] = 'error'
            for idx in df_good.index:
                word_text = str(df.loc[idx, word_col])
                error_words[word_text] = tone_error
        else:
            # Update T column from good rows
            df.loc[good_mask, 'T'] = df_good['T']
            # Update word column (tones removed)
            df.loc[good_mask, word_col] = df_good[word_col]

            # Split around vowels
            df_good, _ = split_around_vowels(df_good, word_col)

            # Check for words that got error parts (no vowels)
            no_vowel_mask = df_good['parts'].apply(
                lambda p: isinstance(p, list) and p[0] == 'error'
            )
            if no_vowel_mask.any():
                for idx in df_good[no_vowel_mask].index:
                    word_text = str(df.loc[idx, word_col])
                    error_words[word_text] = "no vowels detected"
                    for col in seg_cols:
                        df.loc[idx, col] = 'error'

                # Remove no-vowel rows from good processing
                df_good = df_good[~no_vowel_mask].copy()

            # Process onsets for remaining good rows
            if len(df_good) > 0:
                df_processed = process_onsets(df_good, 'parts', word_col)

                # Copy results back
                for col in ['P', 'R', 'C', 'M', 'V', 'F']:
                    df.loc[df_processed.index, col] = df_processed[col]

                # Check for rows that process_onsets marked as error
                for idx in df_processed.index:
                    if df_processed.loc[idx, 'C'] == 'error':
                        word_text = str(df.loc[idx, word_col])
                        if word_text not in error_words:
                            error_words[word_text] = "unrecognizable onset pattern"

    # Build summary
    total_words = len(df)
    error_count = (df['C'] == 'error').sum()
    success_count = total_words - error_count

    summary = {
        "words_segmented": success_count,
        "error_count": error_count,
        "total_words": total_words,
        "error_words": error_words,
        "tone_splits": tone_splits,
    }

    return SegmentationResult(
        success=True,
        df=df,
        cleaning_report=cleaning_report,
        summary=summary,
    )
