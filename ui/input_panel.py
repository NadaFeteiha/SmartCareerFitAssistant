"""Resume + job description inputs (session-keyed for callback-safe reads)."""

from __future__ import annotations

import streamlit as st

from src.services.pdf_parser import extract_text_from_pdf
from ui.components import render_step_label


def render_input_panel() -> None:
    col1, col2 = st.columns([1, 1], gap="large")

    with col1:
        render_step_label(1, "Upload Your Resume")
        st.radio(
            "Input method",
            ["Upload PDF", "Paste text"],
            horizontal=True,
            label_visibility="collapsed",
            key="resume_upload_mode",
        )

        if st.session_state.get("resume_upload_mode") == "Upload PDF":
            uploaded = st.file_uploader(
                "Drop your PDF here",
                type=["pdf"],
                label_visibility="collapsed",
                key="resume_pdf_widget",
            )
            if uploaded is not None:
                text = extract_text_from_pdf(uploaded)
                st.session_state["resume_pdf_extracted"] = text
                st.success(f"✓ Loaded: {uploaded.name}")
                with st.expander("Preview extracted text"):
                    st.text(text[:800] + ("..." if len(text) > 800 else ""))
        else:
            st.text_area(
                "Paste resume",
                height=280,
                placeholder="John Smith\njohn@email.com\n\nSKILLS\nPython, FastAPI...",
                label_visibility="collapsed",
                key="resume_input_paste",
            )

    with col2:
        render_step_label(2, "Paste the Job Description")
        st.text_area(
            "Job description",
            height=320,
            placeholder="Senior Python Developer...\n\nRequired Skills:\n- Python\n- Docker...",
            label_visibility="collapsed",
            key="job_input",
        )


def get_resume_text_for_pipeline() -> str:
    if st.session_state.get("resume_upload_mode") == "Upload PDF":
        return (st.session_state.get("resume_pdf_extracted") or "").strip()
    return (st.session_state.get("resume_input_paste") or "").strip()


def get_job_text_for_pipeline() -> str:
    return (st.session_state.get("job_input") or "").strip()


def inputs_ready() -> bool:
    return bool(get_resume_text_for_pipeline().strip() and get_job_text_for_pipeline().strip())
