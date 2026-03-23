"""Results tabs — scores stay synced with ``st.session_state.analysis_result``."""

from __future__ import annotations

import html
import re

import streamlit as st

from src.models.analysis import FullAnalysis
from ui.components import render_result_box, render_score_cards, render_skill_chips
from ui.resume_handlers import on_resume_markdown_changed, on_cover_letter_changed
from src.utils.pdf import (
    create_cover_letter_docx,
    create_cover_letter_pdf,
    create_resume_docx,
    create_resume_pdf,
)


def render_results() -> None:
    result: FullAnalysis = st.session_state["analysis_result"]

    if "resume_markdown_draft" not in st.session_state:
        from src.utils.resume_sections import fingerprint_for_rescoring

        st.session_state.resume_markdown_draft = result.optimized_resume
        st.session_state["_resume_score_fp"] = fingerprint_for_rescoring(result.optimized_resume)

    err = st.session_state.pop("_rescore_error", None)
    if err:
        st.error(f"Re-score failed: {err}")

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    render_score_cards(result.fit_score)

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    ctx = st.session_state.get("pipeline_context")
    if ctx is not None:
        result = st.session_state["analysis_result"]

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Fit Analysis",
        "📝 Optimized Resume",
        "💌 Cover Letter",
        "📚 Learning Roadmap",
    ])

    with tab1:
        _render_fit_tab(result)

    with tab2:
        _render_resume_tab(result)

    with tab3:
        _render_cover_letter_tab(result)

    with tab4:
        _render_roadmap_tab(result)


def _render_missing_requirements(result: FullAnalysis) -> None:
    mr = result.skill_gaps.missing_requirements
    if not (mr.missing_skills or mr.missing_experience or mr.missing_keywords):
        return

    st.markdown("#### Missing requirements")
    st.caption("Compared to the job description — close gaps to move toward a stronger match.")
    parts = []
    if mr.missing_skills:
        li = "".join(f"<li>{html.escape(x)}</li>" for x in mr.missing_skills)
        parts.append(f"<h4>Skills</h4><ul>{li}</ul>")
    if mr.missing_experience:
        li = "".join(f"<li>{html.escape(x)}</li>" for x in mr.missing_experience)
        parts.append(f"<h4>Experience</h4><ul>{li}</ul>")
    if mr.missing_keywords:
        li = "".join(f"<li>{html.escape(x)}</li>" for x in mr.missing_keywords)
        parts.append(f"<h4>Keywords</h4><ul>{li}</ul>")
    st.markdown(
        f'<div class="missing-req-panel">{" ".join(parts)}</div>',
        unsafe_allow_html=True,
    )


def _render_fit_tab(result: FullAnalysis) -> None:
    render_skill_chips(
        strengths=result.fit_score.strengths,
        missing_hard=result.skill_gaps.missing_hard_skills,
        missing_soft=result.skill_gaps.missing_soft_skills,
    )
    _render_missing_requirements(result)


def _resume_download_basename(markdown: str) -> str:
    candidate_name = "resume"
    for line in markdown.split("\n"):
        if line.strip().startswith("# "):
            candidate_name = re.sub(r"[^\w\s-]", "", line.strip()[2:].strip()).strip().replace(" ", "_")
            break
    return candidate_name


def _render_resume_tab(result: FullAnalysis) -> None:
    st.caption(
        "Edit markdown below. Saving changes to **Skills** or **Experience** sections triggers a fit re-score. "
    )
    
    col_edit, col_prev = st.columns(2)
    with col_edit:
        st.text_area(
            "Editable resume (markdown)",
            height=600,
            key="resume_markdown_draft",
            on_change=on_resume_markdown_changed,
            label_visibility="collapsed",
        )

    md = st.session_state.get("resume_markdown_draft", result.optimized_resume)
    candidate_name = _resume_download_basename(md)

    with col_prev:
        with st.container(height=600, border=True):
            render_result_box(md)

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
    
    col1, col2, _col_spacer = st.columns([1.5, 1.5, 3])
    with col1:
        try:
            pdf_bytes = create_resume_pdf(md, filename_title="Optimized Resume")
            st.download_button(
                "⬇️ Download as PDF",
                data=pdf_bytes,
                file_name=f"{candidate_name}_resume.pdf",
                mime="application/pdf",
                key="resume_pdf_dl",
                use_container_width=True,
            )
        except Exception as e:
            st.error(f"PDF error: {e}")
    with col2:
        try:
            docx_bytes = create_resume_docx(md)
            st.download_button(
                "⬇️ Download as Word",
                data=docx_bytes,
                file_name=f"{candidate_name}_resume.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                key="resume_docx_dl",
                use_container_width=True,
            )
        except Exception as e:
            st.error(f"Word error: {e}")


def _render_cover_letter_tab(result: FullAnalysis) -> None:
    st.caption("Edit your cover letter below. Changes are saved automatically.")
    
    if "cover_letter_draft" not in st.session_state:
        st.session_state.cover_letter_draft = result.cover_letter
        
    col_edit, col_prev = st.columns(2)
    with col_edit:
        st.text_area(
            "Editable cover letter",
            height=600,
            key="cover_letter_draft",
            on_change=on_cover_letter_changed,
            label_visibility="collapsed",
        )
        
    cl = st.session_state.get("cover_letter_draft", result.cover_letter)
    
    with col_prev:
        with st.container(height=600, border=True):
            render_result_box(cl)

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
    
    col1, col2, _col_spacer = st.columns([1.5, 1.5, 3])
    with col1:
        try:
            pdf_bytes = create_cover_letter_pdf(cl, name="Cover Letter")
            st.download_button(
                "⬇️ Download as PDF",
                data=pdf_bytes,
                file_name="cover_letter.pdf",
                mime="application/pdf",
                key="cl_pdf_dl",
                use_container_width=True,
            )
        except Exception as e:
            st.error(f"PDF error: {e}")
    with col2:
        try:
            docx_bytes = create_cover_letter_docx(cl)
            st.download_button(
                "⬇️ Download as Word",
                data=docx_bytes,
                file_name="cover_letter.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                key="cl_docx_dl",
                use_container_width=True,
            )
        except Exception as e:
            st.error(f"Word error: {e}")


def _render_roadmap_tab(result: FullAnalysis) -> None:
    st.markdown("#### Prioritized Learning Roadmap")
    if not result.skill_gaps.learning_roadmap:
        st.info("No learning items identified — you're already a strong match!")
        return

    for item in result.skill_gaps.learning_roadmap:
        icon = "🔴" if item.priority == "high" else ("🟡" if item.priority == "medium" else "🟢")
        badge = f'<span class="step-badge">{item.priority.upper()}</span>'
        with st.expander(f"{icon} {item.skill}"):
            st.markdown(
                f"{badge} **Why it matters:** {item.reason}",
                unsafe_allow_html=True,
            )
            st.markdown(f"**How to learn it:** {item.suggestion}")
