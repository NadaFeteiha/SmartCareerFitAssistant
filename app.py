"""
Streamlit entry point.
Responsibilities: page config, wiring UI modules to the pipeline.
Nothing else belongs here.
"""
import streamlit as st

from src.db.database import init_db
from src.services.pipeline import run_pipeline_sync
from src.services.pdf_parser import extract_text_from_pdf
from ui import apply_styles, render_sidebar, render_hero, render_step_label, render_results

# ── Bootstrap ──────────────────────────────────────────────────────────────────
init_db()

st.set_page_config(
    page_title="SmartCareerFit",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

apply_styles()

# ── Sidebar ────────────────────────────────────────────────────────────────────
profile = render_sidebar()

# ── Hero ───────────────────────────────────────────────────────────────────────
render_hero()

# ── Inputs ─────────────────────────────────────────────────────────────────────
col1, col2 = st.columns([1, 1], gap="large")

with col1:
    render_step_label(1, "Upload Your Resume")
    upload_mode = st.radio("Input method", ["Upload PDF", "Paste text"],
                           horizontal=True, label_visibility="collapsed")
    resume_text = ""

    if upload_mode == "Upload PDF":
        uploaded = st.file_uploader("Drop your PDF here",
                                    type=["pdf"], label_visibility="collapsed")
        if uploaded:
            resume_text = extract_text_from_pdf(uploaded)
            st.success(f"✓ Loaded: {uploaded.name}")
            with st.expander("Preview extracted text"):
                st.text(resume_text[:800] + ("..." if len(resume_text) > 800 else ""))
    else:
        resume_text = st.text_area(
            "Paste resume", height=280,
            placeholder="John Smith\njohn@email.com\n\nSKILLS\nPython, FastAPI...",
            label_visibility="collapsed",
        )

with col2:
    render_step_label(2, "Paste the Job Description")
    job_text = st.text_area(
        "Job description", height=320,
        placeholder="Senior Python Developer...\n\nRequired Skills:\n- Python\n- Docker...",
        label_visibility="collapsed",
    )

# ── Analyze button ─────────────────────────────────────────────────────────────
st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
btn_col, _ = st.columns([1, 2])
with btn_col:
    run = st.button(
        "🚀 Analyze & Generate All Outputs",
        type="primary",
        disabled=not (resume_text.strip() and job_text.strip()),
    )

if not (resume_text.strip() and job_text.strip()):
    st.info("Complete both steps above to enable analysis.")

# ── Pipeline ───────────────────────────────────────────────────────────────────
if run:
    with st.status("Running AI analysis… (2–5 min on local hardware)",
                   expanded=True) as status:
        st.write("⏳ Step 1/3 — Extracting structured data from resume and JD...")
        st.write("⏳ Step 2/3 — Scoring fit and identifying skill gaps...")
        st.write("⏳ Step 3/3 — Generating optimized resume and cover letter...")
        try:
            result = run_pipeline_sync(resume_text, job_text)
            status.update(label="✅ Analysis complete!", state="complete")
        except Exception as e:
            status.update(label="Analysis failed", state="error")
            st.error(f"Error: {e}")
            st.stop()

    render_results(result)