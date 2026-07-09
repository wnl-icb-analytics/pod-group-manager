# =============================================================================
# POD Group Manager - Unmapped Queue (core workflow)
# =============================================================================

import pandas as pd
import streamlit as st
from services.unmapped_service import get_financial_years, get_unmapped, clear_unmapped_cache
from services.options_service import get_option_names
from services.mapping_service import upsert_mapping
from utils.helpers import num, money

UNMAPPED = "— unmapped —"      # per-row default: leave the row unmapped
CHOOSE = "— select group —"    # bulk control default: nothing chosen
COLS = [1.0, 1.0, 1.9, 1.9, 2.1, 1.8]


def _cell(v):
    """Render a component value, or a muted dash when empty (NULL)."""
    if v is None or (isinstance(v, float) and pd.isnull(v)):
        return ":grey[—]"
    return str(v)


def render_unmapped():
    st.subheader("Unmapped POD combinations")
    st.caption(
        "Combinations in the latest file per in-scope provider that have no POD group yet. "
        "Pick a group (and optional note) per row, then save."
    )

    # Rows this session has just mapped - hidden immediately so the user gets
    # instant feedback without waiting for the expensive view to recompute.
    resolved = st.session_state.setdefault("resolved_lookups", set())

    years = get_financial_years()
    if not years:
        st.success("✅ Nothing to map — every combination in the latest provider files has a POD group.")
        return

    c_fy, c_refresh = st.columns([4, 1], vertical_alignment="bottom")
    fy = c_fy.selectbox("Financial year", years, index=0)
    c_refresh.button("↻ Refresh", use_container_width=True, on_click=_refresh,
                     help="Reload from Snowflake (data is cached for 5 min).")

    df = get_unmapped(fy)
    if not df.empty and resolved:
        df = df[~df["POD_LOOKUP"].isin(resolved)]
    if df.empty:
        st.success(f"✅ No unmapped combinations for {fy}.")
        return

    options = get_option_names(active_only=True)
    if not options:
        st.error("No active POD group options. Add some on the Options page first.")
        return

    keys = df["POD_LOOKUP"].tolist()
    st.markdown(f"**{len(df)}** unmapped combination(s) for **{fy}** — choose a group, then Save.")

    # Bulk helper: many combinations share a group, so pre-fill all unset rows.
    b1, b2 = st.columns([3, 1], vertical_alignment="bottom")
    with b1:
        bulk_group = st.selectbox("Set all unset rows to", [CHOOSE] + options, key=f"bulk_{fy}")
    with b2:
        st.button(
            "Apply to unset", use_container_width=True,
            disabled=(bulk_group == CHOOSE),
            on_click=_bulk_apply, args=(fy, keys, bulk_group),
        )

    st.divider()

    # Assignment form: one native dropdown per row (single click to open)
    with st.form(f"assign_{fy}"):
        h = st.columns(COLS)
        for col, label in zip(h, ["POD code", "Local code", "Local description",
                                   "Volume · value", "POD group", "Note"]):
            col.caption(label)

        for _, r in df.iterrows():
            key = r["POD_LOOKUP"]
            with st.container(border=True):
                c = st.columns(COLS, vertical_alignment="center")
                c[0].markdown(_cell(r["POINT_OF_DELIVERY_CODE"]))
                c[1].markdown(_cell(r["LOCAL_POINT_OF_DELIVERY_CODE"]))
                c[2].markdown(_cell(r["LOCAL_POINT_OF_DELIVERY_DESCRIPTION"]))
                c[3].markdown(f"{int(r['RECORD_COUNT']):,} · :grey[{r['PROVIDERS']}]")
                c[3].caption(f"{money(r['ACTUAL_PRICE'])} · {num(r['ACTUAL_ACTIVITY'])} activity")
                c[4].selectbox("group", [UNMAPPED] + options, key=f"grp_{fy}_{key}", label_visibility="collapsed")
                c[5].text_input("note", key=f"note_{fy}_{key}", label_visibility="collapsed", placeholder="optional")

        submitted = st.form_submit_button("💾 Save assignments", type="primary")

    if submitted:
        _save(fy, df)


def _bulk_apply(fy, keys, group):
    """Pre-select a group for every row still left unmapped."""
    for key in keys:
        sk = f"grp_{fy}_{key}"
        if st.session_state.get(sk, UNMAPPED) == UNMAPPED:
            st.session_state[sk] = group


def _refresh():
    """Force a live reload: drop the cache and forget optimistic hides."""
    clear_unmapped_cache()
    st.session_state["resolved_lookups"] = set()


def _save(fy, df):
    options = get_option_names(active_only=True)
    ok, fail, done = 0, [], []
    with st.spinner("Saving…"):
        for _, r in df.iterrows():
            key = r["POD_LOOKUP"]
            group = st.session_state.get(f"grp_{fy}_{key}", UNMAPPED)
            if group not in options:
                continue
            note = st.session_state.get(f"note_{fy}_{key}") or None
            success, msg = upsert_mapping(
                _val(r["POINT_OF_DELIVERY_CODE"]),
                _val(r["LOCAL_POINT_OF_DELIVERY_CODE"]),
                _val(r["LOCAL_POINT_OF_DELIVERY_DESCRIPTION"]),
                group, note,
            )
            if success:
                ok += 1
                done.append(key)
            else:
                fail.append(f"{key}: {msg}")

    if fail:
        st.error("Some rows failed:\n\n" + "\n\n".join(fail))
    if not ok and not fail:
        st.info("No rows selected — choose a group for at least one row.")
    if ok:
        # Hide the saved rows now; the cached view stays warm so the rerun is
        # instant. The 5-min TTL (or ↻ Refresh) reconciles with Snowflake.
        st.session_state["resolved_lookups"].update(done)
        st.toast(f"✅ Assigned {ok} mapping(s).")
        st.rerun()


def _val(v):
    """Normalise a pandas cell to a plain str or None."""
    if v is None or (isinstance(v, float) and pd.isnull(v)):
        return None
    return str(v)
