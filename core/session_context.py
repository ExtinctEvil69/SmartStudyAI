"""Session-scoped helpers for Streamlit pages."""

from __future__ import annotations

import re
import uuid

import streamlit as st


def get_session_workspace(state_key: str, prefix: str) -> str:
    if state_key not in st.session_state:
        raw_workspace = f"{prefix}_{uuid.uuid4().hex[:12]}"
        st.session_state[state_key] = re.sub(r"[^a-zA-Z0-9_]", "_", raw_workspace)
    return st.session_state[state_key]
