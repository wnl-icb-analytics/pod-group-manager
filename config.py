# =============================================================================
# POD Group Manager - Configuration & Constants
# =============================================================================

# Database location (new schema is the source of truth)
DB_SCHEMA = "DATA_LAKE__NCL.POD_GROUP_MANAGER"

# Role and warehouse
ROLE = "ENGINEER"
WAREHOUSE = "NCL_ANALYTICS_XS"

# Page configuration
PAGE_CONFIG = {
    "page_title": "POD Group Manager",
    "page_icon": "🗂️",
    "layout": "wide",
    "initial_sidebar_state": "collapsed",
}

CUSTOM_CSS = """
<style>
/* Primary buttons: solid accent fill with white text in all states */
button[kind="primary"],
button[kind="primaryFormSubmit"],
button[data-testid="stBaseButton-primary"],
button[data-testid="stBaseButton-primaryFormSubmit"] {
    background-color: #1d4ed8 !important;
    border: 1px solid #1d4ed8 !important;
    color: #ffffff !important;
}
button[kind="primary"]:hover,
button[kind="primaryFormSubmit"]:hover,
button[data-testid="stBaseButton-primary"]:hover,
button[data-testid="stBaseButton-primaryFormSubmit"]:hover {
    background-color: #3b82f6 !important;
    border-color: #3b82f6 !important;
    color: #ffffff !important;
}
button[kind="secondary"]:hover,
button[data-testid="stBaseButton-secondary"]:hover {
    border-color: #3b82f6 !important;
    color: #3b82f6 !important;
}
</style>
"""
