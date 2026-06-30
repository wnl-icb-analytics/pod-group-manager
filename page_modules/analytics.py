# =============================================================================
# POD Group Manager - Analytics (activity from the latest LSACM files)
# =============================================================================

import altair as alt
import pandas as pd
import streamlit as st
from services.analytics_service import (
    get_activity_years, get_activity_summary, get_activity_by_group,
    get_activity_by_provider, get_recent_activity,
)
from utils.helpers import num, money, compact, format_time_ago

UNMAPPED_LABEL = "(unmapped)"
BLUE = "#1d4ed8"
RED = "#ef4444"


def render_analytics():
    st.subheader("Analytics")
    st.caption("Actual activity and value by POD group, from the latest file per in-scope provider.")

    years = get_activity_years()
    if not years:
        st.info("No activity data available yet.")
        return
    fy = st.selectbox("Financial year", years, index=0)

    s = get_activity_summary(fy)
    if not s:
        return

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Actual activity", compact(s["activity"]))
    c2.metric("Actual value", compact(s["price"], "£"))
    c3.metric("Records", compact(s["records"]))
    c4.metric("Activity mapped", f"{s['mapped_pct']:.1f}%")

    if s["unmapped_activity"] > 0:
        st.warning(
            f"⚠️ {num(s['unmapped_activity'])} activity across {num(s['unmapped_records'])} "
            f"record(s) is still unmapped — assign it on the **Unmapped** tab."
        )

    g = get_activity_by_group(fy)
    if g.empty:
        return

    st.divider()
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("**Actual activity by POD group**")
        _hbar(g, "ACTUAL_ACTIVITY", "Activity")
    with col_b:
        st.markdown("**Actual value (£) by POD group**")
        _hbar(g, "ACTUAL_PRICE", "Value (£)")

    st.divider()
    st.markdown("**Actual activity by provider**")
    p = get_activity_by_provider(fy)
    if not p.empty:
        _hbar(p, "ACTUAL_ACTIVITY", "Activity", cat="PROVIDER_CODE")

    st.divider()
    st.markdown("**Detail by POD group**")
    detail = pd.DataFrame({
        "POD group": g["POD_GROUP"],
        "Records": g["RECORDS"].map(num),
        "Actual activity": g["ACTUAL_ACTIVITY"].map(num),
        "Planned activity": g["PLANNED_ACTIVITY"].map(num),
        "Actual value": g["ACTUAL_PRICE"].map(money),
    })
    st.dataframe(detail, hide_index=True, use_container_width=True)

    with st.expander("Recent mapping changes"):
        recent = get_recent_activity(15)
        if recent.empty:
            st.caption("No changes recorded yet.")
        else:
            recent = recent.copy()
            recent["WHEN"] = recent["CHANGED_AT"].map(format_time_ago)
            st.dataframe(
                recent[["CHANGE_TYPE", "POD_LOOKUP", "OLD_VALUE", "NEW_VALUE", "CHANGED_BY", "WHEN"]],
                hide_index=True, use_container_width=True,
            )


def _hbar(df, value_col, title, cat="POD_GROUP"):
    """Horizontal bar sorted by value; the unmapped bar is highlighted red."""
    color = (
        alt.condition(alt.datum[cat] == UNMAPPED_LABEL, alt.value(RED), alt.value(BLUE))
        if cat == "POD_GROUP" else alt.value(BLUE)
    )
    chart = (
        alt.Chart(df)
        .mark_bar()
        .encode(
            x=alt.X(f"{value_col}:Q", title=title, axis=alt.Axis(format="~s")),
            y=alt.Y(f"{cat}:N", sort="-x", title=None),
            color=color,
            tooltip=[alt.Tooltip(f"{cat}:N", title=cat.replace("_", " ").title()),
                     alt.Tooltip(f"{value_col}:Q", title=title, format=",.0f")],
        )
        .properties(height=max(220, 26 * len(df)))
    )
    st.altair_chart(chart, use_container_width=True)
