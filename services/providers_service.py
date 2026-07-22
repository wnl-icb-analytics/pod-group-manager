# =============================================================================
# POD Group Manager - Providers Service (in-scope provider codes)
# =============================================================================
# Providers feed V_LATEST_FILES, so every change here alters what unmapped
# detection scans - each write clears the cached unmapped reads.

import pandas as pd
import streamlit as st
from database import get_connection, current_actor, sql_str
from services.unmapped_service import clear_unmapped_cache
from config import DB_SCHEMA

conn = get_connection()


def get_providers(active_only=False):
    """In-scope providers with names resolved from the org dictionary."""
    try:
        where = "WHERE is_active = TRUE" if active_only else ""
        return conn.sql(
            f"""
            SELECT provider_code, provider_name, is_active
            FROM {DB_SCHEMA}.V_POD_PROVIDER
            {where}
            ORDER BY provider_code
            """
        ).to_pandas()
    except Exception as e:
        st.error(f"Error loading providers: {e}")
        return pd.DataFrame()


def upsert_provider(code, is_active=True):
    """Add a provider, or update an existing one's active flag."""
    try:
        actor = current_actor()
        active_sql = "TRUE" if is_active else "FALSE"
        res = conn.sql(
            f"CALL {DB_SCHEMA}.UPSERT_POD_PROVIDER("
            f"{sql_str(code)}, {active_sql}, {sql_str(actor)})"
        ).to_pandas()
        msg = str(res.iloc[0, 0]) if not res.empty else ""
        ok = msg.startswith("SUCCESS")
        if ok:
            clear_unmapped_cache()
        return ok, msg
    except Exception as e:
        return False, str(e)


def set_provider_active(code, is_active):
    """Toggle a provider's active flag, leaving its name alone."""
    try:
        active_sql = "TRUE" if is_active else "FALSE"
        conn.sql(
            f"UPDATE {DB_SCHEMA}.POD_GROUP_PROVIDER SET is_active = {active_sql} "
            f"WHERE provider_code = {sql_str(code)}"
        ).collect()
        clear_unmapped_cache()
        return True, "updated"
    except Exception as e:
        return False, str(e)


def delete_provider(code):
    """Remove a provider outright (for codes added by mistake)."""
    try:
        res = conn.sql(
            f"CALL {DB_SCHEMA}.DELETE_POD_PROVIDER({sql_str(code)})"
        ).to_pandas()
        msg = str(res.iloc[0, 0]) if not res.empty else ""
        ok = msg.startswith("SUCCESS")
        if ok:
            clear_unmapped_cache()
        return ok, msg
    except Exception as e:
        return False, str(e)
