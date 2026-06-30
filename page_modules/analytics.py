# =============================================================================
# POD Group Manager - Analytics
# =============================================================================

import streamlit as st
from services.analytics_service import get_summary, get_group_counts, get_recent_activity
from utils.helpers import format_time_ago


def render_analytics():
    st.subheader("Analytics")

    s = get_summary()
    c1, c2, c3 = st.columns(3)
    c1.metric("Total mappings", f"{s['mappings']:,}")
    c2.metric("POD groups in use", s["groups_used"])
    c3.metric("Unmapped backlog", f"{s['unmapped']:,}")

    st.divider()

    st.markdown("### Mappings per POD group")
    counts = get_group_counts()
    if not counts.empty:
        chart = counts.set_index("POD_GROUP")["MAPPING_COUNT"]
        st.bar_chart(chart)
        st.dataframe(counts, use_container_width=True, hide_index=True)
    else:
        st.caption("No mappings yet.")

    st.divider()

    st.markdown("### Recent activity")
    recent = get_recent_activity(25)
    if recent.empty:
        st.caption("No activity recorded yet.")
    else:
        recent = recent.copy()
        recent["WHEN"] = recent["CHANGED_AT"].map(format_time_ago)
        st.dataframe(
            recent[["CHANGE_TYPE", "POD_LOOKUP", "OLD_VALUE", "NEW_VALUE", "CHANGED_BY", "WHEN"]],
            use_container_width=True, hide_index=True,
        )
