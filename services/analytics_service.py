# =============================================================================
# POD Group Manager - Analytics Service (activity from latest LSACM files)
# =============================================================================

import pandas as pd
import streamlit as st
from database import get_connection, sql_str
from config import DB_SCHEMA

conn = get_connection()


def get_activity_years():
    try:
        df = conn.sql(
            f"SELECT DISTINCT FINANCIAL_YEAR FROM {DB_SCHEMA}.V_POD_ACTIVITY ORDER BY FINANCIAL_YEAR DESC"
        ).to_pandas()
        return df["FINANCIAL_YEAR"].tolist() if not df.empty else []
    except Exception as e:
        st.error(f"Error loading financial years: {e}")
        return []


def _where(fy):
    return f"WHERE FINANCIAL_YEAR = {sql_str(fy)}" if fy else ""


def get_unmapped_summary(fy=None):
    """Activity, value and record totals for unmapped rows only."""
    try:
        df = conn.sql(
            f"""
            SELECT SUM(ACTUAL_ACTIVITY) AS ACTIVITY,
                   SUM(ACTUAL_PRICE)    AS VALUE,
                   SUM(RECORD_COUNT)    AS RECORDS
            FROM {DB_SCHEMA}.V_POD_ACTIVITY
            {_where(fy)}{' AND' if fy else 'WHERE'} NOT IS_MAPPED
            """
        ).to_pandas()
        r = df.iloc[0]
        return {
            "activity": float(r["ACTIVITY"] or 0),
            "value": float(r["VALUE"] or 0),
            "records": float(r["RECORDS"] or 0),
        }
    except Exception as e:
        st.error(f"Error loading unmapped summary: {e}")
        return {}


def get_unmapped_by_provider(fy=None):
    """Unmapped value, activity and records per provider."""
    try:
        return conn.sql(
            f"""
            SELECT PROVIDER_CODE,
                   SUM(ACTUAL_PRICE)    AS ACTUAL_PRICE,
                   SUM(ACTUAL_ACTIVITY) AS ACTUAL_ACTIVITY,
                   SUM(RECORD_COUNT)    AS RECORDS
            FROM {DB_SCHEMA}.V_POD_ACTIVITY
            {_where(fy)}{' AND' if fy else 'WHERE'} NOT IS_MAPPED
            GROUP BY PROVIDER_CODE
            HAVING SUM(ACTUAL_PRICE) <> 0
            ORDER BY ACTUAL_PRICE DESC NULLS LAST
            """
        ).to_pandas()
    except Exception as e:
        st.error(f"Error loading unmapped value by provider: {e}")
        return pd.DataFrame()


def get_recent_activity(limit=15):
    """Recent mapping changes (audit trail)."""
    try:
        return conn.sql(
            f"""
            SELECT change_type, pod_lookup, old_value, new_value, changed_by, changed_at
            FROM {DB_SCHEMA}.POD_GROUP_MAPPING_CHANGES
            ORDER BY changed_at DESC
            LIMIT {int(limit)}
            """
        ).to_pandas()
    except Exception as e:
        st.error(f"Error loading recent activity: {e}")
        return pd.DataFrame()
