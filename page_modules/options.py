# =============================================================================
# POD Group Manager - Options (manage the dropdown values)
# =============================================================================

import pandas as pd
import streamlit as st
from services.options_service import (
    get_options, upsert_option, set_orders, set_active, next_order,
)


def render_options():
    st.subheader("POD group options")
    st.caption(
        "Values in the assignment dropdown. Reorder with ↑ / ↓ (numbers re-sequence automatically); "
        "deactivate to hide a value without losing history."
    )

    df = get_options(active_only=False).reset_index(drop=True)
    names = df["POD_GROUP_NAME"].tolist() if not df.empty else []

    if not df.empty:
        if st.button("↕️ Tidy numbering (1…N)", help="Re-sequence sort order to remove gaps"):
            ok, msg = set_orders(names)
            (st.success if ok else st.error)(msg)
            st.rerun()

        h = st.columns([5, 1, 1.6, 1.6], vertical_alignment="bottom")
        h[0].caption("POD group")
        h[1].caption("Order")
        h[2].caption("Reorder")
        h[3].caption("Status")

        last = len(df) - 1
        for i, row in df.iterrows():
            name = row["POD_GROUP_NAME"]
            active = bool(row["IS_ACTIVE"])
            order = row["SORT_ORDER"]
            c = st.columns([5, 1, 1.6, 1.6], vertical_alignment="center")
            c[0].markdown(name if active else f":grey[{name} · inactive]")
            c[1].markdown("—" if pd.isnull(order) else str(int(order)))
            with c[2]:
                u, d = st.columns(2)
                u.button("↑", key=f"up_{name}", disabled=(i == 0),
                         on_click=_move, args=(names, i, -1), use_container_width=True)
                d.button("↓", key=f"down_{name}", disabled=(i == last),
                         on_click=_move, args=(names, i, 1), use_container_width=True)
            with c[3]:
                if active:
                    st.button("Deactivate", key=f"deact_{name}",
                              on_click=set_active, args=(name, False), use_container_width=True)
                else:
                    st.button("Activate", key=f"act_{name}", type="primary",
                              on_click=set_active, args=(name, True), use_container_width=True)

    st.divider()
    st.markdown("### Add an option")
    st.caption("New options are added to the end of the list — reorder with ↑ / ↓ above.")
    with st.form("option_form"):
        new_name = st.text_input("POD group name")
        submitted = st.form_submit_button("💾 Add option", type="primary")
        if submitted:
            if not new_name.strip():
                st.error("Name is required.")
            else:
                ok, msg = upsert_option(new_name.strip(), next_order(), True)
                (st.success if ok else st.error)(msg)
                if ok:
                    st.rerun()


def _move(names, i, delta):
    """Swap a row with its neighbour and re-sequence 1..N."""
    j = i + delta
    reordered = list(names)
    reordered[i], reordered[j] = reordered[j], reordered[i]
    set_orders(reordered)
