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
    rescore_cache = st.session_state.setdefault("_rescore_cache", {})
    cached = rescore_cache.get(fp)
    if cached is not None:
        ar = st.session_state.analysis_result
        st.session_state.analysis_result = ar.model_copy(
            update={"fit_score": cached, "optimized_resume": md}
        )
        st.session_state["_resume_score_fp"] = fp
        return
    st.session_state["_resume_score_fp"] = fp
    try:
        new_fit = rescore_resume_draft_sync(ctx, md)
        ar = st.session_state.analysis_result
        st.session_state.analysis_result = ar.model_copy(
            update={"fit_score": new_fit, "optimized_resume": md}
        )
        rescore_cache[fp] = new_fit
    except Exception as e:
        st.session_state["_rescore_error"] = str(e)

def on_cover_letter_changed() -> None:
    cl = st.session_state.get("cover_letter_draft", "")
    if "analysis_result" in st.session_state:
        ar = st.session_state.analysis_result
        st.session_state.analysis_result = ar.model_copy(
            update={"cover_letter": cl}
        )


def overall_to_letter_grade(score: int) -> str:
    """Convert a numeric score (0-100) to a letter grade."""
    if score >= 90:
        return "A"
    elif score >= 80:
        return "B"
    elif score >= 70:
        return "C"
    elif score >= 60:
        return "D"
    else:
        return "F"
