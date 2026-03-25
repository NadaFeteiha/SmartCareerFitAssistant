"""Reusable UI components — hero, step labels, score cards, chips, result boxes."""

import base64
import html
from io import BytesIO

import streamlit as st

from src.models.analysis import FitScore


def render_theme_control() -> None:
    """Appearance toggle (sidebar removed; theme lives in the main layout)."""
    _, right = st.columns([4, 1])
    with right:
        st.selectbox(
            "Appearance",
            ["dark", "light"],
            key="ui_theme",
            help="Light or dark colors for the app.",
        )


def render_hero() -> None:
    """Render the hero banner with tagline and stat pills."""
    st.markdown("""
    <div class="hero">
        <div class="hero-badge">AI-Powered · 100% Local</div>
        <h1>Land your <span>dream role</span> faster</h1>
        <p>Upload your resume and a job description. Get an instant fit score,
           skill gap analysis, a tailored cover letter, and an ATS-optimized
           resume — all powered by a local LLM.</p>
        <div class="stats-row">
            <div class="stat-pill"><strong>4</strong> AI outputs</div>
            <div class="stat-pill"><strong>100%</strong> local &amp; private</div>
            <div class="stat-pill"><strong>ATS</strong> optimized</div>
            <div class="stat-pill"><strong>0</strong> paid APIs</div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_step_label(step: int, title: str) -> None:
    """Render a step badge + section title above an input."""
    st.markdown(f"""
    <div class="section-label">
        <span class="step-badge">STEP {step}</span>
        <span class="section-title">{title}</span>
    </div>""", unsafe_allow_html=True)


def render_score_cards(fit: FitScore) -> None:
    """Render score cards, letter grade, and explanation (uses theme CSS classes)."""
    c1, c2, c3, c4 = st.columns(4)

    c1.markdown(f"""
    <div class="score-card">
        <div class="score-number" style="font-size:2.4rem">{fit.overall}</div>
        <div class="score-label">Overall / 100</div>
    </div>""", unsafe_allow_html=True)

    c2.markdown(f"""
    <div class="score-card">
        <div class="score-number" style="font-size:2rem">
            {fit.skill_match}<span class="score-denom">/40</span>
        </div>
        <div class="score-label">Skill match</div>
    </div>""", unsafe_allow_html=True)

    c3.markdown(f"""
    <div class="score-card">
        <div class="score-number" style="font-size:2rem">
            {fit.experience_alignment}<span class="score-denom">/30</span>
        </div>
        <div class="score-label">Experience</div>
    </div>""", unsafe_allow_html=True)

    c4.markdown(f"""
    <div class="score-card">
        <div class="score-number" style="font-size:2rem">
            {fit.keyword_coverage}<span class="score-denom">/30</span>
        </div>
        <div class="score-label">Keywords</div>
    </div>""", unsafe_allow_html=True)

    safe_exp = html.escape(fit.explanation)
    st.markdown(f"""
    <style>.score-denom {{ font-size: 1rem; opacity: 0.65; }}</style>
    <div class="score-analysis-box" style="margin-top: 1.5rem; padding: 1.25rem; border-radius: 8px;">
        <h4 style="margin-top: 0; margin-bottom: 0.5rem; font-size: 1.05rem;">🔍 Score analysis</h4>
        <p style="font-size: 14px; line-height: 1.6; margin-bottom: 0;">{safe_exp}</p>
    </div>
    """, unsafe_allow_html=True)


def render_result_box(content: str) -> None:
    """Render plain text content in a styled dark result box."""
    safe = content.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    st.markdown(
        f'<div class="result-box">{safe}</div>',
        unsafe_allow_html=True,
    )


def render_pdf_iframe(pdf_bytes_io: BytesIO, title: str, *, fallback_text: str) -> None:
    """Embed a PDF from in-memory bytes in an iframe, with optional text fallback on error."""
    try:
        base64_pdf = base64.b64encode(pdf_bytes_io.getvalue()).decode("utf-8")
        safe_title = html.escape(title)
        pdf_display = f"""
        <div style="
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 16px;
            background: #ffffff;
            height: 600px;
            overflow: hidden;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        ">
            <div style="
                text-align: center;
                margin-bottom: 12px;
                font-weight: 600;
                color: #1e293b;
                font-size: 14px;
            ">
                📄 {safe_title}
            </div>
            <iframe
                src="data:application/pdf;base64,{base64_pdf}"
                width="100%"
                height="550px"
                style="
                    border: none;
                    border-radius: 4px;
                    background: white;
                "
                title="{safe_title}"
            ></iframe>
        </div>
        """
        st.markdown(pdf_display, unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Error generating PDF preview: {str(e)}")
        render_result_box(fallback_text)


def render_skill_chips(strengths: list[str], missing_hard: list[str], missing_soft: list[str]) -> None:
    """Render strength and missing skill chips side by side."""
    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown("#### ✅ Your Strengths")
        chips = "".join(f'<span class="chip-green">{html.escape(s)}</span>' for s in strengths)
        st.markdown(chips or "<p style='color:#6b7fa3'>None identified</p>",
                    unsafe_allow_html=True)

    with col_b:
        st.markdown("#### ❌ Missing Skills")
        chips = "".join(
            f'<span class="chip-red">{html.escape(s)}</span>'
            for s in missing_hard + missing_soft
        )
        st.markdown(chips or "<p style='color:#6b7fa3'>No gaps found</p>",
                    unsafe_allow_html=True)