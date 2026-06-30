# =============================================================================
# POD Group Manager - Unmapped Queue (core workflow)
# =============================================================================

import pandas as pd
import streamlit as st
from services.unmapped_service import get_financial_years, get_unmapped
from services.options_service import get_option_names
from services.mapping_service import upsert_mapping
from utils.helpers import display_component

SKIP = "— skip —"


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

    keys = df["POD_LOOKUP"].tolist()
    st.markdown(f"**{len(df)}** unmapped combination(s) for **{fy}** — choose a group, then Save.")

    # Bulk helper: many combinations share a group, so pre-fill all unset rows.
    b1, b2 = st.columns([3, 1])
    with b1:
        bulk_group = st.selectbox("Set all unset rows to", [SKIP] + options, key=f"bulk_{fy}")
    with b2:
        st.markdown("<br>", unsafe_allow_html=True)
        st.button(
            "Apply to unset", use_container_width=True,
            disabled=(bulk_group == SKIP),
            on_click=_bulk_apply, args=(fy, keys, bulk_group),
        )

    # Assignment form: one native dropdown per row (single click to open)
    with st.form(f"assign_{fy}"):
        h = st.columns([3, 1.4, 2, 2])
        h[0].caption("Combination (POD / local / description)")
        h[1].caption("Records · providers")
        h[2].caption("POD group")
        h[3].caption("Note")

        for _, r in df.iterrows():
            key = r["POD_LOOKUP"]
            c = st.columns([3, 1.4, 2, 2])
            with c[0]:
                st.markdown(
                    f"{display_component(r['POINT_OF_DELIVERY_CODE'])} / "
                    f"{display_component(r['LOCAL_POINT_OF_DELIVERY_CODE'])} / "
                    f"{display_component(r['LOCAL_POINT_OF_DELIVERY_DESCRIPTION'])}"
                )
                st.caption(key)
            c[1].markdown(f"{int(r['RECORD_COUNT']):,}  \n`{r['PROVIDERS']}`")
            c[2].selectbox("group", [SKIP] + options, key=f"grp_{fy}_{key}", label_visibility="collapsed")
            c[3].text_input("note", key=f"note_{fy}_{key}", label_visibility="collapsed", placeholder="optional")

        submitted = st.form_submit_button("💾 Save assignments", type="primary")

    if submitted:
        _save(fy, df)


def _bulk_apply(fy, keys, group):
    """Pre-select a group for every row still left unset."""
    for key in keys:
        sk = f"grp_{fy}_{key}"
        if st.session_state.get(sk, SKIP) == SKIP:
            st.session_state[sk] = group


def _save(fy, df):
    options = get_option_names(active_only=True)
    ok, fail = 0, []
    for _, r in df.iterrows():
        key = r["POD_LOOKUP"]
        group = st.session_state.get(f"grp_{fy}_{key}", SKIP)
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
