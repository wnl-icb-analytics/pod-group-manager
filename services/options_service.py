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


def set_orders(ordered_names):
    """Assign sort_order 1..N to options in the given order (single statement)."""
    if not ordered_names:
        return True, "nothing to do"
    try:
        values = ", ".join(f"({sql_str(n)}, {i})" for i, n in enumerate(ordered_names, start=1))
        conn.sql(
            f"""
            UPDATE {DB_SCHEMA}.POD_GROUP_OPTION t
            SET sort_order = v.ord
            FROM (VALUES {values}) AS v(name, ord)
            WHERE t.pod_group_name = v.name
            """
        ).collect()
        return True, "reordered"
    except Exception as e:
        return False, str(e)


def set_active(name, is_active):
    """Toggle an option's active flag."""
    try:
        active_sql = "TRUE" if is_active else "FALSE"
        conn.sql(
            f"UPDATE {DB_SCHEMA}.POD_GROUP_OPTION SET is_active = {active_sql} "
            f"WHERE pod_group_name = {sql_str(name)}"
        ).collect()
        return True, "updated"
    except Exception as e:
        return False, str(e)


def next_order():
    """Next sort_order value (max + 1), for appending a new option."""
    try:
        df = conn.sql(f"SELECT COALESCE(MAX(sort_order), 0) + 1 AS N FROM {DB_SCHEMA}.POD_GROUP_OPTION").to_pandas()
        return int(df.iloc[0]["N"]) if not df.empty else 1
    except Exception:
        return 1
