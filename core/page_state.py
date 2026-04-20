"""Small Streamlit state helpers used across pages."""

from __future__ import annotations

import streamlit as st


def ensure_state(**defaults):
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def set_result(key: str, value):
    st.session_state[key] = value


def get_result(key: str, default=None):
    return st.session_state.get(key, default)
