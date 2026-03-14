"""Results tabs — rendered after pipeline completes."""

import streamlit as st
from src.models.analysis import FullAnalysis
from ui.components import render_score_cards, render_skill_chips, render_result_box
from src.utils.pdf import create_resume_pdf, create_cover_letter_pdf


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
    try:
        pdf_bytes = create_resume_pdf(result.optimized_resume, name="Optimized Resume")
        st.download_button(
            "⬇️ Download Resume PDF",
            data=pdf_bytes,
            file_name="optimized_resume.pdf",
            mime="application/pdf",
        )
    except Exception as e:
        st.error(f"Error generating PDF: {e}")
        st.download_button(
            "⬇️ Download Resume (Text)",
            data=result.optimized_resume,
            file_name="optimized_resume.txt",
            mime="text/plain",
        )


def _render_cover_letter_tab(result: FullAnalysis) -> None:
    render_result_box(result.cover_letter)
    try:
        pdf_bytes = create_cover_letter_pdf(result.cover_letter, name="Cover Letter")
        st.download_button(
            "⬇️ Download Cover Letter PDF",
            data=pdf_bytes,
            file_name="cover_letter.pdf",
            mime="application/pdf",
        )
    except Exception as e:
        st.error(f"Error generating PDF: {e}")
        st.download_button(
            "⬇️ Download Cover Letter (Text)",
            data=result.cover_letter,
            file_name="cover_letter.txt",
            mime="text/plain",
        )


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