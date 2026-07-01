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
| `V_LSACM_POD_GROUP` | Row-level LSACM (latest file, all providers) tagged with its `POD_GROUP` — every staging column, group by anything. |
| `V_UNMAPPED_PODS` | Combinations in the latest files with no POD group yet (the old *PGO Finder*). |
| `POD_GROUP_MAPPING` | Underlying mapping table. |
"""
    )

    st.markdown("#### The mappings")
    st.caption(
        "Look up any combination's group, or browse the full lookup. `POD_LOOKUP` is "
        "the three component codes concatenated, with `?` for nulls."
    )
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

    st.markdown("#### Plan vs actual by POD group")
    st.caption(
        "`V_LSACM_POD_GROUP` is row-level LSACM already tagged with `POD_GROUP` — no "
        "key-building needed. Group by any staging column (e.g. "
        "`ACTIVITY_TREATMENT_FUNCTION_CODE`, `COMMISSIONER_CODE`) and filter by period "
        "with the clean typed `DV_FINANCIAL_YEAR` / `DV_FINANCIAL_MONTH`."
    )
    st.code(
        "SELECT\n"
        "    POD_GROUP,\n"
        "    SUM(DV_ACTUAL_PRICE)                         AS actual_value,\n"
        "    SUM(DV_PLANNED_PRICE)                        AS planned_value,\n"
        "    SUM(DV_ACTUAL_PRICE) - SUM(DV_PLANNED_PRICE) AS variance\n"
        f"FROM {DB_SCHEMA}.V_LSACM_POD_GROUP\n"
        "WHERE DV_FINANCIAL_YEAR = '202627'\n"
        "GROUP BY 1\n"
        "ORDER BY variance DESC;",
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
