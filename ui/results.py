"""Results tabs — rendered after pipeline completes."""

import streamlit as st
import re
from src.models.analysis import FullAnalysis
from ui.components import render_score_cards, render_skill_chips, render_result_box
from src.utils.pdf import (
    create_resume_pdf, create_cover_letter_pdf,
    create_resume_docx, create_cover_letter_docx,
)


def render_results(result: FullAnalysis) -> None:
    """Render the full results section: score cards + four output tabs."""
    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    render_score_cards(result.fit_score)

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


# ── Private tab renderers ──────────────────────────────────────────────────────

def _render_fit_tab(result: FullAnalysis) -> None:
    render_skill_chips(
        strengths=result.fit_score.strengths,
        missing_hard=result.skill_gaps.missing_hard_skills,
        missing_soft=result.skill_gaps.missing_soft_skills,
    )


def _render_resume_tab(result: FullAnalysis) -> None:
    render_result_box(result.optimized_resume)

    candidate_name = "resume"
    for line in result.optimized_resume.split('\n'):
        if line.strip().startswith('# '):
            candidate_name = re.sub(r'[^\w\s-]', '', line.strip()[2:].strip()).strip().replace(' ', '_')
            break

    col1, col2 = st.columns(2)
    with col1:
        try:
            pdf_bytes = create_resume_pdf(result.optimized_resume, filename_title="Optimized Resume")
            st.download_button(
                "⬇️ Download as PDF",
                data=pdf_bytes,
                file_name=f"{candidate_name}_resume.pdf",
                mime="application/pdf",
                key="resume_pdf",
            )
        except Exception as e:
            st.error(f"PDF error: {e}")
    with col2:
        try:
            docx_bytes = create_resume_docx(result.optimized_resume)
            st.download_button(
                "⬇️ Download as Word",
                data=docx_bytes,
                file_name=f"{candidate_name}_resume.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                key="resume_docx",
            )
        except Exception as e:
            st.error(f"Word error: {e}")


def _render_cover_letter_tab(result: FullAnalysis) -> None:
    render_result_box(result.cover_letter)

    col1, col2 = st.columns(2)
    with col1:
        try:
            pdf_bytes = create_cover_letter_pdf(result.cover_letter, name="Cover Letter")
            st.download_button(
                "⬇️ Download as PDF",
                data=pdf_bytes,
                file_name="cover_letter.pdf",
                mime="application/pdf",
                key="cl_pdf",
            )
        except Exception as e:
            st.error(f"PDF error: {e}")
    with col2:
        try:
            docx_bytes = create_cover_letter_docx(result.cover_letter)
            st.download_button(
                "⬇️ Download as Word",
                data=docx_bytes,
                file_name="cover_letter.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                key="cl_docx",
            )
        except Exception as e:
            st.error(f"Word error: {e}")


def _render_roadmap_tab(result: FullAnalysis) -> None:
    st.markdown("#### Prioritized Learning Roadmap")
    if not result.skill_gaps.learning_roadmap:
        st.info("No learning items identified — you're already a strong match!")
        return

    for item in result.skill_gaps.learning_roadmap:
        icon  = "🔴" if item.priority == "high" else ("🟡" if item.priority == "medium" else "🟢")
        badge = f'<span class="step-badge">{item.priority.upper()}</span>'
        with st.expander(f"{icon} {item.skill}"):
            st.markdown(f"{badge} **Why it matters:** {item.reason}",
                        unsafe_allow_html=True)
            st.markdown(f"**How to learn it:** {item.suggestion}")