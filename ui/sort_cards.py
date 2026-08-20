"""
ui/sort_cards.py
Screen for digital, in-app card sorting (Orthography Development).
"""

import streamlit as st

from tasks import parse_uid_list, find_card_index_by_uid, generate_single_card_html, build_cards
from ui.navigation import go_back_to_menu
from ui.generate_cards import _render_filter_and_card_content_config


def _clear_sort_cards_state():
    """Remove all Sort Cards session-state, including per-pile widget keys."""
    for pile_id in st.session_state.get("_sc_pile_ids", []):
        label_key = f"_sc_pile_label_{pile_id}"
        if label_key in st.session_state:
            del st.session_state[label_key]

    for key in [
        "_sc_started",
        "_sc_entry_method",
        "_sc_active_index_col",
        "_sc_active_sub_index_col",
        "_sc_active_line_columns",
        "_sc_deck",
        "_sc_current_card",
        "_sc_pile_ids",
        "_sc_pile_cards",
        "_sc_next_pile_id",
        "_sc_filter_epoch",
        "_sc_begin_error",
    ]:
        if key in st.session_state:
            del st.session_state[key]


def _sc_add_pile():
    """Create a new empty pile with a default 'Pile N' label."""
    pile_id = st.session_state._sc_next_pile_id
    st.session_state._sc_pile_ids.append(pile_id)
    st.session_state._sc_pile_cards[pile_id] = []
    st.session_state[f"_sc_pile_label_{pile_id}"] = f"Pile {pile_id}"
    st.session_state._sc_next_pile_id = pile_id + 1


def _sc_advance_card(skip: bool = False):
    """Pop the next card from the deck into current_card. If skip, the
    current card is sent to the back of the deck first."""
    if skip and st.session_state._sc_current_card is not None:
        st.session_state._sc_deck.append(st.session_state._sc_current_card)
    if st.session_state._sc_deck:
        st.session_state._sc_current_card = st.session_state._sc_deck.pop(0)
    else:
        st.session_state._sc_current_card = None


def _sc_assign_current_to_pile(pile_id):
    """Assign the current card to a pile and advance to the next card."""
    card = st.session_state._sc_current_card
    if card is None:
        return
    st.session_state._sc_pile_cards[pile_id].append(card)
    _sc_advance_card()


def _sc_return_card_to_deck(card):
    """Return a card removed from a pile back to the end of the deck."""
    st.session_state._sc_deck.append(card)
    if st.session_state._sc_current_card is None:
        _sc_advance_card()


def _sc_quick_add(pile_id, uid_text: str) -> list[str]:
    """Assign every UID in uid_text (comma/space/newline separated) to
    pile_id, checking the current card first, then the remaining deck.
    Returns the UIDs that couldn't be matched (already sorted, or invalid)."""
    not_found = []
    for uid in parse_uid_list(uid_text):
        current = st.session_state._sc_current_card
        if current is not None and current.index_display == uid:
            st.session_state._sc_pile_cards[pile_id].append(current)
            _sc_advance_card()
            continue
        idx = find_card_index_by_uid(st.session_state._sc_deck, uid)
        if idx is not None:
            card = st.session_state._sc_deck.pop(idx)
            st.session_state._sc_pile_cards[pile_id].append(card)
        else:
            not_found.append(uid)
    return not_found


@st.dialog("Pile Contents")
def _sc_pile_details_dialog(pile_id):
    """Modal listing every card in a pile, each individually removable
    back to the deck."""
    label = st.session_state.get(f"_sc_pile_label_{pile_id}", f"Pile {pile_id}")
    st.subheader(label)

    cards = st.session_state._sc_pile_cards.get(pile_id, [])
    if not cards:
        st.info("No cards in this pile yet.")
        return

    for i, card in enumerate(cards):
        detail_col1, detail_col2 = st.columns([4, 1])
        with detail_col1:
            st.markdown(f"**{card.index_display}** — {' / '.join(card.lines)}")
        with detail_col2:
            if st.button("Remove", key=f"_sc_detail_remove_{pile_id}_{i}"):
                removed = st.session_state._sc_pile_cards[pile_id].pop(i)
                _sc_return_card_to_deck(removed)
                st.rerun()


def _sc_pile_preview_text(pile_id, max_items: int = 5) -> str:
    """Build a short preview string for a pile's quick-reference box,
    showing the first cards placed in it, in placement order.

    Deliberately the *first* N rather than the most recent N: once a pile
    has more than max_items cards, this keeps showing the same early
    cards as a steady point of comparison, rather than sliding to show
    whatever was just added.
    """
    cards = st.session_state._sc_pile_cards.get(pile_id, [])
    if not cards:
        return ""
    shown = cards[:max_items]
    lines = [f"{card.index_display} — {' / '.join(card.lines)}" for card in shown]
    if len(cards) > max_items:
        lines.append(f"... and {len(cards) - max_items} more")
    return "\n".join(lines)


def _sc_remove_pile(pile_id):
    """Remove a pile entirely, returning every card it held to the deck."""
    cards = st.session_state._sc_pile_cards.pop(pile_id, [])
    st.session_state._sc_deck.extend(cards)
    st.session_state._sc_pile_ids.remove(pile_id)
    label_key = f"_sc_pile_label_{pile_id}"
    if label_key in st.session_state:
        del st.session_state[label_key]
    if st.session_state._sc_current_card is None and st.session_state._sc_deck:
        _sc_advance_card()


def _render_sort_cards_pile(pile_id):
    """Render one pile's mini-card: editable name, count, preview, add/view/quick-add."""
    with st.container(border=True):
        name_col, remove_col = st.columns([5, 1])
        with name_col:
            st.text_input(
                "Pile name",
                key=f"_sc_pile_label_{pile_id}",
                label_visibility="collapsed",
            )
        with remove_col:
            if st.button("✕", key=f"_sc_remove_pile_{pile_id}", use_container_width=True, help="Remove this pile (cards return to the deck)"):
                _sc_remove_pile(pile_id)
                st.rerun()

        cards = st.session_state._sc_pile_cards.get(pile_id, [])
        st.caption(f"{len(cards)} card(s)")

        st.text_area(
            "Preview",
            value=_sc_pile_preview_text(pile_id),
            key=f"_sc_pile_preview_{pile_id}",
            height=100,
            disabled=True,
            label_visibility="collapsed",
        )

        current_card = st.session_state._sc_current_card
        if st.button(
            "Add Card",
            key=f"_sc_add_{pile_id}",
            use_container_width=True,
            type="primary",
            disabled=current_card is None,
        ):
            _sc_assign_current_to_pile(pile_id)
            st.rerun()

        if st.button(
            "View All",
            key=f"_sc_view_{pile_id}",
            use_container_width=True,
            disabled=not cards,
        ):
            _sc_pile_details_dialog(pile_id)

        epoch_key = f"_sc_quickadd_epoch_{pile_id}"
        if epoch_key not in st.session_state:
            st.session_state[epoch_key] = 0
        epoch = st.session_state[epoch_key]

        quick_uid = st.text_input(
            "Quick add",
            key=f"_sc_quickadd_{pile_id}_{epoch}",
            placeholder="UID(s)",
            label_visibility="collapsed",
            help="Paste one or more UIDs (comma/space/newline separated) to assign them to this pile directly.",
        )
        if st.button(
            "Quick Add",
            key=f"_sc_quickadd_btn_{pile_id}",
            use_container_width=True,
            disabled=not quick_uid.strip(),
        ):
            not_found = _sc_quick_add(pile_id, quick_uid)
            st.session_state[epoch_key] = epoch + 1
            if not_found:
                st.session_state[f"_sc_quickadd_error_{pile_id}"] = not_found
            else:
                st.session_state.pop(f"_sc_quickadd_error_{pile_id}", None)
            st.rerun()

        quickadd_not_found = st.session_state.get(f"_sc_quickadd_error_{pile_id}")
        if quickadd_not_found:
            st.caption(f"Not found (already sorted or invalid): {', '.join(quickadd_not_found)}")


def _render_sort_cards_active():
    """The active sorting screen: current card, controls, and the piles grid."""
    current_card = st.session_state._sc_current_card
    deck = st.session_state._sc_deck

    top_col1, top_col2 = st.columns([3, 1])
    with top_col1:
        remaining = len(deck) + (1 if current_card is not None else 0)
        st.markdown(f"**Cards remaining:** {remaining}")
    with top_col2:
        if st.button("Back to Main Menu", use_container_width=True, key="_sc_active_back"):
            _clear_sort_cards_state()
            go_back_to_menu()

    st.caption("Progress isn't saved automatically yet in this stage -- returning to the main menu will lose it.")

    st.markdown("---")

    if current_card is not None:
        st.markdown(generate_single_card_html(current_card), unsafe_allow_html=True)

        control_col1, control_col2 = st.columns(2)
        with control_col1:
            if st.button("Skip Card", use_container_width=True):
                _sc_advance_card(skip=True)
                st.rerun()
        with control_col2:
            if st.button("+ Add Pile", use_container_width=True, key="_sc_add_pile_active"):
                _sc_add_pile()
                st.rerun()
    else:
        st.success("Sorting complete! Every card has been assigned to a pile.")
        if st.button("+ Add Pile", use_container_width=True, key="_sc_add_pile_done"):
            _sc_add_pile()
            st.rerun()
        st.info("Saving and exporting results is coming in the next stage.")

    st.markdown("---")
    st.markdown("**Piles**")

    pile_ids = st.session_state._sc_pile_ids
    piles_per_row = 4
    for row_start in range(0, len(pile_ids), piles_per_row):
        row_ids = pile_ids[row_start:row_start + piles_per_row]
        pile_cols = st.columns(len(row_ids))
        for pile_col, pile_id in zip(pile_cols, row_ids):
            with pile_col:
                _render_sort_cards_pile(pile_id)


def _render_sort_cards_setup(df, columns):
    """Pre-sort configuration: choose New Sort vs Load Prepared Activity,
    then (for New Sort) the same filter + card content steps as Generate
    Cards, ending in a "Begin Sort" button that builds the deck."""
    config_col, output_col = st.columns([1, 2])

    with config_col:
        st.subheader("Method")

        if "_sc_entry_method" not in st.session_state:
            st.session_state._sc_entry_method = "new"

        def _method_pill(label: str):
            st.markdown(
                f'<div style="padding:0.5rem 1rem;border-radius:0.5rem;'
                f'background-color:#2E7D32;color:white;text-align:center;'
                f'font-weight:600;">{label}</div>',
                unsafe_allow_html=True,
            )

        method_col1, method_col2 = st.columns(2)
        with method_col1:
            if st.session_state._sc_entry_method == "new":
                _method_pill("New Sort")
            elif st.button("New Sort", use_container_width=True):
                st.session_state._sc_entry_method = "new"
                st.rerun()
        with method_col2:
            if st.session_state._sc_entry_method == "load":
                _method_pill("Load Prepared Activity")
            else:
                st.button(
                    "Load Prepared Activity",
                    use_container_width=True,
                    disabled=True,
                    help="Coming soon",
                )

        st.markdown("---")

        if st.session_state._sc_entry_method == "new":
            filtered_df, index_col, sub_index_col, line_columns, sort_by_col, selected_filters = (
                _render_filter_and_card_content_config(
                    df, columns, key_prefix="sc", filter_epoch_key="_sc_filter_epoch"
                )
            )

            st.markdown("---")
            st.subheader("Step 3: Begin")

            can_begin = len(filtered_df) > 0 and len(line_columns) > 0

            begin_clicked = st.button(
                "Begin Sort",
                type="primary",
                use_container_width=True,
                disabled=not can_begin,
            )

            if not can_begin:
                if len(filtered_df) == 0:
                    st.caption("No rows match your current filters.")
                else:
                    st.caption("Select at least one card line above.")

            if begin_clicked:
                build_result = build_cards(
                    df=filtered_df,
                    index_col=index_col,
                    sub_index_col=sub_index_col,
                    line_columns=line_columns,
                    sort_by_col=sort_by_col,
                )
                if build_result.success:
                    st.session_state._sc_active_index_col = index_col
                    st.session_state._sc_active_sub_index_col = sub_index_col
                    st.session_state._sc_active_line_columns = line_columns
                    st.session_state._sc_deck = list(build_result.cards)
                    st.session_state._sc_current_card = None
                    st.session_state._sc_pile_ids = []
                    st.session_state._sc_pile_cards = {}
                    st.session_state._sc_next_pile_id = 1
                    for _ in range(3):
                        _sc_add_pile()
                    _sc_advance_card()
                    st.session_state._sc_begin_error = None
                    st.session_state._sc_started = True
                    st.rerun()
                else:
                    st.session_state._sc_begin_error = build_result
                    st.rerun()

            if st.session_state.get("_sc_begin_error"):
                error_result = st.session_state._sc_begin_error
                st.error(f"**Error:** {error_result.error}")
                if error_result.duplicate_indices:
                    st.markdown("**Duplicate values:**")
                    for dup in error_result.duplicate_indices[:20]:
                        st.text(f"  {dup}")
                    if len(error_result.duplicate_indices) > 20:
                        st.text(f"  ... and {len(error_result.duplicate_indices) - 20} more")
        else:
            st.info("Loading a prepared activity file is coming soon.")

        st.markdown("")

        if st.button("Back to Main Menu", use_container_width=True, key="_sc_setup_back"):
            _clear_sort_cards_state()
            go_back_to_menu()

    with output_col:
        st.subheader("Output")

        if st.session_state._sc_entry_method == "new":
            st.markdown("**About Sort Cards**")
            st.markdown(
                """
                This task lets you sort cards digitally, one at a time, instead of printing
                them -- handy when printing isn't practical, or when handing a sorting task
                off to someone else.

                1. **Filter** and **Card Content** work exactly like Generate Cards -- narrow
                   down the rows, then pick what shows on each card.
                2. **Begin Sort** opens the sorting screen with a starting set of blank piles.
                   Rename piles as you like, add more, and assign each card as it comes up.
                3. When you're finished (or want to pause), you'll export a results file --
                   Sort Cards never writes to the database directly. Bring that file into
                   Process Cards to write the results in.
                """
            )
        else:
            st.markdown("**About Loading a Prepared Activity**")
            st.markdown(
                "Upload a sorting-activity JSON (from Generate Cards, or from a previous Sort "
                "Cards session) to skip configuration and jump straight into sorting with the "
                "filter, card content, and any in-progress piles already set up."
            )


def screen_sort_cards():
    """Screen for digital, in-app card sorting (Orthography Development)."""
    st.title("Sort Cards")
    st.markdown("---")

    df = st.session_state.database
    columns = list(df.columns)

    if not st.session_state.get("_sc_started"):
        # Add vertical divider CSS (matches other task screens' two-column setup layout)
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
        _render_sort_cards_setup(df, columns)
    else:
        _render_sort_cards_active()
