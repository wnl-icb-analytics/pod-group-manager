# =============================================================================
# POD Group Manager - Existing Mappings (search, edit, history)
# =============================================================================

import streamlit as st
from services.mapping_service import (
    get_all_mappings, update_mapping_group, delete_mapping, get_mapping_changes,
)
from services.options_service import get_option_names
from utils.helpers import format_time_ago


def render_mappings():
    st.subheader("Existing mappings")

    df = get_all_mappings()
    if df.empty:
        st.info("No mappings yet. Assign some on the Unmapped page.")
        return

    options = get_option_names(active_only=True)

    # --- Search / filter -------------------------------------------------
    c1, c2 = st.columns([3, 2])
    with c1:
        term = st.text_input("Search", placeholder="code, description or POD group…",
                             label_visibility="collapsed")
    with c2:
        group_filter = st.selectbox("Filter by group", ["All groups"] + options)

    view = df.copy()
    if term:
        t = term.lower()
        mask = (
            view["POD_LOOKUP"].str.lower().str.contains(t, na=False)
            | view["POINT_OF_DELIVERY_CODE"].astype(str).str.lower().str.contains(t, na=False)
            | view["LOCAL_POINT_OF_DELIVERY_CODE"].astype(str).str.lower().str.contains(t, na=False)
            | view["LOCAL_POINT_OF_DELIVERY_DESCRIPTION"].astype(str).str.lower().str.contains(t, na=False)
            | view["POD_GROUP_OVERVIEW_MASTER"].astype(str).str.lower().str.contains(t, na=False)
        )
        view = view[mask]
    if group_filter != "All groups":
        view = view[view["POD_GROUP_OVERVIEW_MASTER"] == group_filter]

    st.caption(f"Showing {len(view)} of {len(df)} mapping(s)")
    st.dataframe(
        view[[
            "POD_LOOKUP", "POINT_OF_DELIVERY_CODE", "LOCAL_POINT_OF_DELIVERY_CODE",
            "LOCAL_POINT_OF_DELIVERY_DESCRIPTION", "POD_GROUP_OVERVIEW_MASTER",
            "UPDATED_BY", "UPDATED_AT",
        ]],
        use_container_width=True, hide_index=True,
    )

    st.divider()

    # --- Edit a single mapping ------------------------------------------
    st.markdown("### Edit a mapping")
    if view.empty:
        st.info("No rows match the filter.")
        return

    keys = view["POD_LOOKUP"].tolist()
    selected = st.selectbox("Mapping", keys, format_func=_labeller(view))
    row = view[view["POD_LOOKUP"] == selected].iloc[0]

    current_group = row["POD_GROUP_OVERVIEW_MASTER"]
    idx = options.index(current_group) if current_group in options else 0

    e1, e2 = st.columns([2, 3])
    with e1:
        new_group = st.selectbox("POD group", options, index=idx)
    with e2:
        notes = st.text_input("Reason for change", value="")

    b1, b2, _ = st.columns([1, 1, 3])
    with b1:
        if st.button("💾 Update", type="primary",
                     disabled=(new_group == current_group)):
            ok, msg = update_mapping_group(selected, new_group, notes or None)
            (st.success if ok else st.error)(msg)
            if ok:
                st.rerun()
    with b2:
        if st.button("🗑️ Delete"):
            st.session_state["confirm_delete"] = selected
            st.rerun()

    if st.session_state.get("confirm_delete") == selected:
        st.warning(f"Delete mapping `{selected}` ({current_group})? This cannot be undone.")
        d1, d2, _ = st.columns([1, 1, 3])
        with d1:
            if st.button("Yes, delete"):
                ok, msg = delete_mapping(selected)
                (st.success if ok else st.error)(msg)
                st.session_state.pop("confirm_delete", None)
                if ok:
                    st.rerun()
        with d2:
            if st.button("Cancel"):
                st.session_state.pop("confirm_delete", None)
                st.rerun()

    # --- History --------------------------------------------------------
    with st.expander("Change history for this mapping"):
        hist = get_mapping_changes(selected)
        if hist.empty:
            st.caption("No recorded changes.")
        else:
            hist = hist.copy()
            hist["WHEN"] = hist["CHANGED_AT"].map(format_time_ago)
            st.dataframe(
                hist[["CHANGE_TYPE", "OLD_VALUE", "NEW_VALUE", "NOTES", "CHANGED_BY", "WHEN"]],
                use_container_width=True, hide_index=True,
            )


def _labeller(view):
    desc = dict(zip(view["POD_LOOKUP"], view["POD_GROUP_OVERVIEW_MASTER"]))
    return lambda k: f"{k}  →  {desc.get(k, '')}"
