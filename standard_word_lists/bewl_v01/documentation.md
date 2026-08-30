# Big Excelerant Word List (BEWL) — Documentation

**Version 1.0 · English + Lao** *(word list released 29 August 2026; this
documentation revised 30 August 2026)*

Developers: Ryan Gehrmann & Zack Anderson

Adapted from the *EFEO‑CNRS‑SOAS Word List for Linguistic Fieldwork in
Southeast Asia* (Pain et al. 2022), <https://shs.hal.science/halshs-01068533>

This document accompanies the word list file `BEWL_v1.0.xlsx` and is part of
the BEWL's version record. It is written for the linguists and language
workers who will use the list, not for Excelerant's developers.

**All inquiries and feedback are welcome** at
<excelerant.linguistics@gmail.com>.

---

## 1. What the BEWL is

The BEWL is a large, semantically organized elicitation list built for
**efficiently audio‑recording lexical data** in Mainland Southeast Asia. Its
intended uses are language documentation, phonological analysis, and
orthography development.

Version 1.0 contains **1,886 entries**, each with:

- a unique numerical identifier;
- an **English gloss** and a **Lao gloss**;
- a place in a four‑level **semantic classification**;
- where applicable, a **cross‑reference** to the EFEO‑CNRS‑SOAS list.

The list is delivered as a single spreadsheet (`.xlsx`), one row per entry.
In Excelerant it is offered as a ready‑made "standard word list tool": the
user picks a gloss language (English or Lao) and Excelerant builds the
SpeechRecorder recording script directly, with no file preparation.

## 2. Why it exists — design rationale

The EFEO‑CNRS‑SOAS list is an excellent basis for recording large amounts of
lexical data. It is cross‑indexed to several historically important Southeast
Asian word lists, and it already includes a great deal of regionally relevant
vocabulary (culture, geography, flora, fauna, and so on).

Because that list was aggregated from many sources, however, its glossing
style is not uniform — and that unevenness is compounded once glosses are
translated into additional languages. The BEWL's central goal is a **more
standardized glossing style**: one that removes gloss ambiguity wherever
possible and elicits a **predictable word class**, assuming the target
language has an equivalent term.

To achieve this, the developers used the EFEO‑CNRS‑SOAS list as a starting
point but did not treat its wording as fixed. They edited English glosses,
removed redundant or regionally irrelevant entries, split ambiguous ones,
and added entries to broaden coverage. The guiding principle throughout is
**ease of use for the language consultant**: a participant should be able to
read a gloss in a language they know well and immediately understand what is
being asked for. The aim is smoother, faster elicitation sessions.

## 3. Relationship to the EFEO‑CNRS‑SOAS list

Version 1.0 was produced by revising **v4** of the EFEO‑CNRS‑SOAS list in
three areas.

### English glosses

- **Verbs are given a sample argument in parentheses** to fix the sense and
  the expected frame — e.g. *to cut (hand)*, *to throw (a stone)*, *to blow
  (the wind blows)*.
- **Abstract nouns were converted to verbs** where a verb is the more
  natural and less ambiguous target.
- **Entries with more than one referent were split.** For example, the
  single EFEO entry *shadow, shade* became two BEWL entries, *shadow* and
  *shade*.
- **New entries were added**, notably local flora (new in this revision) and
  fauna (added earlier, first published here).

### Lao glosses

- Existing Lao glosses were checked for accuracy and improved where needed.
- Lao glosses were supplied for entries that lacked them.
- All 1,886 v1.0 entries carry a Lao gloss. Some glosses record register or
  speaker‑sex information in parentheses — e.g. *ໂດຍ (ຜູ້ຊາຍເວົ້າ)* "yes
  (men's speech)".

See §12 for who prepared the Lao glosses.

### Semantic organization

- Classification was deepened from **one level to four** (not every entry is
  filled to the fourth level).
- The former **"Actions and States"** category was dissolved; its entries
  were redistributed into meaning‑based categories.

### The EFEO cross‑reference

The `index_efeo` column carries the source entry's number in the
EFEO‑CNRS‑SOAS list.

- **1,678 distinct EFEO entries** are represented in BEWL v1.0.
- Where one EFEO entry was split, or a BEWL entry was inserted next to a
  related EFEO entry, `index_efeo` uses **decimal notation** — e.g. EFEO
  entry 61 ("soil") corresponds to BEWL's *fertile soil* (61.1), *soil low
  in nutrients* (61.2), *red soil* (61.3), *gravelly soil* (61.4), *swelling
  soil* (61.5). 141 entries use this notation.
- One entry (BEWL 255, a catfish) is entirely new and has no EFEO number.

### Three generations of numbering

The word list has been renumbered twice, and every generation is preserved
so that older data and references stay usable:

| column | numbering | range |
|---|---|---|
| `index_efeo` | the original EFEO‑CNRS‑SOAS numbers | ~1–2900, with gaps |
| `index_v0` | the BEWL's first numbering | 1–1896 |
| `index` | the **current** (v1.0) BEWL numbering | 1–1886 |

`index` is the identifier to cite. If you hold recordings or notes keyed to
`index_v0`, the `index_v0` column is the crosswalk to the current numbers —
though a handful of `index_v0` items were dropped when v1.0 was finalized
and so have no row here.

## 4. Version 1.0 status at a glance

| | |
|---|---|
| Entries | 1,886 |
| Gloss languages | English, Lao (both complete for every entry) |
| EFEO entries incorporated | 1,678 of the source list |
| Top‑level semantic categories | 25 |
| Entries classified to level 3 or 4 | ~65% |
| Overall list order | not yet organized by frequency |
| Picture lookup | a Google Images link per entry |

Version 1.0 is a **working release**: the content is usable now, but the
frequency ordering and further semantic tuning are still outstanding.

## 5. The spreadsheet — column reference

One sheet, `word_list`; 1,886 data rows; 12 columns (columns below appear in
file order). For the canonical entry order, sort by `index`.

| column | contents |
|---|---|
| `index` | **Current BEWL entry number.** Unique, 1–1886, no gaps. The stable identifier — cite this. |
| `index_v0` | The BEWL's previous entry number (see §3). Blank for the one entry added after the renumber. |
| `index_efeo` | The entry's number in the EFEO‑CNRS‑SOAS list; decimal for splits/insertions (see §3); blank for the one wholly new entry. |
| `sem_cat_1_order` | Display rank of the top‑level category (see §6). Not a plain sequence — some values are decimals and a few integers are unused, reflecting categories that were merged or removed. |
| `sem_cat_1` | Top‑level semantic category (25 values — see §6). |
| `sem_cat_2` | Second‑level category. Filled for ~94% of entries. |
| `sem_cat_3` | Third‑level category. `-` where not subdivided this far. |
| `sem_cat_4` | Fourth‑level category. `-` where not subdivided this far. |
| `gloss_english` | English gloss (the elicitation prompt for English‑speaking consultants). |
| `gloss_lao` | Lao gloss. |
| `images` | An Excel `HYPERLINK` formula (shown as the word "images") that opens a Google Images search for the entry's English gloss. Present on every row. |
| `note` | Free‑text editorial notes on four entries (taxonomy clarifications, pending decisions). |

## 6. Semantic classification

Every entry has a top‑level category (`sem_cat_1`) and, for most, up to three
further levels of nesting (`sem_cat_2`–`sem_cat_4`). About 94% of entries
reach level 2 and roughly two‑thirds reach level 3 or 4. Where a branch is
not subdivided further, the deeper columns hold `-`.

The 25 top‑level categories, in their intended display order, with entry
counts:

| # | category | entries |
|---|---|---|
| 1 | natural environment | 166 |
| 2 | animals | 389 |
| 2.1 | numbers | 50 |
| 2.2 | time | 49 |
| 3 | plants | 315 |
| 4 | kinship | 147 |
| 5 | personal pronouns | 12 |
| 6 | society | 98 |
| 7 | religion and divination | 10 |
| 8 | coming / going | 59 |
| 9 | house / home | 111 |
| 10 | food and drink | 107 |
| 11 | personal care / clothes / adornment | 8 |
| 12 | human body | 126 |
| 13 | various | 43 |
| 15 | measures | 13 |
| 17 | directions | 8 |
| 18 | physical space | 15 |
| 19 | colours | 12 |
| 20 | interpersonal communication | 52 |
| 21 | cognition | 21 |
| 22 | emotion | 13 |
| 23 | manual labor, tools, and weapons | 32 |
| 24 | crafts (smithy, woodcraft…) | 26 |
| 25 | fabric and weaving | 4 |

Notes:

- **Animals** and **Plants** are the largest and most deeply structured
  categories. Animals branches by class (*mammals*, *birds*, *fish*,
  *insects*, *arachnids*, *molluscs*, *crustaceans*, *amphibians*,
  *reptiles*, *lizards*, *worms*, *parasites/pests*) plus *hunting*,
  *fishing*, and *general*. Plants branches largely by botanical family and
  by use (*rice*, *legumes*, *gourds*, *nightshades*, *leafy greens and
  herbs*, *aromatics*, *trees*, *agriculture*, and so on).
- The gaps and decimals in the category numbering (no 14 or 16; *numbers* and
  *time* sit at 2.1 and 2.2) are a trace of reorganization, including the
  removal of the "Actions and States" category. The numbering is a sort key,
  not a fixed taxonomy.
- Level‑3/4 organization is uneven by design and is still being refined.

## 7. Glossing conventions — quick reference for users

**English:**

- A verb gloss may be followed by a parenthesized argument or scenario that
  fixes its sense: *to cut (hand)*, *to set (the sun sets)*, *to recede (of
  flood water)*. Elicit the verb, not the parenthetical. About 46% of
  entries carry a parenthetical of some kind.
- Plants and animals often carry a scientific name — a binomial
  (*Panthera tigris*), a genus (*Genus: dendrocitta*), or a family
  (*Family: bagridae*) — to disambiguate folk terms. Around 205 entries do
  this.
- A leading parenthetical, e.g. *(polite for men)*, marks an entry whose
  gloss is a **usage note** rather than a headword — typically particles and
  politeness markers. There are seven such entries, and they are being
  reworked.

**Lao:**

- Parentheses in a Lao gloss carry the same kind of sense‑fixing or
  register/speaker information as in the English.

## 8. Frequency ordering (planned)

Version 1.0 keeps the entries in semantic‑category order; they are **not**
ordered by how basic or common a word is. A frequency/importance ordering is
planned for a future version, and it is what will define the nested SEWL and
MEWL subsets described in §9. Early ranking work exists but is kept outside
this file.

## 9. Planned subsets — SEWL and MEWL

The BEWL is designed to be the largest of a nested family of three lists.
Two shorter lists are planned for a future version:

- **SEWL — Small Excelerant Word List** (~200 items). The most essential
  vocabulary: enough for a rapid survey or a first recording session.
- **MEWL — Medium Excelerant Word List** (~1,000 items). A middle option
  for projects that want good coverage without committing to the full list.

The three lists will be **strictly nested**: every SEWL item is also in the
MEWL and the BEWL, and every MEWL item is also in the BEWL. This is achieved
by ordering: the SEWL items sit at the top of the MEWL and the BEWL, and the
MEWL items sit at the top of the BEWL. A researcher can therefore take "the
first 200" or "the first 1,000" entries and get a coherent, balanced list —
and data collected with a shorter list stays directly comparable to data
collected with a longer one.

The item selections for the SEWL and the MEWL have not yet been made. In
Excelerant, the SEWL and MEWL will appear as their own word list tools
alongside the BEWL.

## 10. Known limitations in version 1.0

- **List order is not yet meaningful.** Entries are grouped by semantic
  category but not ordered by frequency or importance within or across
  categories.
- **Semantic levels 3–4 are uneven** and still being tuned; some branches
  are much more developed than others.
- **Seven entries are glossed only by a usage note** (see §7) and need
  proper headwords or reclassification. Four of these collide as apparent
  duplicates — they are the polite "yes" and "no" particles for men's and
  women's speech.
- **Only English and Lao are implemented.** Burmese glosses are planned for
  version 2.

None of these block use of the list; they are the work items for subsequent
versions. (A pass for stray whitespace, mistyped punctuation, and clear
English typos was completed for this release, and the near‑duplicate entries
identified during review have been resolved.)

## 11. Roadmap

Planned for future versions (from the developers' working notes):

1. **Add Burmese glosses** (version 2).
2. Refine the semantic classification, especially at levels 3 and 4.
3. Rank the whole list by frequency/importance and select the nested
   **SEWL (~200)** and **MEWL (~1,000)** subsets (see §9).
4. Resolve the usage‑note entries; continue proofreading.
5. Add further gloss languages beyond English, Lao, and Burmese.
6. **Cross‑reference other established word lists** — Swadesh 100,
   Swadesh 200, MSEA 436, and others — so entries can be filtered to any of
   them, as the BEWL already is to the EFEO‑CNRS‑SOAS list. Suggestions of
   lists to include, or offers to help with the mapping, are welcome at
   <excelerant.linguistics@gmail.com>.

## 12. Acknowledgments — gloss translation

Each gloss language is overseen by a translator working with native‑speaker
consultants. Contributors will be added to this section as languages are
added.

### Lao

The Lao glosses were prepared by **Zack Anderson**, who revised the
EFEO‑CNRS‑SOAS Lao glosses for accuracy and clarity and developed new Lao
glosses for the items added to the BEWL. This work was carried out in
consultation with native Lao speakers **Mr. K** and **Mr. B**. *(The
pseudonyms are intentional.)*

### Burmese

*Planned for version 2. The Burmese translator and consultants will be
acknowledged here.*

## 13. Citation and attribution

When using the BEWL, please credit both the BEWL and its source:

> Gehrmann, Ryan & Zack Anderson. 2026. *Big Excelerant Word List (BEWL) for
> Lexical Data Collection in Mainland Southeast Asia*, version 1.0.

> Pain, Frédéric et al. 2022. *EFEO‑CNRS‑SOAS Word List for Linguistic
> Fieldwork in Southeast Asia*. <https://shs.hal.science/halshs-01068533>

## 14. AI use declaration

This documentation guide was largely composed by **Claude** (Anthropic's AI
assistant) under the direction and review of Ryan Gehrmann, working from the
word list file, the developers' notes, and Ryan's guidance.

**Artificial intelligence was not used in the development of the BEWL
itself.** The selection and editing of entries, the English and Lao glosses,
the semantic classification, and the cross‑referencing to the EFEO‑CNRS‑SOAS
list are the work of the human developers and consultants named in this
document.

## 15. Version history

### 1.0 — 29 August 2026

First release. 1,886 entries with complete English and Lao glosses; four‑level
semantic classification; EFEO‑CNRS‑SOAS cross‑referencing (`index_efeo`);
one Google Images link per entry. Based on a revision of EFEO‑CNRS‑SOAS list
v4.

As it was finalized the word list was renumbered (the previous numbering is
kept as `index_v0`), the glosses were lightly copy‑edited, duplicate entries
flagged in review were merged, and development‑only columns were removed —
leaving the 12 columns documented in §5. This documentation was completed
30 August 2026.
