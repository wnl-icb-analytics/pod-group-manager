# =============================================================================
# POD Group Manager - SQL reference (how to query the mappings natively)
# =============================================================================

import streamlit as st
from config import DB_SCHEMA


def render_reference():
    st.subheader("Querying in SQL")
    st.caption(
        f"Everything lives in `{DB_SCHEMA}`. Query it from any Snowflake worksheet "
        "with a role that can read the schema (ANALYST or above). The mapping table "
        "here replaces the old `ANALYST_MANAGED.FA__MONTHLY_WNL_POD_GROUP_OVERVIEW` lookup."
    )

    st.markdown("#### Objects")
    st.markdown(
        """
| Object | What it is |
| --- | --- |
| `V_POD_GROUP_OVERVIEW` | Current mappings — each `POD_LOOKUP` and its `POD_GROUP_OVERVIEW_MASTER`. |
| `V_POD_ACTIVITY` | Activity from the latest file per in-scope provider, already joined to the mappings and grouped by POD group. |
| `V_UNMAPPED_PODS` | Combinations in the latest files with no POD group yet (the old *PGO Finder*). |
| `POD_GROUP_MAPPING` | Underlying mapping table — the join target for your own queries. |
"""
    )

    st.markdown("#### The mappings")
    st.caption("Look up any combination's group, or browse the full lookup.")
    st.code(
        f"SELECT *\n"
        f"FROM {DB_SCHEMA}.V_POD_GROUP_OVERVIEW\n"
        f"ORDER BY POD_LOOKUP;",
        language="sql",
    )

    st.markdown("#### Activity by POD group")
    st.caption(
        "`V_POD_ACTIVITY` already does the join and scopes to the latest file per "
        "in-scope provider — quickest way to grouped totals."
    )
    st.code(
        "SELECT POD_GROUP,\n"
        "       SUM(ACTUAL_ACTIVITY) AS actual_activity,\n"
        "       SUM(ACTUAL_PRICE)    AS actual_value,\n"
        "       SUM(RECORD_COUNT)    AS records\n"
        f"FROM {DB_SCHEMA}.V_POD_ACTIVITY\n"
        "WHERE FINANCIAL_YEAR = '202627'\n"
        "GROUP BY POD_GROUP\n"
        "ORDER BY actual_activity DESC;",
        language="sql",
    )

    st.markdown("#### Add POD groups to your own query")
    st.caption(
        "The join key `POD_LOOKUP` is the three component codes concatenated, with "
        "`?` for nulls. Build the same key and LEFT JOIN to the mapping table; "
        "`COALESCE` labels anything not yet mapped. Scope `LSACM` yourself "
        "(e.g. via `V_LATEST_FILES`) — a raw join spans every file."
    )
    st.code(
        "SELECT\n"
        "    COALESCE(m.POD_GROUP_OVERVIEW_MASTER, '(unmapped)') AS pod_group,\n"
        "    SUM(L.CONTRACT_MONITORING_ACTUAL_ACTIVITY)          AS actual_activity\n"
        "FROM DATA_LAKE.SDL.LSACM L\n"
        f"LEFT JOIN {DB_SCHEMA}.POD_GROUP_MAPPING m\n"
        "    ON CONCAT(\n"
        "         IFNULL(L.POINT_OF_DELIVERY_CODE, '?'),\n"
        "         IFNULL(L.LOCAL_POINT_OF_DELIVERY_CODE, '?'),\n"
        "         IFNULL(L.LOCAL_POINT_OF_DELIVERY_DESCRIPTION, '?')\n"
        "       ) = m.POD_LOOKUP\n"
        "GROUP BY 1\n"
        "ORDER BY actual_activity DESC;",
        language="sql",
    )

    st.markdown("#### What still needs mapping")
    st.caption("Combinations in the latest files with no POD group — assign these on the Unmapped tab.")
    st.code(
        f"SELECT *\n"
        f"FROM {DB_SCHEMA}.V_UNMAPPED_PODS\n"
        "WHERE FINANCIAL_YEAR = '202627';",
        language="sql",
    )
