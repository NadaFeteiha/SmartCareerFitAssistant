"""
Extractor agents: resume parser + job description parser.

The job extractor now returns top ATS keywords as part of JobRequirements,
so keyword_optimizer.py is no longer needed as a separate agent/file.
"""
from __future__ import annotations

import json
import re

from pydantic_ai import Agent

from src.agents.utils import unwrap_llm_json
from src.config import completion_settings, make_model
from src.models.job import JobRequirements
from src.models.resume import ResumeData


# ── Resume extractor ─────────────────────────────────────────────────────────

_resume_agent = Agent(
    make_model(),
    output_type=str,
    retries=3,
    model_settings=completion_settings(4000),
    system_prompt="""You are a resume parser. Extract structured data from resume text.

Return ONLY a JSON object with exactly these fields:
{
  "name": "full name as string",
  "email": "email or empty string",
  "summary": "1-2 sentence professional summary",
  "education": ["degree and school as string"],
  "skills": [
    {"name": "skill name", "category": "programming|data|soft_skill|other", "proficiency": "beginner|intermediate|advanced"}
  ],
  "experiences": [
    {
      "title": "job title",
      "company": "company name",
      "duration": "date range",
      "highlights": ["achievement 1", "achievement 2"]
    }
  ]
}

No markdown. No explanation. No wrapper keys. Just the JSON object.""",
)


async def extract_resume(text: str) -> ResumeData:
    """Run the resume extractor and validate the output as ResumeData."""
    last_error: Exception | None = None
    raw = ""
    for attempt in range(3):
        raw = (await _resume_agent.run(text)).output
        clean = re.sub(r",\s*([\]}])", r"\1", unwrap_llm_json(raw))
        try:
            return ResumeData.model_validate_json(clean)
        except Exception as exc:
            last_error = exc
            if settings.debug:
                print(f"[DEBUG] extract_resume attempt {attempt + 1} failed: {exc}")

    print(f"\n[DEBUG] Raw resume LLM output (final failure):\n{raw}\n")
    raise last_error  # type: ignore[misc]


# ── Job description extractor (includes ATS keyword extraction) ───────────────

_job_agent = Agent(
    make_model(),
    output_type=str,
    retries=3,
    model_settings=completion_settings(4000),
    system_prompt="""You are a job description parser. Extract structured data.

Return ONLY a JSON object with exactly these fields:
{
  "title": "job title",
  "company": "company name or empty string",
  "experience_years": 0,
  "keywords": ["keyword1", "keyword2"],
  "top_ats_keywords": ["kw1", "kw2"],
  "responsibilities": ["responsibility 1"],
  "required_skills": [
    {"name": "skill name", "importance": "required|preferred", "category": "programming|data|soft_skill|other"}
  ]
}

Rules for top_ats_keywords:
- Exactly 10 distinct keywords or short phrases (1-3 words each)
- Prefer hard skills, tools, methodologies, and domain terms
- Lowercase except proper nouns (e.g. AWS, Kubernetes)

No markdown. No explanation. No wrapper keys. Just the JSON object.""",
)


def _sanitize_job_json(raw: str) -> str:
    """Repair and normalise raw job-extractor JSON."""
    repaired = re.sub(r",\s*([\]}])", r"\1", raw)
    clean = unwrap_llm_json(repaired)
    try:
        data = json.loads(clean)
    except json.JSONDecodeError:
        return clean

    if not isinstance(data, dict):
        return clean

    # Ensure list fields are always lists
    for field in ("keywords", "top_ats_keywords", "responsibilities", "required_skills"):
        if not isinstance(data.get(field), list):
            data[field] = []

    if not isinstance(data.get("experience_years"), int):
        try:
            data["experience_years"] = int(data.get("experience_years", 0))
        except (TypeError, ValueError):
            data["experience_years"] = 0

    return json.dumps(data)


async def extract_job(text: str) -> tuple[JobRequirements, list[str]]:
    """
    Run the job extractor.

    Returns:
        (JobRequirements, top_ats_keywords)  — callers merge keywords as needed.
    """
    last_error: Exception | None = None
    raw = ""
    for attempt in range(3):
        raw = (await _job_agent.run(text)).output
        clean = _sanitize_job_json(raw)
        try:
            data = json.loads(clean)
            top_ats: list[str] = data.pop("top_ats_keywords", [])
            job = JobRequirements.model_validate(data)
            return job, _dedup(top_ats)
        except Exception as exc:
            last_error = exc
            if settings.debug:
                print(f"[DEBUG] extract_job attempt {attempt + 1} failed: {exc}")

    print(f"\n[DEBUG] Raw JD LLM output (final failure):\n{raw}\n")
    raise last_error  # type: ignore[misc]


def _dedup(items: list[str], limit: int = 10) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for x in items:
        if not isinstance(x, str):
            continue
        t = x.strip()
        key = t.lower()
        if t and key not in seen:
            seen.add(key)
            out.append(t)
        if len(out) >= limit:
            break
    return out


# Keep these names so any external tooling that imported them still resolves.
# The pipeline should call extract_resume / extract_job directly.
resume_extractor = _resume_agent
job_extractor = _job_agent


# Lazy import to avoid circular reference at module load time
from src.config import settings  # noqa: E402
