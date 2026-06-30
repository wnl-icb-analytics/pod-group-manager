# =============================================================================
# POD Group Manager - Mapping Service (master mappings + audit)
# =============================================================================

import pandas as pd
import streamlit as st
from database import get_connection, current_actor, sql_str
from config import DB_SCHEMA

conn = get_connection()


def get_all_mappings():
    """All current mappings with audit metadata."""
    try:
        return conn.sql(
            f"""
            SELECT
                pod_lookup, point_of_delivery_code, local_point_of_delivery_code,
                local_point_of_delivery_description, pod_group_overview_master,
                old_pod_group_overview, notes, insertion_date,
                created_by, created_at, updated_by, updated_at
            FROM {DB_SCHEMA}.POD_GROUP_MAPPING
            ORDER BY pod_group_overview_master, pod_lookup
            """
        ).to_pandas()
    except Exception as e:
        st.error(f"Error loading mappings: {e}")
        return pd.DataFrame()


def upsert_mapping(point_code, local_code, local_desc, group, notes=None):
    """Create/update a mapping from its component fields."""
    try:
        actor = current_actor()
        res = conn.sql(
            f"CALL {DB_SCHEMA}.UPSERT_POD_MAPPING("
            f"{sql_str(point_code)}, {sql_str(local_code)}, {sql_str(local_desc)}, "
            f"{sql_str(group)}, {sql_str(actor)}, {sql_str(notes)})"
        ).to_pandas()
        msg = str(res.iloc[0, 0]) if not res.empty else ""
        return msg.startswith("SUCCESS"), msg
    except Exception as e:
        return False, str(e)


def update_mapping_group(pod_lookup, group, notes=None):
    """Retrospectively change the group on an existing mapping."""
    try:
        actor = current_actor()
        res = conn.sql(
            f"CALL {DB_SCHEMA}.UPDATE_POD_MAPPING_GROUP("
            f"{sql_str(pod_lookup)}, {sql_str(group)}, {sql_str(actor)}, {sql_str(notes)})"
        ).to_pandas()
        msg = str(res.iloc[0, 0]) if not res.empty else ""
        return msg.startswith("SUCCESS"), msg
    except Exception as e:
        return False, str(e)


def delete_mapping(pod_lookup):
    try:
        actor = current_actor()
        res = conn.sql(
            f"CALL {DB_SCHEMA}.DELETE_POD_MAPPING({sql_str(pod_lookup)}, {sql_str(actor)})"
        ).to_pandas()
        msg = str(res.iloc[0, 0]) if not res.empty else ""
        return msg.startswith("SUCCESS"), msg
    except Exception as e:
        return False, str(e)


def get_mapping_changes(pod_lookup=None, limit=200):
    """Audit history, optionally for a single key."""
    try:
        where = f"WHERE pod_lookup = {sql_str(pod_lookup)}" if pod_lookup else ""
        return conn.sql(
            f"""
            SELECT change_id, pod_lookup, change_type, old_value, new_value,
                   notes, changed_by, changed_at
            FROM {DB_SCHEMA}.POD_GROUP_MAPPING_CHANGES
            {where}
            ORDER BY changed_at DESC
            LIMIT {int(limit)}
            """
        ).to_pandas()
    except Exception as e:
        st.error(f"Error loading change history: {e}")
        return pd.DataFrame()
