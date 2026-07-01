# =============================================================================
# POD Group Manager - Main Application Entry Point
# =============================================================================

import streamlit as st
from config import PAGE_CONFIG, CUSTOM_CSS
from database import get_connection

st.set_page_config(**PAGE_CONFIG)
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# Initialise connection (cached)
get_connection()

# Navigation state
if "page" not in st.session_state:
    st.session_state.page = "home"

# Header + nav
col1, col2 = st.columns([3, 2])
with col1:
    st.title("🗂️ POD Group Manager")
    st.caption("Assign and maintain POD group overview mappings")
with col2:
    st.markdown("<br>", unsafe_allow_html=True)
    n1, n2, n3, n4, n5 = st.columns(5)
    pages = [
        (n1, "Unmapped", "home"),
        (n2, "Mappings", "mappings"),
        (n3, "Analytics", "analytics"),
        (n4, "Options", "options"),
        (n5, "SQL", "reference"),
    ]
    for col, label, key in pages:
        with col:
            primary = st.session_state.page == key
            if st.button(label, use_container_width=True,
                         type="primary" if primary else "secondary", key=f"nav_{key}"):
                st.session_state.page = key
                st.rerun()

st.divider()

# Routing
if st.session_state.page == "home":
    from page_modules.unmapped import render_unmapped
    render_unmapped()
elif st.session_state.page == "mappings":
    from page_modules.mappings import render_mappings
    render_mappings()
elif st.session_state.page == "analytics":
    from page_modules.analytics import render_analytics
    render_analytics()
elif st.session_state.page == "options":
    from page_modules.options import render_options
    render_options()
elif st.session_state.page == "reference":
    from page_modules.reference import render_reference
    render_reference()
