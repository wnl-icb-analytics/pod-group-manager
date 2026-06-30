# =============================================================================
# POD Group Manager - Database Connection
# =============================================================================

import pandas as pd
import streamlit as st


@st.cache_resource
def get_connection():
    """Active Snowpark session inside Streamlit-in-Snowflake."""
    from snowflake.snowpark.context import get_active_session
    return get_active_session()


def rerun():
    if hasattr(st, "rerun"):
        st.rerun()
    else:
        st.experimental_rerun()


def current_actor():
    """Email of the signed-in Streamlit user, uppercased; '' if unavailable."""
    try:
        actor = st.user.get("email") if hasattr(st, "user") else None
    except Exception:
        actor = None
    return (actor or "").upper()


def sql_str(value):
    """Render a Python value as a SQL literal (NULL or escaped quoted string)."""
    # Treat None and any pandas missing value (NaN, NA, NaT) as SQL NULL
    try:
        if value is None or pd.isna(value):
            return "NULL"
    except (TypeError, ValueError):
        pass
    return "'" + str(value).replace("'", "''") + "'"
