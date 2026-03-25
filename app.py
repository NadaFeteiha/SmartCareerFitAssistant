"""
Streamlit entry point — layout, session defaults, and pipeline orchestration.
Heavy UI lives under ``ui/``; styles in ``src/styles``; persistence in ``src/database``.
"""
from __future__ import annotations

import hashlib

import streamlit as st

from src.database.database import init_db
from src.services.pipeline import (
    finalize_resume_cover_letter_and_save_sync,
    run_pipeline_through_gap_analysis_sync,
    stream_optimized_resume_for_streamlit,
)
from src.utils.resume_sections import fingerprint_for_rescoring
from ui import apply_styles, render_hero, render_results, render_sidebar
from ui.callbacks import queue_pipeline_run
from ui.skill_survey import render_chat_assistant
from ui.input_panel import (
    get_job_text_for_pipeline,
    get_resume_text_for_pipeline,
    inputs_ready,
    render_input_panel,
)

# ── Bootstrap ─────────────────────────────────────────────────────────────────
init_db()

st.set_page_config(
    page_title="SmartCareerFit",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

if "ui_theme" not in st.session_state:
    st.session_state.ui_theme = "dark"
if "resume_upload_mode" not in st.session_state:
    st.session_state.resume_upload_mode = "Paste text"

render_sidebar()
apply_styles(st.session_state.ui_theme)

render_hero()
render_input_panel()

st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
btn_col, _ = st.columns([1, 2])
with btn_col:
    st.button(
        "🚀 Analyze & Generate All Outputs",
        type="primary",
        disabled=not inputs_ready(),
        on_click=queue_pipeline_run,
        key="btn_run_pipeline",
    )

if not inputs_ready():
    st.info("Complete both steps above to enable analysis.")


def _reset_post_analysis_state() -> None:
    for _k in (
        "skill_survey_queue",
        "skill_survey_index",
        "skill_survey_finished",
        "skill_chat",
        "resume_markdown_draft",
        "_resume_score_fp",
        "_rescore_error",
    ):
        st.session_state.pop(_k, None)


# ── Pipeline (triggered via on_click → session flag) ─────────────────────────
if st.session_state.pop("pipeline_queued", False):
    resume_text = get_resume_text_for_pipeline()
    job_text = get_job_text_for_pipeline()
    if not (resume_text.strip() and job_text.strip()):
        st.warning("Add resume content and a job description before analyzing.")
    else:
        cache_key = hashlib.md5((resume_text + job_text).encode()).hexdigest()
        pipeline_cache = st.session_state.setdefault("_pipeline_cache", {})

        if cache_key in pipeline_cache:
            _reset_post_analysis_state()
            cached = pipeline_cache[cache_key]
            result = cached["analysis_result"]
            ctx = cached["pipeline_context"]
            st.session_state["analysis_result"] = result
            st.session_state["pipeline_context"] = ctx
            st.session_state["resume_markdown_draft"] = result.optimized_resume
            st.session_state["_resume_score_fp"] = fingerprint_for_rescoring(
                result.optimized_resume
            )
            st.success("Loaded cached analysis for this resume + job pair.")
        else:
            with st.status("Running AI analysis… (2–5 min on local hardware)", expanded=True) as status:
                st.write("⏳ Step 1/3 — Extracting structured data from resume and JD...")
                st.write("⏳ Step 2/3 — Scoring fit and identifying skill gaps...")
                st.write("⏳ Step 3/3 — Generating optimized resume and cover letter...")
                try:
                    _reset_post_analysis_state()
                    ctx, fit_score, skill_gaps = run_pipeline_through_gap_analysis_sync(
                        resume_text, job_text
                    )
                    st.write("✓ Scoring complete — streaming optimized resume…")
                    full_resume_md = st.write_stream(
                        stream_optimized_resume_for_streamlit(ctx)
                    )
                    result = finalize_resume_cover_letter_and_save_sync(
                        ctx, fit_score, skill_gaps, full_resume_md
                    )
                    st.session_state["analysis_result"] = result
                    st.session_state["pipeline_context"] = ctx
                    st.session_state["resume_markdown_draft"] = result.optimized_resume
                    st.session_state["_resume_score_fp"] = fingerprint_for_rescoring(
                        result.optimized_resume
                    )
                    pipeline_cache[cache_key] = {
                        "analysis_result": result,
                        "pipeline_context": ctx,
                    }
                    status.update(label="✅ Analysis complete!", state="complete")
                except Exception as e:
                    status.update(label="Analysis failed", state="error")
                    st.error(f"Error: {e}")
                    st.stop()

render_chat_assistant()

if "analysis_result" in st.session_state:
    render_results()
