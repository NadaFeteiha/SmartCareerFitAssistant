import io
import json
import re
import urllib.error
import urllib.parse
import urllib.request
import uuid

from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from src.config import get_runtime_config, set_runtime_config
from src.database.database import init_db
from src.database.repository import (
    add_user_skill,
    delete_resume,
    get_all_analyses,
    get_resume,
    get_user_skill_confirmations,
    get_user_skills,
    get_user_profile,
    upsert_user_skill_confirmation,
    upsert_user_profile,
    upsert_resume,
)
from src.models.structured_resume import PersonalInfo, ProjectEntry, StructuredResume, to_markdown
from src.services.auth import (
    authenticate_user,
    consume_reset_token,
    create_access_token,
    create_user,
    get_current_user,
    get_user_by_email,
    issue_reset_token,
)
from src.services.pdf_parser import extract_text_from_pdf
from src.services.pipeline import run_pipeline
from src.services.resume_assist import assist_text, import_text_to_structured
from src.utils.pdf import create_cover_letter_pdf, create_resume_pdf


def _empty_resume() -> StructuredResume:
    return StructuredResume()


def _load_structured(raw: str | None) -> StructuredResume:
    """Read stored content as structured JSON; fall back to legacy plain text."""
    if not raw:
        return _empty_resume()
    raw = raw.strip()
    if raw.startswith("{"):
        try:
            return StructuredResume.model_validate_json(raw)
        except Exception:
            pass
    # Legacy plain-text resume — surface it as a summary so users can edit.
    return StructuredResume(personal=PersonalInfo(summary=raw))

app = FastAPI(title="SmartCareerFitAssistant API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

init_db()


# ── Auth ──────────────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


class ForgotRequest(BaseModel):
    email: str


class ResetRequest(BaseModel):
    token: str
    new_password: str


class ResumeRequest(BaseModel):
    """Save the user's structured resume."""
    resume: StructuredResume


class ImportTextRequest(BaseModel):
    text: str


class AssistRequest(BaseModel):
    text: str
    action: str  # improve_writing | suggest_content | grammar_check | shorter


class SkillConfirmationRequest(BaseModel):
    skill_name: str
    has_skill: bool


class GitHubImportRequest(BaseModel):
    username: str
    max_repos: int = 6
    job_text: str = ""


class UserProfileRequest(BaseModel):
    phone: str = ""
    linkedin: str = ""
    github: str = ""


@app.post("/api/auth/register")
def register(body: RegisterRequest):
    user = create_user(body.email, body.password)
    token = create_access_token(user["id"])
    return {"token": token, "user": user}


@app.post("/api/auth/login")
def login(body: LoginRequest):
    user = authenticate_user(body.email, body.password)
    token = create_access_token(user["id"])
    return {"token": token, "user": user}


@app.get("/api/auth/me")
def me(current_user: dict = Depends(get_current_user)):
    return current_user


@app.post("/api/auth/forgot")
def forgot_password(body: ForgotRequest):
    """Issue a password reset token. In dev the token is returned directly."""
    user = get_user_by_email(body.email)
    if not user:
        # Don't leak whether the email exists.
        return {"message": "If the email is registered, a reset token has been issued."}
    token = issue_reset_token(user["id"])
    return {
        "message": "Reset token issued. Use it within 30 minutes.",
        "reset_token": token,
    }


@app.post("/api/auth/reset")
def reset_password(body: ResetRequest):
    consume_reset_token(body.token, body.new_password)
    return {"status": "ok"}


# ── Resume (per-user) ─────────────────────────────────────────────────────────

@app.get("/api/resume")
def fetch_resume(current_user: dict = Depends(get_current_user)):
    content = get_resume(current_user["id"])
    structured = _load_structured(content)
    profile = get_user_profile(current_user["id"])
    if not structured.personal.phone:
        structured.personal.phone = profile["phone"]
    if not structured.personal.linkedin:
        structured.personal.linkedin = profile["linkedin"]
    if not structured.personal.github:
        structured.personal.github = profile["github"]
    return structured.model_dump()


@app.put("/api/resume")
def save_resume(body: ResumeRequest, current_user: dict = Depends(get_current_user)):
    upsert_user_profile(
        current_user["id"],
        phone=body.resume.personal.phone,
        linkedin=body.resume.personal.linkedin,
        github=body.resume.personal.github,
    )
    upsert_resume(current_user["id"], body.resume.model_dump_json())
    return {"status": "ok"}


@app.delete("/api/resume")
def remove_resume(current_user: dict = Depends(get_current_user)):
    delete_resume(current_user["id"])
    return {"status": "ok"}


@app.post("/api/resume/import")
async def import_resume(
    body: ImportTextRequest,
    current_user: dict = Depends(get_current_user),
):
    """Parse raw resume text into structured form and persist it."""
    if not body.text.strip():
        raise HTTPException(status_code=400, detail="Resume text is required")
    structured = await import_text_to_structured(body.text)
    profile = get_user_profile(current_user["id"])
    if not structured.personal.phone:
        structured.personal.phone = profile["phone"]
    if not structured.personal.linkedin:
        structured.personal.linkedin = profile["linkedin"]
    if not structured.personal.github:
        structured.personal.github = profile["github"]
    upsert_user_profile(
        current_user["id"],
        phone=structured.personal.phone,
        linkedin=structured.personal.linkedin,
        github=structured.personal.github,
    )
    upsert_resume(current_user["id"], structured.model_dump_json())
    return structured.model_dump()


@app.post("/api/resume/parse")
async def parse_resume(
    body: ImportTextRequest,
    current_user: dict = Depends(get_current_user),
):
    """Parse raw resume text into structured form WITHOUT persisting (used for the
    optimized-resume editor after analysis)."""
    if not body.text.strip():
        raise HTTPException(status_code=400, detail="Resume text is required")
    structured = await import_text_to_structured(body.text)
    profile = get_user_profile(current_user["id"])
    if not structured.personal.phone:
        structured.personal.phone = profile["phone"]
    if not structured.personal.linkedin:
        structured.personal.linkedin = profile["linkedin"]
    if not structured.personal.github:
        structured.personal.github = profile["github"]
    return structured.model_dump()


@app.post("/api/resume/assist")
async def resume_assist(
    body: AssistRequest,
    current_user: dict = Depends(get_current_user),
):
    """Run an AI rewrite (Improve Writing / Grammar Check / Shorter / Suggest Content)."""
    try:
        rewritten = await assist_text(body.text, body.action)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"text": rewritten}


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
async def upload_pdf(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
):
    """Extract text from a PDF, parse into structured form, and persist."""
    content = await file.read()
    text = extract_text_from_pdf(io.BytesIO(content))
    if not text.strip():
        return {"text": text, "resume": _empty_resume().model_dump()}
    structured = await import_text_to_structured(text)
    profile = get_user_profile(current_user["id"])
    if not structured.personal.phone:
        structured.personal.phone = profile["phone"]
    if not structured.personal.linkedin:
        structured.personal.linkedin = profile["linkedin"]
    if not structured.personal.github:
        structured.personal.github = profile["github"]
    upsert_user_profile(
        current_user["id"],
        phone=structured.personal.phone,
        linkedin=structured.personal.linkedin,
        github=structured.personal.github,
    )
    upsert_resume(current_user["id"], structured.model_dump_json())
    return {"text": text, "resume": structured.model_dump()}


@app.post("/api/analyze")
async def analyze(
    job_text: str = Form(...),
    current_user: dict = Depends(get_current_user),
):
    """Run the full 7-agent pipeline against the user's stored structured resume."""
    if not job_text.strip():
        raise HTTPException(status_code=400, detail="Job description is required")
    structured = _load_structured(get_resume(current_user["id"]))
    resume_md = to_markdown(structured)
    if not resume_md.strip():
        raise HTTPException(
            status_code=400,
            detail="No resume on file. Build or import your resume first.",
        )
    result, _ = await run_pipeline(resume_md, job_text, user_id=current_user["id"])
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


@app.get("/api/user/skill-confirmations")
def get_skill_confirmations(current_user: dict = Depends(get_current_user)):
    """Fetch saved skill confirmation decisions for this user."""
    return {"confirmations": get_user_skill_confirmations(current_user["id"])}


@app.post("/api/user/skill-confirmations")
def save_skill_confirmation(
    body: SkillConfirmationRequest,
    current_user: dict = Depends(get_current_user),
):
    """Save one skill confirmation (has skill / does not have skill)."""
    skill_name = body.skill_name.strip()
    if not skill_name:
        raise HTTPException(status_code=400, detail="skill_name is required")
    upsert_user_skill_confirmation(current_user["id"], skill_name, body.has_skill)
    if body.has_skill:
        structured = _load_structured(get_resume(current_user["id"]))
        existing = {s.lower() for s in structured.skills}
        if skill_name.lower() not in existing:
            structured.skills.append(skill_name)
            upsert_resume(current_user["id"], structured.model_dump_json())
    return {"status": "ok"}


def _fetch_public_repos(username: str, max_repos: int) -> list[dict]:
    safe_user = urllib.parse.quote(username.strip())
    url = f"https://api.github.com/users/{safe_user}/repos?sort=updated&per_page=100"
    req = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "SmartCareerFitAssistant",
        },
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            raise HTTPException(status_code=404, detail="GitHub user not found") from exc
        raise HTTPException(status_code=502, detail="Failed to fetch GitHub repositories") from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Failed to fetch GitHub repositories") from exc

    repos = []
    for repo in data:
        if not isinstance(repo, dict):
            continue
        if repo.get("fork"):
            continue
        repos.append(repo)
    repos.sort(key=lambda r: (r.get("stargazers_count", 0), r.get("updated_at", "")), reverse=True)
    return repos[:max(1, min(max_repos, 20))]


def _extract_job_keywords(job_text: str) -> set[str]:
    words = re.findall(r"[a-zA-Z][a-zA-Z0-9+#.\-]{1,}", (job_text or "").lower())
    stop = {
        "the", "and", "for", "with", "you", "your", "are", "this", "that", "from", "have",
        "has", "our", "not", "all", "will", "can", "job", "role", "team", "work", "using",
        "years", "year", "experience", "required", "preferred", "skills", "engineer",
        "developer", "development",
    }
    return {w for w in words if len(w) >= 3 and w not in stop}


def _repo_match_score(repo: dict, job_terms: set[str]) -> int:
    if not job_terms:
        return 0
    hay = []
    for field in ("name", "description", "language"):
        val = repo.get(field)
        if isinstance(val, str):
            hay.append(val.lower())
    topics = repo.get("topics")
    if isinstance(topics, list):
        hay.extend(str(t).lower() for t in topics)
    text = " ".join(hay)
    score = 0
    for term in job_terms:
        if term in text:
            score += 1
    return score


@app.post("/api/github/import")
def import_github_projects(
    body: GitHubImportRequest,
    current_user: dict = Depends(get_current_user),
):
    """Import top public GitHub repos into the user's resume projects section."""
    username = body.username.strip()
    if not username:
        raise HTTPException(status_code=400, detail="username is required")

    structured = _load_structured(get_resume(current_user["id"]))
    repos = _fetch_public_repos(username, body.max_repos)
    job_terms = _extract_job_keywords(body.job_text)
    if job_terms:
        ranked = sorted(
            repos,
            key=lambda r: (_repo_match_score(r, job_terms), r.get("stargazers_count", 0)),
            reverse=True,
        )
        repos = [r for r in ranked if _repo_match_score(r, job_terms) > 0][: max(1, min(body.max_repos, 20))]

    existing_links = {p.link.strip().lower() for p in structured.projects if p.link}
    added = 0
    for repo in repos:
        html_url = str(repo.get("html_url") or "").strip()
        if not html_url or html_url.lower() in existing_links:
            continue

        topics = repo.get("topics") or []
        topic_text = ", ".join(str(t) for t in topics[:5]) if isinstance(topics, list) else ""
        lang = str(repo.get("language") or "").strip()
        stars = int(repo.get("stargazers_count") or 0)
        base_desc = str(repo.get("description") or "").strip()
        bullets = []
        if base_desc:
            bullets.append(base_desc)
        meta = []
        if lang:
            meta.append(f"Primary language: {lang}")
        if topic_text:
            meta.append(f"Topics: {topic_text}")
        if stars:
            meta.append(f"Stars: {stars}")
        if meta:
            bullets.append(" | ".join(meta))
        description = "\n".join(f"- {line}" for line in bullets) if bullets else ""

        structured.projects.append(
            ProjectEntry(
                id=str(uuid.uuid4()),
                name=str(repo.get("name") or "GitHub Project"),
                link=html_url,
                description=description,
            )
        )
        existing_links.add(html_url.lower())
        added += 1

    if username and not structured.personal.github:
        structured.personal.github = f"https://github.com/{username}"

    upsert_user_profile(
        current_user["id"],
        phone=structured.personal.phone,
        linkedin=structured.personal.linkedin,
        github=structured.personal.github,
    )
    upsert_resume(current_user["id"], structured.model_dump_json())
    return {
        "status": "ok",
        "added_projects": added,
        "matched_by_job": bool(job_terms),
        "resume": structured.model_dump(),
    }


@app.get("/api/user/profile")
def fetch_user_profile(current_user: dict = Depends(get_current_user)):
    """Get saved contact profile values used to prefill resumes."""
    return get_user_profile(current_user["id"])


@app.put("/api/user/profile")
def save_user_profile(body: UserProfileRequest, current_user: dict = Depends(get_current_user)):
    """Persist contact profile values so user does not need to re-enter them."""
    upsert_user_profile(
        current_user["id"],
        phone=body.phone,
        linkedin=body.linkedin,
        github=body.github,
    )
    return {"status": "ok"}
