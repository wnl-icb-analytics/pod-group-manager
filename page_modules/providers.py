# =============================================================================
# POD Group Manager - Providers (manage the in-scope provider codes)
# =============================================================================

import pandas as pd
import streamlit as st
from services.providers_service import (
    get_providers, upsert_provider, set_provider_active, delete_provider,
)

COLS = [1.2, 5, 1.7, 1.5]
PENDING = "provider_pending_delete"


def _name(row):
    """Dictionary-resolved provider name; unknown codes muted."""
    value = row["PROVIDER_NAME"]
    if value is None or (isinstance(value, float) and pd.isnull(value)):
        return ":grey[— not in dictionary —]"
    return str(value)


def render_providers():
    st.subheader("In-scope providers")
    st.caption(
        "Provider codes scanned for unmapped POD combinations. Names come from the "
        "org dictionary automatically. Deactivate to drop a provider from detection "
        "while keeping the code on record. Changes take effect immediately — the "
        "unmapped list is reloaded on the next visit."
    )

    df = get_providers(active_only=False).reset_index(drop=True)

    if not df.empty:
        active_n = int(df["IS_ACTIVE"].sum())
        st.markdown(f"**{active_n}** active of **{len(df)}** provider(s).")

        h = st.columns(COLS, vertical_alignment="bottom")
        for col, label in zip(h, ["Code", "Provider name", "Status", "Remove"]):
            col.caption(label)

        pending = st.session_state.get(PENDING)
        for _, row in df.iterrows():
            code = row["PROVIDER_CODE"]
            active = bool(row["IS_ACTIVE"])
            c = st.columns(COLS, vertical_alignment="center")
            c[0].markdown(f"**{code}**" if active else f":grey[{code}]")
            c[1].markdown(_name(row) + ("" if active else " · :grey[inactive]"))

            with c[2]:
                if active:
                    st.button("Deactivate", key=f"deact_{code}", use_container_width=True,
                              on_click=_toggle, args=(code, False))
                else:
                    st.button("Activate", key=f"act_{code}", type="primary",
                              use_container_width=True, on_click=_toggle, args=(code, True))

            with c[3]:
                if pending == code:
                    y, n = st.columns(2)
                    y.button("✓", key=f"yes_{code}", type="primary", use_container_width=True,
                             help=f"Confirm removal of {code}", on_click=_confirm_delete, args=(code,))
                    n.button("✕", key=f"no_{code}", use_container_width=True,
                             help="Cancel", on_click=_cancel_delete)
                else:
                    st.button("Remove", key=f"del_{code}", use_container_width=True,
                              help="Delete this code — prefer Deactivate to keep it on record",
                              on_click=_ask_delete, args=(code,))

    st.divider()
    st.markdown("### Add a provider")
    st.caption(
        "Just the ODS code — the name fills in from the org dictionary. "
        "New providers are active straight away."
    )
    with st.form("provider_form"):
        f = st.columns([1.2, 5], vertical_alignment="bottom")
        new_code = f[0].text_input("Code", placeholder="RPY", max_chars=10)
        submitted = f[1].form_submit_button("💾 Add provider", type="primary")
        if submitted:
            code = (new_code or "").strip().upper()
            if not code:
                st.error("Provider code is required.")
            else:
                ok, msg = upsert_provider(code, True)
                (st.success if ok else st.error)(msg)
                if ok:
                    st.rerun()


def _toggle(code, is_active):
    ok, msg = set_provider_active(code, is_active)
    if not ok:
        st.error(msg)


def _ask_delete(code):
    st.session_state[PENDING] = code


def _cancel_delete():
    st.session_state.pop(PENDING, None)


def _confirm_delete(code):
    st.session_state.pop(PENDING, None)
    ok, msg = delete_provider(code)
    if not ok:
        st.error(msg)
