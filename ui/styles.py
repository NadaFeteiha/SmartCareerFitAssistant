"""All custom CSS for the SmartCareerFit UI."""

import streamlit as st


def apply_styles() -> None:
    """Inject the full custom CSS into the Streamlit app."""
    st.markdown(_CSS, unsafe_allow_html=True)


_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.stApp { background: #0f1117; }
#MainMenu, footer { visibility: hidden; }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: #161b27 !important;
    border-right: 1px solid #1e2535;
}
[data-testid="stSidebar"] * { color: #c9d1e0 !important; }
[data-testid="stSidebar"] .stTextInput input,
[data-testid="stSidebar"] .stTextArea textarea,
[data-testid="stSidebar"] .stSelectbox select {
    background: #1e2535 !important;
    border: 1px solid #2d3a52 !important;
    color: #e2e8f0 !important;
    border-radius: 8px !important;
}
[data-testid="stSidebar"] .stButton > button {
    background: linear-gradient(135deg, #6366f1, #4f46e5) !important;
    border: none !important;
    color: white !important;
    font-weight: 600 !important;
    border-radius: 10px !important;
    width: 100% !important;
}
.sidebar-logo { font-size: 18px; font-weight: 700; color: #818cf8 !important; }
.sidebar-sub  { font-size: 12px; color: #4a5568 !important; margin-top: 3px; }

/* ── Hero ── */
.hero {
    background: linear-gradient(135deg, #1a2340 0%, #0f1117 50%, #101828 100%);
    border: 1px solid #1e2d50;
    border-radius: 16px;
    padding: 40px 48px;
    margin-bottom: 32px;
    position: relative;
    overflow: hidden;
}
.hero-badge {
    display: inline-block;
    background: rgba(99,102,241,0.15);
    border: 1px solid rgba(99,102,241,0.35);
    color: #818cf8;
    font-size: 12px;
    font-weight: 600;
    letter-spacing: 1.2px;
    text-transform: uppercase;
    padding: 4px 14px;
    border-radius: 20px;
    margin-bottom: 14px;
}
.hero h1 {
    font-size: 2.4rem;
    font-weight: 700;
    color: #f1f5f9;
    margin: 0 0 10px 0;
    line-height: 1.2;
}
.hero h1 span { color: #818cf8; }
.hero p {
    color: #7d8fa8;
    font-size: 1rem;
    margin: 0;
    max-width: 560px;
    line-height: 1.7;
}
.stats-row { display: flex; gap: 16px; margin-top: 28px; flex-wrap: wrap; }
.stat-pill {
    background: rgba(255,255,255,0.04);
    border: 1px solid #1e2d50;
    border-radius: 10px;
    padding: 10px 20px;
    color: #94a3b8;
    font-size: 13px;
    font-weight: 500;
}
.stat-pill strong { color: #818cf8; margin-right: 6px; font-size: 15px; }

/* ── Step badges ── */
.section-label { display: flex; align-items: center; gap: 10px; margin-bottom: 12px; }
.step-badge {
    background: rgba(99,102,241,0.18);
    color: #818cf8;
    font-size: 11px;
    font-weight: 700;
    padding: 3px 10px;
    border-radius: 20px;
    letter-spacing: 0.6px;
}
.section-title { color: #e2e8f0; font-size: 15px; font-weight: 600; }

/* ── Inputs ── */
.stTextArea textarea, .stTextInput input {
    background: #1e2535 !important;
    border: 1px solid #2d3a52 !important;
    color: #e2e8f0 !important;
    border-radius: 10px !important;
    font-size: 14px !important;
}
.stTextArea textarea:focus, .stTextInput input:focus {
    border-color: #6366f1 !important;
    box-shadow: 0 0 0 2px rgba(99,102,241,0.2) !important;
}
[data-testid="stFileUploader"] {
    background: #1e2535 !important;
    border: 2px dashed #2d3a52 !important;
    border-radius: 12px !important;
}
[data-testid="stFileUploader"]:hover { border-color: #6366f1 !important; }

/* ── Primary button ── */
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #6366f1, #4f46e5) !important;
    border: none !important;
    color: white !important;
    font-weight: 600 !important;
    font-size: 15px !important;
    padding: 14px 40px !important;
    border-radius: 12px !important;
    width: 100% !important;
    transition: opacity 0.2s ease !important;
}
.stButton > button[kind="primary"]:hover {
    opacity: 0.9 !important;
    box-shadow: 0 8px 24px rgba(99,102,241,0.35) !important;
}

/* ── Tabs ── */
[data-testid="stTabs"] [role="tablist"] {
    background: #161b27;
    border-radius: 12px;
    padding: 4px;
    border: 1px solid #1e2535;
}
[data-testid="stTabs"] [role="tab"] {
    border-radius: 9px !important;
    color: #6b7fa3 !important;
    font-weight: 500 !important;
    font-size: 14px !important;
    padding: 8px 18px !important;
    border: none !important;
}
[data-testid="stTabs"] [role="tab"][aria-selected="true"] {
    background: linear-gradient(135deg, #6366f1, #4f46e5) !important;
    color: white !important;
}

/* ── Score cards ── */
.score-card {
    background: #161b27;
    border: 1px solid #1e2535;
    border-radius: 14px;
    padding: 24px;
    text-align: center;
}
.score-number { font-size: 3rem; font-weight: 700; color: #818cf8; line-height: 1; }
.score-label  { color: #6b7fa3; font-size: 13px; margin-top: 6px; }

/* ── Skill chips ── */
.chip-green {
    display: inline-block;
    background: rgba(16,185,129,0.12);
    border: 1px solid rgba(16,185,129,0.3);
    color: #34d399;
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 13px;
    margin: 3px;
}
.chip-red {
    display: inline-block;
    background: rgba(239,68,68,0.12);
    border: 1px solid rgba(239,68,68,0.3);
    color: #f87171;
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 13px;
    margin: 3px;
}

/* ── Result box ── */
.result-box {
    background: #1a2030;
    border: 1px solid #1e2d50;
    border-radius: 12px;
    padding: 24px;
    margin-top: 8px;
    color: #c9d1e0;
    line-height: 1.8;
    font-size: 14px;
    white-space: pre-wrap;
}

/* ── Download button ── */
.stDownloadButton > button {
    background: #1e2535 !important;
    border: 1px solid #2d3a52 !important;
    color: #818cf8 !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    margin-top: 12px !important;
}
.stDownloadButton > button:hover {
    border-color: #6366f1 !important;
    background: rgba(99,102,241,0.1) !important;
}

/* ── Misc ── */
[data-testid="stAlert"]   { border-radius: 10px !important; border: none !important; }
[data-testid="stSpinner"] p { color: #818cf8 !important; }
</style>
"""