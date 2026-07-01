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


def get_activity_summary(fy=None):
    """Headline totals plus the mapped / unmapped split of activity."""
    try:
        df = conn.sql(
            f"""
            SELECT
                SUM(RECORD_COUNT)                              AS RECORDS,
                SUM(ACTUAL_ACTIVITY)                           AS ACTIVITY,
                SUM(ACTUAL_PRICE)                              AS PRICE,
                SUM(IFF(IS_MAPPED, ACTUAL_ACTIVITY, 0))        AS MAPPED_ACTIVITY,
                SUM(IFF(NOT IS_MAPPED, ACTUAL_ACTIVITY, 0))    AS UNMAPPED_ACTIVITY,
                SUM(IFF(NOT IS_MAPPED, RECORD_COUNT, 0))       AS UNMAPPED_RECORDS
            FROM {DB_SCHEMA}.V_POD_ACTIVITY
            {_where(fy)}
            """
        ).to_pandas()
        r = df.iloc[0]
        activity = float(r["ACTIVITY"] or 0)
        mapped = float(r["MAPPED_ACTIVITY"] or 0)
        return {
            "records": float(r["RECORDS"] or 0),
            "activity": activity,
            "price": float(r["PRICE"] or 0),
            "mapped_activity": mapped,
            "unmapped_activity": float(r["UNMAPPED_ACTIVITY"] or 0),
            "unmapped_records": float(r["UNMAPPED_RECORDS"] or 0),
            "mapped_pct": (mapped / activity * 100) if activity else 100.0,
        }
    except Exception as e:
        st.error(f"Error loading activity summary: {e}")
        return {}


def get_activity_by_group(fy=None):
    try:
        return conn.sql(
            f"""
            SELECT
                POD_GROUP,
                SUM(RECORD_COUNT)     AS RECORDS,
                SUM(ACTUAL_ACTIVITY)  AS ACTUAL_ACTIVITY,
                SUM(PLANNED_ACTIVITY) AS PLANNED_ACTIVITY,
                SUM(ACTUAL_PRICE)     AS ACTUAL_PRICE
            FROM {DB_SCHEMA}.V_POD_ACTIVITY
            {_where(fy)}
            GROUP BY POD_GROUP
            ORDER BY ACTUAL_ACTIVITY DESC NULLS LAST
            """
        ).to_pandas()
    except Exception as e:
        st.error(f"Error loading activity by group: {e}")
        return pd.DataFrame()


def get_activity_by_provider(fy=None):
    try:
        return conn.sql(
            f"""
            SELECT
                PROVIDER_CODE,
                SUM(ACTUAL_ACTIVITY) AS ACTUAL_ACTIVITY,
                SUM(ACTUAL_PRICE)    AS ACTUAL_PRICE,
                SUM(RECORD_COUNT)    AS RECORDS
            FROM {DB_SCHEMA}.V_POD_ACTIVITY
            {_where(fy)}
            GROUP BY PROVIDER_CODE
            ORDER BY ACTUAL_ACTIVITY DESC NULLS LAST
            """
        ).to_pandas()
    except Exception as e:
        st.error(f"Error loading activity by provider: {e}")
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
