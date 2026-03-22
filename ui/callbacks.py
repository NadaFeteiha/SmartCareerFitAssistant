"""Streamlit on_click / on_change callbacks (avoid fragile ``if st.button()`` patterns)."""

from __future__ import annotations

import streamlit as st


def queue_pipeline_run() -> None:
    st.session_state["pipeline_queued"] = True
