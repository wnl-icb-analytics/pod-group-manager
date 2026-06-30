# =============================================================================
# POD Group Manager - Options (manage the dropdown values)
# =============================================================================

import streamlit as st
from services.options_service import get_options, upsert_option


def render_options():
    st.subheader("POD group options")
    st.caption("The values available in the assignment dropdown. Deactivate instead of deleting to keep history intact.")

    df = get_options(active_only=False)
    if not df.empty:
        st.dataframe(df, use_container_width=True, hide_index=True)

    st.divider()
    st.markdown("### Add or update an option")
    with st.form("option_form"):
        name = st.text_input("POD group name")
        c1, c2 = st.columns(2, vertical_alignment="bottom")
        with c1:
            order = st.number_input("Sort order", min_value=0, max_value=999, value=99, step=1)
        with c2:
            active = st.checkbox("Active", value=True)
        submitted = st.form_submit_button("💾 Save option", type="primary")
        if submitted:
            if not name.strip():
                st.error("Name is required.")
            else:
                ok, msg = upsert_option(name.strip(), int(order), active)
                (st.success if ok else st.error)(msg)
                if ok:
                    st.rerun()
