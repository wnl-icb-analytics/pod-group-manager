# =============================================================================
# POD Group Manager - Unmapped Queue (core workflow)
# =============================================================================

import altair as alt
import pandas as pd
import streamlit as st
from services.unmapped_service import (
    get_financial_years, get_unmapped,
    get_unmapped_summary, get_unmapped_value_by_provider,
)
from services.options_service import get_option_names
from services.mapping_service import upsert_mapping
from utils.helpers import compact

BLUE = "#1d4ed8"

UNMAPPED = "— unmapped —"      # per-row default: leave the row unmapped
CHOOSE = "— select group —"    # bulk control default: nothing chosen
COLS = [1.1, 1.1, 2, 1.4, 2.2, 2]


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

    years = get_financial_years()
    if not years:
        st.success("✅ Nothing to map — every combination in the latest provider files has a POD group.")
        return

    fy = st.selectbox("Financial year", years, index=0)
    df = get_unmapped(fy)
    if df.empty:
        st.success(f"✅ No unmapped combinations for {fy}.")
        return

    options = get_option_names(active_only=True)
    if not options:
        st.error("No active POD group options. Add some on the Options page first.")
        return

    # Headline totals for the unmapped rows only.
    s = get_unmapped_summary(fy)
    if s:
        m1, m2, m3 = st.columns(3)
        m1.metric("Actual activity", compact(s["activity"]))
        m2.metric("Actual value", compact(s["value"], "£"))
        m3.metric("Records", compact(s["records"]))

    prov = get_unmapped_value_by_provider(fy)
    if not prov.empty:
        st.markdown("**Unmapped value (£) by provider**")
        _provider_chart(prov)

    st.divider()

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
                                   "Records · provider", "POD group", "Note"]):
            col.caption(label)

        for _, r in df.iterrows():
            key = r["POD_LOOKUP"]
            with st.container(border=True):
                c = st.columns(COLS, vertical_alignment="center")
                c[0].markdown(_cell(r["POINT_OF_DELIVERY_CODE"]))
                c[1].markdown(_cell(r["LOCAL_POINT_OF_DELIVERY_CODE"]))
                c[2].markdown(_cell(r["LOCAL_POINT_OF_DELIVERY_DESCRIPTION"]))
                c[3].markdown(f"{int(r['RECORD_COUNT']):,} · :grey[{r['PROVIDERS']}]")
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


def _save(fy, df):
    options = get_option_names(active_only=True)
    ok, fail = 0, []
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
        else:
            fail.append(f"{key}: {msg}")

    if ok:
        st.success(f"✅ Assigned {ok} mapping(s).")
    if fail:
        st.error("Some rows failed:\n\n" + "\n\n".join(fail))
    if not ok and not fail:
        st.info("No rows selected — choose a group for at least one row.")
    if ok:
        st.rerun()


def _val(v):
    """Normalise a pandas cell to a plain str or None."""
    if v is None or (isinstance(v, float) and pd.isnull(v)):
        return None
    return str(v)


def _provider_chart(df):
    """Horizontal bar of unmapped value (£) per provider, sorted by value."""
    chart = (
        alt.Chart(df)
        .mark_bar(color=BLUE)
        .encode(
            x=alt.X("ACTUAL_PRICE:Q", title="Value (£)", axis=alt.Axis(format="~s")),
            y=alt.Y("PROVIDER_CODE:N", sort="-x", title=None),
            tooltip=[
                alt.Tooltip("PROVIDER_CODE:N", title="Provider"),
                alt.Tooltip("ACTUAL_PRICE:Q", title="Value (£)", format=",.0f"),
                alt.Tooltip("ACTUAL_ACTIVITY:Q", title="Activity", format=",.0f"),
                alt.Tooltip("RECORDS:Q", title="Records", format=",.0f"),
            ],
        )
        .properties(height=max(180, 26 * len(df)))
    )
    st.altair_chart(chart, use_container_width=True)
