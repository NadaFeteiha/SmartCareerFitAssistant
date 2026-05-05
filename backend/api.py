import io

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from src.config import get_runtime_config, set_runtime_config
from src.database.database import init_db
from src.database.repository import add_user_skill, get_all_analyses, get_user_skills
from src.services.pdf_parser import extract_text_from_pdf
from src.services.pipeline import run_pipeline
from src.utils.pdf import create_cover_letter_pdf, create_resume_pdf

app = FastAPI(title="SmartCareerFitAssistant API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

init_db()


# ── LLM Provider Config ───────────────────────────────────────────────────────

class LLMConfigRequest(BaseModel):
    provider: str  # "ollama" | "anthropic"
    api_key: str = ""
    model_name: str = ""


@app.get("/api/config")
def get_config():
    """Return current LLM provider config (api_key is never returned for security)."""
    return get_runtime_config()


@app.post("/api/config")
def update_config(body: LLMConfigRequest):
    """Update the active LLM provider at runtime."""
    if body.provider not in ("ollama", "anthropic"):
        raise HTTPException(status_code=400, detail="provider must be 'ollama' or 'anthropic'")
    if body.provider == "anthropic" and not body.api_key:
        raise HTTPException(status_code=400, detail="api_key is required for the Anthropic provider")
    set_runtime_config(
        provider=body.provider,
        api_key=body.api_key,
        model_name=body.model_name,
    )
    return {"status": "ok", **get_runtime_config()}


# ── PDF / Analysis ────────────────────────────────────────────────────────────

@app.post("/api/upload-pdf")
async def upload_pdf(file: UploadFile = File(...)):
    """Extract text from an uploaded PDF resume."""
    content = await file.read()
    text = extract_text_from_pdf(io.BytesIO(content))
    return {"text": text}


@app.post("/api/analyze")
async def analyze(resume_text: str = Form(...), job_text: str = Form(...)):
    """Run the full 7-agent pipeline."""
    if not resume_text.strip() or not job_text.strip():
        raise HTTPException(status_code=400, detail="Resume and job description are required")
    result, _ = await run_pipeline(resume_text, job_text)
    return result.model_dump()


@app.get("/api/analyses")
def get_analyses():
    """Fetch all saved analyses."""
    return get_all_analyses()


# ── Download endpoints ────────────────────────────────────────────────────────

@app.post("/api/download/resume")
async def download_resume(resume_markdown: str = Form(...)):
    """Generate and stream a resume PDF."""
    buf = create_resume_pdf(resume_markdown)
    return StreamingResponse(
        buf,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=resume.pdf"},
    )


@app.post("/api/download/cover-letter")
async def download_cover_letter(cover_letter_text: str = Form(...)):
    """Generate and stream a cover letter PDF."""
    buf = create_cover_letter_pdf(cover_letter_text)
    return StreamingResponse(
        buf,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=cover_letter.pdf"},
    )


# ── User Skills ───────────────────────────────────────────────────────────────

@app.post("/api/user/skills")
def add_skill(user_name: str = Form(...), skill_name: str = Form(...)):
    """Persist a confirmed skill for a user."""
    add_user_skill(user_name, skill_name)
    return {"status": "ok"}


@app.get("/api/user/skills/{user_name}")
def get_skills(user_name: str):
    """Retrieve all saved skills for a user."""
    return {"skills": get_user_skills(user_name)}
