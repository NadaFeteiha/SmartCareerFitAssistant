"""Reusable UI components — hero, step labels, score cards, chips, result boxes."""

import streamlit as st
from src.models.analysis import FitScore


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
    """Render the four score metric cards and the explanation caption."""
    c1, c2, c3, c4 = st.columns(4)

    c1.markdown(f"""
    <div class="score-card">
        <div class="score-number">{fit.overall}</div>
        <div class="score-label">Overall Score / 100</div>
    </div>""", unsafe_allow_html=True)

    c2.markdown(f"""
    <div class="score-card">
        <div class="score-number" style="font-size:2rem">
            {fit.skill_match}<span style="font-size:1rem;color:#6b7fa3">/40</span>
        </div>
        <div class="score-label">Skill Match</div>
    </div>""", unsafe_allow_html=True)

    c3.markdown(f"""
    <div class="score-card">
        <div class="score-number" style="font-size:2rem">
            {fit.experience_alignment}<span style="font-size:1rem;color:#6b7fa3">/30</span>
        </div>
        <div class="score-label">Experience</div>
    </div>""", unsafe_allow_html=True)

    c4.markdown(f"""
    <div class="score-card">
        <div class="score-number" style="font-size:2rem">
            {fit.keyword_coverage}<span style="font-size:1rem;color:#6b7fa3">/30</span>
        </div>
        <div class="score-label">Keywords</div>
    </div>""", unsafe_allow_html=True)

    st.markdown(f"""
    <div style="margin-top: 1.5rem; padding: 1.25rem; border-radius: 8px; background-color: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.1);">
        <h4 style="margin-top: 0; margin-bottom: 0.5rem; color: #e2e8f0; font-size: 1.05rem; display: flex; align-items: center; gap: 0.5rem;">
            🔍 Score Analysis
        </h4>
        <p style="color: #94a3b8; font-size: 14px; line-height: 1.6; margin-bottom: 0;">
            {fit.explanation}
        </p>
    </div>
    """, unsafe_allow_html=True)


def render_result_box(content: str) -> None:
    """Render plain text content in a styled dark result box."""
    safe = content.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    st.markdown(
        f'<div class="result-box">{safe}</div>',
        unsafe_allow_html=True,
    )


def render_skill_chips(strengths: list[str], missing_hard: list[str], missing_soft: list[str]) -> None:
    """Render strength and missing skill chips side by side."""
    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown("#### ✅ Your Strengths")
        chips = "".join(f'<span class="chip-green">{s}</span>' for s in strengths)
        st.markdown(chips or "<p style='color:#6b7fa3'>None identified</p>",
                    unsafe_allow_html=True)

    with col_b:
        st.markdown("#### ❌ Missing Skills")
        chips = "".join(
            f'<span class="chip-red">{s}</span>'
            for s in missing_hard + missing_soft
        )
        st.markdown(chips or "<p style='color:#6b7fa3'>No gaps found</p>",
                    unsafe_allow_html=True)