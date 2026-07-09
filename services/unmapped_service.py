# =============================================================================
# POD Group Manager - Unmapped Detection Service
# =============================================================================

import pandas as pd
import streamlit as st
from database import get_connection, sql_str
from config import DB_SCHEMA

conn = get_connection()


@st.cache_data(ttl=300, show_spinner=False)
def get_financial_years():
    """Distinct financial years that currently have unmapped combinations.

    Cached (5 min) - the view scans the 600M-row LSACM staging table, so an
    uncached call costs ~15s. Call clear_unmapped_cache() after a write to
    force a fresh read.
    """
    try:
        df = conn.sql(
            f"SELECT DISTINCT FINANCIAL_YEAR FROM {DB_SCHEMA}.V_UNMAPPED_PODS ORDER BY FINANCIAL_YEAR DESC"
        ).to_pandas()
        return df["FINANCIAL_YEAR"].tolist() if not df.empty else []
    except Exception as e:
        st.error(f"Error loading financial years: {e}")
        return []


@st.cache_data(ttl=300, show_spinner="Loading unmapped combinations…")
def get_unmapped(financial_year=None):
    """Unmapped combinations, optionally filtered to one financial year.

    Cached (5 min) - the view scans the 600M-row LSACM staging table (~23s
    uncached). Call clear_unmapped_cache() after a write to force a refresh.
    """
    try:
        where = f"WHERE FINANCIAL_YEAR = {sql_str(financial_year)}" if financial_year else ""
        return conn.sql(
            f"""
            SELECT FINANCIAL_YEAR, POD_LOOKUP, POINT_OF_DELIVERY_CODE,
                   LOCAL_POINT_OF_DELIVERY_CODE, LOCAL_POINT_OF_DELIVERY_DESCRIPTION,
                   RECORD_COUNT, ACTUAL_ACTIVITY, ACTUAL_PRICE, PROVIDER_COUNT, PROVIDERS
            FROM {DB_SCHEMA}.V_UNMAPPED_PODS
            {where}
            ORDER BY RECORD_COUNT DESC, POD_LOOKUP
            """
        ).to_pandas()
    except Exception as e:
        st.error(f"Error loading unmapped combinations: {e}")
        return pd.DataFrame()


def clear_unmapped_cache():
    """Drop the cached unmapped queries so the next read hits Snowflake."""
    get_financial_years.clear()
    get_unmapped.clear()
