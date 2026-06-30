# =============================================================================
# POD Group Manager - Options Service (dropdown values)
# =============================================================================

import pandas as pd
import streamlit as st
from database import get_connection, current_actor, sql_str
from config import DB_SCHEMA

conn = get_connection()


def get_options(active_only=True):
    """Return POD group options ordered by sort_order."""
    try:
        where = "WHERE is_active = TRUE" if active_only else ""
        df = conn.sql(
            f"""
            SELECT pod_group_name, sort_order, is_active
            FROM {DB_SCHEMA}.POD_GROUP_OPTION
            {where}
            ORDER BY sort_order, pod_group_name
            """
        ).to_pandas()
        return df
    except Exception as e:
        st.error(f"Error loading options: {e}")
        return pd.DataFrame()


def get_option_names(active_only=True):
    df = get_options(active_only)
    return df["POD_GROUP_NAME"].tolist() if not df.empty else []


def upsert_option(name, sort_order, is_active):
    try:
        actor = current_actor()
        active_sql = "TRUE" if is_active else "FALSE"
        order_sql = "NULL" if sort_order is None else str(int(sort_order))
        res = conn.sql(
            f"CALL {DB_SCHEMA}.UPSERT_POD_OPTION({sql_str(name)}, {order_sql}, {active_sql}, {sql_str(actor)})"
        ).to_pandas()
        msg = str(res.iloc[0, 0]) if not res.empty else ""
        return msg.startswith("SUCCESS"), msg
    except Exception as e:
        return False, str(e)
