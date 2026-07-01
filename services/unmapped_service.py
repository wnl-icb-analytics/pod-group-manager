# =============================================================================
# POD Group Manager - Unmapped Detection Service
# =============================================================================

import pandas as pd
import streamlit as st
from database import get_connection, sql_str
from config import DB_SCHEMA

conn = get_connection()


def get_financial_years():
    """Distinct financial years that currently have unmapped combinations."""
    try:
        df = conn.sql(
            f"SELECT DISTINCT FINANCIAL_YEAR FROM {DB_SCHEMA}.V_UNMAPPED_PODS ORDER BY FINANCIAL_YEAR DESC"
        ).to_pandas()
        return df["FINANCIAL_YEAR"].tolist() if not df.empty else []
    except Exception as e:
        st.error(f"Error loading financial years: {e}")
        return []


def get_unmapped(financial_year=None):
    """Unmapped combinations, optionally filtered to one financial year."""
    try:
        where = f"WHERE FINANCIAL_YEAR = {sql_str(financial_year)}" if financial_year else ""
        return conn.sql(
            f"""
            SELECT FINANCIAL_YEAR, POD_LOOKUP, POINT_OF_DELIVERY_CODE,
                   LOCAL_POINT_OF_DELIVERY_CODE, LOCAL_POINT_OF_DELIVERY_DESCRIPTION,
                   RECORD_COUNT, PROVIDER_COUNT, PROVIDERS
            FROM {DB_SCHEMA}.V_UNMAPPED_PODS
            {where}
            ORDER BY RECORD_COUNT DESC, POD_LOOKUP
            """
        ).to_pandas()
    except Exception as e:
        st.error(f"Error loading unmapped combinations: {e}")
        return pd.DataFrame()
