# =============================================================================
# POD Group Manager - Unmapped Queue (core workflow)
# =============================================================================

import pandas as pd
import streamlit as st
from services.unmapped_service import get_financial_years, get_unmapped
from services.options_service import get_option_names
from services.mapping_service import upsert_mapping
from utils.helpers import display_component

ASSIGN_COL = "Assign group"
NOTES_COL = "Notes"


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

    st.markdown(f"**{len(df)}** unmapped combination(s) for **{fy}**")

    # Build editable grid: read-only context columns + two editable columns
    editor_df = pd.DataFrame({
        "POD lookup": df["POD_LOOKUP"],
        "POD code": df["POINT_OF_DELIVERY_CODE"].map(display_component),
        "Local code": df["LOCAL_POINT_OF_DELIVERY_CODE"].map(display_component),
        "Local description": df["LOCAL_POINT_OF_DELIVERY_DESCRIPTION"].map(display_component),
        "Records": df["RECORD_COUNT"],
        "Providers": df["PROVIDERS"],
        ASSIGN_COL: ["" for _ in range(len(df))],
        NOTES_COL: ["" for _ in range(len(df))],
    })

    edited = st.data_editor(
        editor_df,
        use_container_width=True,
        hide_index=True,
        disabled=["POD lookup", "POD code", "Local code", "Local description", "Records", "Providers"],
        column_config={
            "Records": st.column_config.NumberColumn(help="Lines in the latest provider files"),
            ASSIGN_COL: st.column_config.SelectboxColumn(
                options=[""] + options, required=False,
                help="Choose the POD group overview for this combination",
            ),
            NOTES_COL: st.column_config.TextColumn(help="Optional reason / context"),
        },
        key=f"unmapped_editor_{fy}",
    )

    # An unselected SelectboxColumn cell can come back as "" or NaN; treat both as blank
    assign = edited[ASSIGN_COL].fillna("").astype(str).str.strip()
    pending = edited[assign.isin(options)]
    st.caption(f"{len(pending)} row(s) ready to assign.")

    if st.button("💾 Save assignments", type="primary", disabled=pending.empty):
        ok, fail = 0, []
        # Map back to original component values (real NULLs) by POD lookup
        src = df.set_index("POD_LOOKUP")
        for _, row in pending.iterrows():
            key = row["POD lookup"]
            r = src.loc[key]
            success, msg = upsert_mapping(
                _val(r["POINT_OF_DELIVERY_CODE"]),
                _val(r["LOCAL_POINT_OF_DELIVERY_CODE"]),
                _val(r["LOCAL_POINT_OF_DELIVERY_DESCRIPTION"]),
                row[ASSIGN_COL],
                row[NOTES_COL] or None,
            )
            if success:
                ok += 1
            else:
                fail.append(f"{key}: {msg}")
        if ok:
            st.success(f"✅ Assigned {ok} mapping(s).")
        if fail:
            st.error("Some rows failed:\n\n" + "\n\n".join(fail))
        st.rerun()


def _val(v):
    """Normalise a pandas cell to a plain str or None."""
    if v is None or (isinstance(v, float) and pd.isnull(v)):
        return None
    return str(v)
