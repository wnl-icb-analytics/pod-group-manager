# =============================================================================
# POD Group Manager - Analytics Service
# =============================================================================

import pandas as pd
import streamlit as st
from database import get_connection
from config import DB_SCHEMA

conn = get_connection()


def get_group_counts():
    """Mapping count per POD group, including options with zero mappings."""
    try:
        return conn.sql(
            f"""
            SELECT o.pod_group_name AS POD_GROUP,
                   COUNT(m.pod_lookup) AS MAPPING_COUNT
            FROM {DB_SCHEMA}.POD_GROUP_OPTION o
            LEFT JOIN {DB_SCHEMA}.POD_GROUP_MAPPING m
                   ON m.pod_group_overview_master = o.pod_group_name
            WHERE o.is_active = TRUE
            GROUP BY o.pod_group_name
            ORDER BY MAPPING_COUNT DESC, POD_GROUP
            """
        ).to_pandas()
    except Exception as e:
        st.error(f"Error loading group counts: {e}")
        return pd.DataFrame()


def get_summary():
    """Headline KPIs: total mappings, groups in use, unmapped backlog."""
    try:
        mapped = conn.sql(
            f"SELECT COUNT(*) N, COUNT(DISTINCT pod_group_overview_master) G FROM {DB_SCHEMA}.POD_GROUP_MAPPING"
        ).to_pandas()
        unmapped = conn.sql(
            f"SELECT COUNT(*) N FROM {DB_SCHEMA}.V_UNMAPPED_PODS"
        ).to_pandas()
        return {
            "mappings": int(mapped.iloc[0]["N"]) if not mapped.empty else 0,
            "groups_used": int(mapped.iloc[0]["G"]) if not mapped.empty else 0,
            "unmapped": int(unmapped.iloc[0]["N"]) if not unmapped.empty else 0,
        }
    except Exception as e:
        st.error(f"Error loading summary: {e}")
        return {"mappings": 0, "groups_used": 0, "unmapped": 0}


def get_recent_activity(limit=20):
    """Recent mapping changes across all keys."""
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
