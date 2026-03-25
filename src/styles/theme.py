"""Streamlit theme injection — dark (default) and light palettes via CSS variables."""

from __future__ import annotations

import streamlit as st

_FONT_IMPORT = "@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');"


def apply_theme_styles(theme: str | None = None) -> None:
    """Inject CSS for the active theme. Call after sidebar sets ``st.session_state.ui_theme``."""
    t = (theme or st.session_state.get("ui_theme") or "dark").lower()
    if t not in ("dark", "light"):
        t = "dark"
    st.markdown(_THEME_CSS[t], unsafe_allow_html=True)


_THEME_CSS = {
    "dark": f"""
<style>
{_FONT_IMPORT}
html, body, [class*="css"] {{ font-family: 'Inter', sans-serif; }}
.stApp {{ background: #0A0F1C !important; color: #E2E8F0; }}
#MainMenu, footer {{ visibility: hidden; }}

[data-testid="stSidebar"] {{
    background: #111827 !important;
    border-right: 1px solid rgba(255, 255, 255, 0.05);
}}
[data-testid="stSidebar"] * {{ color: #94A3B8 !important; }}
[data-testid="stSidebar"] .stTextInput input,
[data-testid="stSidebar"] .stTextArea textarea,
[data-testid="stSidebar"] .stSelectbox select {{
    background: #1E293B !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    color: #F8FAFC !important;
    border-radius: 8px !important;
    transition: all 0.3s ease;
}}
[data-testid="stSidebar"] .stTextInput input:focus,
[data-testid="stSidebar"] .stTextArea textarea:focus {{
    border-color: #6366F1 !important;
    box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.2) !important;
}}
[data-testid="stSidebar"] .stButton > button {{
    background: linear-gradient(135deg, #6366F1, #4F46E5) !important;
    border: none !important;
    color: white !important;
    font-weight: 600 !important;
    border-radius: 10px !important;
    width: 100% !important;
    box-shadow: 0 4px 14px 0 rgba(99, 102, 241, 0.39);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}}
[data-testid="stSidebar"] .stButton > button:hover {{
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(99, 102, 241, 0.5);
}}
.sidebar-logo {{ font-size: 20px; font-weight: 800; background: -webkit-linear-gradient(180deg, #A5B4FC, #6366F1); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
.sidebar-sub  {{ font-size: 13px; color: #64748B !important; margin-top: 4px; letter-spacing: 0.5px; }}

.hero {{
    background: radial-gradient(circle at top left, #1E1B4B 0%, #0A0F1C 50%, #0A0F1C 100%);
    border: 1px solid rgba(255, 255, 255, 0.05);
    border-radius: 20px;
    padding: 48px 56px;
    margin-bottom: 32px;
    position: relative;
    overflow: hidden;
    box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
}}
.hero::before {{
    content: ''; position: absolute; top: -50px; left: -50px; width: 200px; height: 200px;
    background: rgba(99, 102, 241, 0.2); filter: blur(80px); border-radius: 50%;
}}
.hero-badge {{ color: #818cf8; border-color: rgba(99,102,241,0.35); background: rgba(99,102,241,0.15); display: inline-block; padding: 4px 12px; border-radius: 20px; font-size: 0.85rem; font-weight: 600; margin-bottom: 1rem; }}
.hero h1 {{ color: #F8FAFC; font-size: 3rem; font-weight: 800; letter-spacing: -0.02em; line-height: 1.1; margin-bottom: 1rem; }}
.hero h1 span {{ background: linear-gradient(to right, #818CF8, #C084FC); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
.hero p {{ color: #94A3B8; font-size: 1.15rem; line-height: 1.6; max-width: 800px; font-weight: 300; }}
.stats-row {{ display: flex; gap: 1rem; margin-top: 2rem; flex-wrap: wrap; }}
.stat-pill {{ background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.1); color: #94a3b8; padding: 8px 16px; border-radius: 12px; font-size: 0.95rem; backdrop-filter: blur(10px); }}
.stat-pill strong {{ color: #818cf8; }}

.section-label {{ margin-bottom: 1rem; display: flex; align-items: center; gap: 0.75rem; }}
.section-title {{ color: #F1F5F9; font-weight: 600; font-size: 1.25rem; }}
.step-badge {{ background: rgba(99,102,241,0.2); color: #818cf8; padding: 4px 10px; border-radius: 8px; font-weight: 700; font-size: 0.75rem; letter-spacing: 0.05em; }}

.stTextArea textarea, .stTextInput input {{
    background: #111827 !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    color: #F8FAFC !important;
    border-radius: 12px !important;
    transition: all 0.3s ease;
}}
.stTextArea textarea:focus, .stTextInput input:focus {{
    border-color: #6366F1 !important;
    box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.15) !important;
}}
[data-testid="stFileUploader"] {{
    background: #111827 !important;
    border: 2px dashed rgba(255, 255, 255, 0.15) !important;
    border-radius: 16px !important;
    transition: all 0.3s ease;
}}
[data-testid="stFileUploader"]:hover {{
    border-color: rgba(99, 102, 241, 0.5) !important;
    background: rgba(99, 102, 241, 0.02) !important;
}}

.stButton > button[kind="primary"] {{
    background: linear-gradient(135deg, #6366F1, #8B5CF6) !important;
    border: none !important;
    color: white !important;
    border-radius: 12px !important;
    padding: 0.75rem 1.5rem !important;
    font-weight: 600 !important;
    box-shadow: 0 4px 14px 0 rgba(99, 102, 241, 0.39);
    transition: all 0.3s ease;
}}
.stButton > button[kind="primary"]:hover {{
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(99, 102, 241, 0.6);
}}

[data-testid="stTabs"] [role="tablist"] {{
    background: #111827;
    border: 1px solid rgba(255, 255, 255, 0.05);
    border-radius: 14px;
    padding: 4px;
    gap: 0.5rem;
}}
[data-testid="stTabs"] [role="tab"] {{ color: #64748B !important; font-weight: 500; border-radius: 10px; transition: all 0.2s ease; padding: 0.5rem 1rem; }}
[data-testid="stTabs"] [role="tab"]:hover {{ color: #F1F5F9 !important; background: rgba(255, 255, 255, 0.05); }}
[data-testid="stTabs"] [role="tab"][aria-selected="true"] {{
    background: linear-gradient(135deg, #6366F1, #8B5CF6) !important;
    color: white !important;
    box-shadow: 0 2px 10px rgba(99, 102, 241, 0.3);
}}

.score-card {{
    background: rgba(17, 24, 39, 0.6);
    backdrop-filter: blur(12px);
    border: 1px solid rgba(255, 255, 255, 0.05);
    border-radius: 16px;
    padding: 28px 24px;
    text-align: center;
    box-shadow: 0 10px 30px -10px rgba(0, 0, 0, 0.3);
    transition: transform 0.3s ease, border-color 0.3s ease;
}}
.score-card:hover {{
    transform: translateY(-4px);
    border-color: rgba(99, 102, 241, 0.3);
}}
.score-number {{ color: #818CF8; font-weight: 800; font-family: 'Inter', sans-serif; letter-spacing: -0.05em; }}
.score-label {{ color: #94A3B8; font-weight: 500; margin-top: 8px; font-size: 0.95rem; }}
.score-analysis-box {{
    background: linear-gradient(180deg, rgba(30, 41, 59, 0.5) 0%, rgba(17, 24, 39, 0.5) 100%);
    border: 1px solid rgba(255, 255, 255, 0.05);
    border-radius: 12px;
    color: #CBD5E1;
}}
.score-analysis-box h4 {{ color: #F8FAFC; display: flex; align-items: center; gap: 8px; }}

.chip-green {{
    background: rgba(16,185,129,0.1); border: 1px solid rgba(16,185,129,0.2); color: #34D399;
    padding: 4px 12px; border-radius: 16px; font-size: 0.85rem; font-weight: 500; display: inline-block; margin: 4px;
}}
.chip-red {{
    background: rgba(239,68,68,0.1); border: 1px solid rgba(239,68,68,0.2); color: #F87171;
    padding: 4px 12px; border-radius: 16px; font-size: 0.85rem; font-weight: 500; display: inline-block; margin: 4px;
}}
.chip-amber {{
    background: rgba(245,158,11,0.1); border: 1px solid rgba(245,158,11,0.2); color: #FBBF24;
    padding: 4px 12px; border-radius: 16px; font-size: 0.85rem; font-weight: 500; display: inline-block; margin: 4px;
}}

.result-box {{
    background: #0F172A;
    border: 1px solid rgba(255, 255, 255, 0.05);
    color: #E2E8F0;
    border-radius: 12px;
    padding: 1.5rem;
    font-size: 0.95rem;
    line-height: 1.6;
    overflow-y: auto;
    height: 100%;
}}

.stDownloadButton > button {{
    background: #111827 !important;
    border: 1px solid rgba(99, 102, 241, 0.3) !important;
    color: #818CF8 !important;
    border-radius: 10px !important;
    transition: all 0.2s ease;
}}
.stDownloadButton > button:hover {{
    background: rgba(99, 102, 241, 0.1) !important;
    color: #A5B4FC !important;
    border-color: rgba(99, 102, 241, 0.5) !important;
}}

.missing-req-panel {{
    background: rgba(17, 24, 39, 0.6);
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.05);
    border-radius: 16px;
    padding: 1.5rem;
    margin-top: 1rem;
}}
.missing-req-panel h4 {{ color: #F1F5F9; margin-top: 0; font-weight: 600; font-size: 1.1rem; }}
.missing-req-panel li {{ color: #94A3B8; margin-bottom: 0.5rem; list-style-type: none; position: relative; padding-left: 1.25rem; }}
.missing-req-panel li::before {{ content: '•'; position: absolute; left: 0; color: #6366F1; }}

[data-testid="stAlert"] {{ border-radius: 12px !important; border: 1px solid rgba(255,255,255,0.05) !important; }}

div[data-testid="stVerticalBlock"]:has(> div.element-container .chat-container-anchor) {{
    position: fixed !important;
    bottom: 2rem !important;
    right: 2rem !important;
    width: 380px !important;
    background: rgba(17, 24, 39, 0.95) !important;
    backdrop-filter: blur(12px) !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    border-radius: 16px !important;
    z-index: 1000 !important;
    padding: 1.5rem !important;
    box-shadow: 0 10px 30px -5px rgba(0, 0, 0, 0.5) !important;
}}
div[data-testid="stVerticalBlock"]:has(> div.element-container .chat-container-anchor):not(:has(h3)) {{
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    padding: 0 !important;
    width: auto !important;
}}
div[data-testid="stVerticalBlock"]:has(> div.element-container .chat-container-anchor):not(:has(h3)) button {{
    width: auto !important;
    box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.4) !important;
    border-radius: 50px !important;
    padding: 12px 24px !important;
    background: linear-gradient(135deg, #6366F1, #8B5CF6) !important;
    color: white !important;
    border: none !important;
    font-weight: 600 !important;
}}
div[data-testid="stVerticalBlock"]:has(> div.element-container .chat-container-anchor):not(:has(h3)) button p {{
    color: white !important;
    font-weight: 600 !important;
}}
</style>
""",
    "light": f"""
<style>
{_FONT_IMPORT}
html, body, [class*="css"] {{ font-family: 'Inter', sans-serif; }}
.stApp {{ background: #F8FAFC !important; color: #0F172A; }}
#MainMenu, footer {{ visibility: hidden; }}

[data-testid="stSidebar"] {{
    background: #FFFFFF !important;
    border-right: 1px solid rgba(0, 0, 0, 0.05);
}}
[data-testid="stSidebar"] * {{ color: #475569 !important; }}
[data-testid="stSidebar"] .stTextInput input,
[data-testid="stSidebar"] .stTextArea textarea,
[data-testid="stSidebar"] .stSelectbox select {{
    background: #F1F5F9 !important;
    border: 1px solid rgba(0, 0, 0, 0.05) !important;
    color: #0F172A !important;
    border-radius: 8px !important;
    transition: all 0.3s ease;
}}
[data-testid="stSidebar"] .stTextInput input:focus,
[data-testid="stSidebar"] .stTextArea textarea:focus {{
    border-color: #4F46E5 !important;
    box-shadow: 0 0 0 2px rgba(79, 70, 229, 0.1) !important;
}}
[data-testid="stSidebar"] .stButton > button {{
    background: linear-gradient(135deg, #4F46E5, #4338CA) !important;
    border: none !important;
    color: white !important;
    font-weight: 600 !important;
    border-radius: 10px !important;
    width: 100% !important;
    box-shadow: 0 4px 14px 0 rgba(79, 70, 229, 0.25);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}}
[data-testid="stSidebar"] .stButton > button:hover {{
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(79, 70, 229, 0.35);
}}
.sidebar-logo {{ font-size: 20px; font-weight: 800; background: -webkit-linear-gradient(180deg, #4338CA, #4F46E5); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
.sidebar-sub  {{ font-size: 13px; color: #64748B !important; margin-top: 4px; letter-spacing: 0.5px; }}

.hero {{
    background: radial-gradient(circle at top left, #EEF2FF 0%, #FFFFFF 50%, #F8FAFC 100%);
    border: 1px solid rgba(0, 0, 0, 0.05);
    border-radius: 20px;
    padding: 48px 56px;
    margin-bottom: 32px;
    position: relative;
    overflow: hidden;
    box-shadow: 0 10px 40px -10px rgba(0, 0, 0, 0.05);
}}
.hero-badge {{ color: #4338CA; border-color: rgba(79,70,229,0.2); background: rgba(79,70,229,0.1); display: inline-block; padding: 4px 12px; border-radius: 20px; font-size: 0.85rem; font-weight: 600; margin-bottom: 1rem; }}
.hero h1 {{ color: #0F172A; font-size: 3rem; font-weight: 800; letter-spacing: -0.02em; line-height: 1.1; margin-bottom: 1rem; }}
.hero h1 span {{ background: linear-gradient(to right, #4F46E5, #9333EA); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
.hero p {{ color: #475569; font-size: 1.15rem; line-height: 1.6; max-width: 800px; font-weight: 400; }}
.stat-pill {{ background: #FFFFFF; border: 1px solid rgba(0,0,0,0.05); color: #64748B; padding: 8px 16px; border-radius: 12px; font-size: 0.95rem; box-shadow: 0 1px 3px rgba(0,0,0,0.02); }}
.stat-pill strong {{ color: #4338CA; }}

.section-label {{ margin-bottom: 1rem; display: flex; align-items: center; gap: 0.75rem; }}
.section-title {{ color: #0F172A; font-weight: 600; font-size: 1.25rem; }}
.step-badge {{ background: #E0E7FF; color: #4338CA; padding: 4px 10px; border-radius: 8px; font-weight: 700; font-size: 0.75rem; letter-spacing: 0.05em; }}

.stTextArea textarea, .stTextInput input {{
    background: #FFFFFF !important;
    border: 1px solid rgba(0, 0, 0, 0.1) !important;
    color: #0F172A !important;
    border-radius: 12px !important;
    transition: all 0.3s ease;
}}
.stTextArea textarea:focus, .stTextInput input:focus {{
    border-color: #4F46E5 !important;
    box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.1) !important;
}}
[data-testid="stFileUploader"] {{
    background: #F8FAFC !important;
    border: 2px dashed rgba(0, 0, 0, 0.15) !important;
    border-radius: 16px !important;
    transition: all 0.3s ease;
}}
[data-testid="stFileUploader"]:hover {{
    border-color: #4F46E5 !important;
    background: rgba(79, 70, 229, 0.02) !important;
}}

.stButton > button[kind="primary"] {{
    background: linear-gradient(135deg, #4F46E5, #4338CA) !important;
    border: none !important;
    color: white !important;
    border-radius: 12px !important;
    padding: 0.75rem 1.5rem !important;
    font-weight: 600 !important;
    box-shadow: 0 4px 14px 0 rgba(79, 70, 229, 0.25);
    transition: all 0.3s ease;
}}
.stButton > button[kind="primary"]:hover {{
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(79, 70, 229, 0.35);
}}

[data-testid="stTabs"] [role="tablist"] {{
    background: #F1F5F9;
    border: 1px solid rgba(0, 0, 0, 0.05);
    border-radius: 14px;
    padding: 4px;
    gap: 0.5rem;
}}
[data-testid="stTabs"] [role="tab"] {{ color: #64748B !important; font-weight: 500; border-radius: 10px; transition: all 0.2s ease; padding: 0.5rem 1rem; }}
[data-testid="stTabs"] [role="tab"]:hover {{ color: #0F172A !important; background: rgba(0, 0, 0, 0.02); }}
[data-testid="stTabs"] [role="tab"][aria-selected="true"] {{
    background: linear-gradient(135deg, #4F46E5, #4338CA) !important;
    color: white !important;
    box-shadow: 0 2px 10px rgba(79, 70, 229, 0.2);
}}

.score-card {{
    background: #FFFFFF;
    border: 1px solid rgba(0, 0, 0, 0.05);
    border-radius: 16px;
    padding: 28px 24px;
    text-align: center;
    box-shadow: 0 4px 15px -5px rgba(0, 0, 0, 0.05);
    transition: transform 0.3s ease, border-color 0.3s ease, box-shadow 0.3s ease;
}}
.score-card:hover {{
    transform: translateY(-4px);
    border-color: rgba(79, 70, 229, 0.2);
    box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.1);
}}
.score-number {{ color: #4338CA; font-weight: 800; font-family: 'Inter', sans-serif; letter-spacing: -0.05em; }}
.score-label {{ color: #64748B; font-weight: 500; margin-top: 8px; font-size: 0.95rem; }}
.score-analysis-box {{
    background: #F1F5F9;
    border: 1px solid rgba(0, 0, 0, 0.05);
    border-radius: 12px;
    color: #475569;
}}
.score-analysis-box h4 {{ color: #0F172A; display: flex; align-items: center; gap: 8px; }}

.chip-green {{
    background: #ECFDF5; border: 1px solid #A7F3D0; color: #059669;
    padding: 4px 12px; border-radius: 16px; font-size: 0.85rem; font-weight: 500; display: inline-block; margin: 4px;
}}
.chip-red {{
    background: #FEF2F2; border: 1px solid #FECACA; color: #DC2626;
    padding: 4px 12px; border-radius: 16px; font-size: 0.85rem; font-weight: 500; display: inline-block; margin: 4px;
}}
.chip-amber {{
    background: #FFFBEB; border: 1px solid #FDE68A; color: #D97706;
    padding: 4px 12px; border-radius: 16px; font-size: 0.85rem; font-weight: 500; display: inline-block; margin: 4px;
}}

.result-box {{
    background: #FFFFFF;
    border: 1px solid rgba(0, 0, 0, 0.1);
    color: #334155;
    border-radius: 12px;
    padding: 1.5rem;
    font-size: 0.95rem;
    line-height: 1.6;
    overflow-y: auto;
    height: 100%;
}}

.stDownloadButton > button {{
    background: #FFFFFF !important;
    border: 1px solid rgba(79, 70, 229, 0.2) !important;
    color: #4F46E5 !important;
    border-radius: 10px !important;
    transition: all 0.2s ease;
}}
.stDownloadButton > button:hover {{
    background: #EEF2FF !important;
    border-color: #4F46E5 !important;
}}

.missing-req-panel {{
    background: #FFFFFF;
    border: 1px solid rgba(0, 0, 0, 0.05);
    border-radius: 16px;
    padding: 1.5rem;
    margin-top: 1rem;
    box-shadow: 0 4px 15px -5px rgba(0,0,0,0.05);
}}
.missing-req-panel h4 {{ color: #0F172A; margin-top: 0; font-weight: 600; font-size: 1.1rem; }}
.missing-req-panel li {{ color: #475569; margin-bottom: 0.5rem; list-style-type: none; position: relative; padding-left: 1.25rem; }}
.missing-req-panel li::before {{ content: '•'; position: absolute; left: 0; color: #4F46E5; }}

[data-testid="stAlert"] {{ border-radius: 12px !important; border: 1px solid rgba(0,0,0,0.05) !important; }}

div[data-testid="stVerticalBlock"]:has(> div.element-container .chat-container-anchor) {{
    position: fixed !important;
    bottom: 2rem !important;
    right: 2rem !important;
    width: 380px !important;
    background: rgba(255, 255, 255, 0.95) !important;
    backdrop-filter: blur(12px) !important;
    border: 1px solid rgba(0, 0, 0, 0.1) !important;
    border-radius: 16px !important;
    z-index: 1000 !important;
    padding: 1.5rem !important;
    box-shadow: 0 10px 30px -5px rgba(0, 0, 0, 0.2) !important;
}}
div[data-testid="stVerticalBlock"]:has(> div.element-container .chat-container-anchor):not(:has(h3)) {{
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    padding: 0 !important;
    width: auto !important;
}}
div[data-testid="stVerticalBlock"]:has(> div.element-container .chat-container-anchor):not(:has(h3)) button {{
    width: auto !important;
    box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.2) !important;
    border-radius: 50px !important;
    padding: 12px 24px !important;
    background: linear-gradient(135deg, #4F46E5, #4338CA) !important;
    color: white !important;
    border: none !important;
    font-weight: 600 !important;
}}
div[data-testid="stVerticalBlock"]:has(> div.element-container .chat-container-anchor):not(:has(h3)) button p {{
    color: white !important;
    font-weight: 600 !important;
}}
</style>
"""
}
