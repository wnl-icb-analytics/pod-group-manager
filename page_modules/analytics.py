# =============================================================================
# POD Group Manager - Analytics (unmapped activity from the latest LSACM files)
# =============================================================================

import altair as alt
import streamlit as st
from services.analytics_service import (
    get_activity_years, get_unmapped_summary, get_unmapped_by_provider,
    get_recent_activity,
)
from utils.helpers import compact, format_time_ago

BLUE = "#1d4ed8"


def render_analytics():
    st.subheader("Unmapped analytics")
    st.caption("Activity, value and records still without a POD group, from the latest file per in-scope provider.")

    years = get_activity_years()
    if not years:
        st.info("No activity data available yet.")
        return
    fy = st.selectbox("Financial year", years, index=0)

    s = get_unmapped_summary(fy)
    if not s:
        return

    if s["records"] == 0:
        st.success(f"✅ Nothing unmapped for {fy} — every combination has a POD group.")
        _recent_changes()
        return

    c1, c2, c3 = st.columns(3)
    c1.metric("Actual activity", compact(s["activity"]))
    c2.metric("Actual value", compact(s["value"], "£"))
    c3.metric("Records", compact(s["records"]))

    p = get_unmapped_by_provider(fy)
    if p.empty:
        _recent_changes()
        return

    st.divider()
    st.markdown("**Unmapped value (£) by provider**")
    st.caption("Providers carrying unmapped cost. Most unmapped records have no price and are excluded here.")
    _hbar(p, "ACTUAL_PRICE", "Value (£)")

    _recent_changes()


def _recent_changes():
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


def _hbar(df, value_col, title, cat="PROVIDER_CODE"):
    """Horizontal bar sorted by value."""
    chart = (
        alt.Chart(df)
        .mark_bar(color=BLUE)
        .encode(
            x=alt.X(f"{value_col}:Q", title=title, axis=alt.Axis(format="~s")),
            y=alt.Y(f"{cat}:N", sort="-x", title=None),
            tooltip=[alt.Tooltip(f"{cat}:N", title=cat.replace("_", " ").title()),
                     alt.Tooltip(f"{value_col}:Q", title=title, format=",.0f")],
        )
        .properties(height=max(180, 26 * len(df)))
    )
    st.altair_chart(chart, use_container_width=True)
