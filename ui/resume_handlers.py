"""Resume editor change handlers — re-score only when skills/experience sections change."""

from __future__ import annotations

import streamlit as st

from src.services.rescore import rescore_resume_draft_sync
from src.utils.resume_sections import fingerprint_for_rescoring


def on_resume_markdown_changed() -> None:
    md = st.session_state.get("resume_markdown_draft", "")
    ctx = st.session_state.get("pipeline_context")
    if ctx is None or "analysis_result" not in st.session_state:
        return
    fp = fingerprint_for_rescoring(md)
    if fp == st.session_state.get("_resume_score_fp"):
        return
    st.session_state.pop("_rescore_error", None)
    st.session_state["_resume_score_fp"] = fp
    try:
        new_fit = rescore_resume_draft_sync(ctx, md)
        ar = st.session_state.analysis_result
        st.session_state.analysis_result = ar.model_copy(
            update={"fit_score": new_fit, "optimized_resume": md}
        )
    except Exception as e:
        st.session_state["_rescore_error"] = str(e)


def overall_to_letter_grade(overall: int) -> str:
    if overall >= 97:
        return "A+"
    if overall >= 93:
        return "A"
    if overall >= 90:
        return "A−"
    if overall >= 87:
        return "B+"
    if overall >= 83:
        return "B"
    if overall >= 80:
        return "B−"
    if overall >= 77:
        return "C+"
    if overall >= 73:
        return "C"
    if overall >= 70:
        return "C−"
    if overall >= 60:
        return "D"
    return "F"
