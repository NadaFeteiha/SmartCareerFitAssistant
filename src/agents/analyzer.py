"""
Analyzer agents: fit scorer + skill-gap analyzer.
Both agents share the same AnalysisContext dataclass.
"""
from __future__ import annotations

import json
from dataclasses import dataclass

from pydantic_ai import Agent, RunContext

from src.agents.utils import unwrap_llm_json
from src.config import completion_settings, make_model
from src.models.analysis import FitScore, SkillGapReport
from src.models.job import JobRequirements
from src.models.resume import ResumeData


@dataclass
class AnalysisContext:
    resume_text: str
    job_text: str
    resume_data: ResumeData
    job_data: JobRequirements


# ── Fit Scorer ────────────────────────────────────────────────────────────────

_scorer_agent = Agent(
    make_model(),
    output_type=str,
    deps_type=AnalysisContext,
    retries=3,
    model_settings=completion_settings(4000),
    system_prompt="""You are a career analyst. Score the candidate's fit for a job.

Return ONLY a JSON object with exactly these fields:
{
    "overall": 75,
    "skill_match": 30,
    "experience_alignment": 25,
    "keyword_coverage": 20,
    "strengths": ["strength 1", "strength 2"],
    "explanation": "A detailed 2-3 sentence breakdown explaining why the score was given, what is missing, and why the score wasn't higher."
}

Rules:
- overall must equal skill_match + experience_alignment + keyword_coverage
- skill_match: 0-40, experience_alignment: 0-30, keyword_coverage: 0-30
- strengths is a list of strings
- No markdown, no wrapper keys, just the JSON object""",
)


@_scorer_agent.system_prompt
def _scorer_context(ctx: RunContext[AnalysisContext]) -> str:
    candidate_skills = [s.name for s in ctx.deps.resume_data.skills]
    required_skills = [s.name for s in ctx.deps.job_data.required_skills]
    body = (ctx.deps.resume_text or "")[:12_000]
    return (
        f"Candidate skills (structured): {candidate_skills}\n"
        f"Required skills: {required_skills}\n"
        f"Job title: {ctx.deps.job_data.title}\n"
        f"Candidate summary: {ctx.deps.resume_data.summary}\n\n"
        f"User-edited resume body (markdown):\n---\n{body}\n---\n"
    )


def _sanitize_fit_score(raw: str) -> str:
    clean = unwrap_llm_json(raw)
    try:
        data = json.loads(clean)
    except json.JSONDecodeError:
        return clean

    if not isinstance(data, dict):
        return clean

    if not data.get("strengths"):
        data["strengths"] = []
    elif isinstance(data["strengths"], str):
        data["strengths"] = [data["strengths"]]

    data.setdefault("explanation", "")

    def _clamp(val, lo, hi) -> int:
        try:
            return max(lo, min(hi, int(val)))
        except (TypeError, ValueError):
            return lo

    data["skill_match"] = _clamp(data.get("skill_match", 0), 0, 40)
    data["experience_alignment"] = _clamp(data.get("experience_alignment", 0), 0, 30)
    data["keyword_coverage"] = _clamp(data.get("keyword_coverage", 0), 0, 30)
    data["overall"] = (
        data["skill_match"] + data["experience_alignment"] + data["keyword_coverage"]
    )
    return json.dumps(data)


async def score_candidate(ctx: AnalysisContext) -> FitScore:
    raw = (await _scorer_agent.run("Score this candidate.", deps=ctx)).output
    clean = _sanitize_fit_score(raw)
    try:
        return FitScore.model_validate_json(clean)
    except Exception:
        print(f"\n[DEBUG] Raw fit score output:\n{raw}\n[DEBUG] Sanitized:\n{clean}\n")
        raise


# ── Gap Analyzer ──────────────────────────────────────────────────────────────

_gap_agent = Agent(
    make_model(),
    output_type=str,
    deps_type=AnalysisContext,
    retries=3,
    model_settings=completion_settings(4000),
    system_prompt="""You are a career coach. Identify skill gaps and create a learning roadmap.

Return ONLY a JSON object with exactly these fields:
{
  "missing_hard_skills": ["skill1", "skill2"],
  "missing_soft_skills": ["skill1"],
  "missing_requirements": {
    "missing_skills": ["required skills not evidenced on resume"],
    "missing_experience": ["JD responsibilities not shown in work history"],
    "missing_keywords": ["important JD terms absent from resume"]
  },
  "learning_roadmap": [
    {
      "skill": "Kubernetes",
      "priority": "high",
      "reason": "Required by the job posting",
      "suggestion": "Take the official Kubernetes fundamentals course"
    }
  ]
}

Rules:
- priority must be one of: high, medium, low
- All list values must be plain strings
- missing_hard_skills / missing_soft_skills must list ONLY genuine transferable skills
  (languages, frameworks, tools, platforms, methodologies)
- NEVER list employer names, brand names, or copied job-ad phrases
- No markdown, no wrapper keys, just the JSON object""",
)


@_gap_agent.system_prompt
def _gap_context(ctx: RunContext[AnalysisContext]) -> str:
    candidate_skills = [s.name for s in ctx.deps.resume_data.skills]
    required_skills = [s.name for s in ctx.deps.job_data.required_skills]
    resume_snip = (ctx.deps.resume_text or "")[:8_000]
    return (
        f"Candidate skills: {candidate_skills}\n"
        f"Required skills: {required_skills}\n"
        f"Job title: {ctx.deps.job_data.title}\n"
        f"Job responsibilities: {ctx.deps.job_data.responsibilities}\n"
        f"Resume excerpt:\n---\n{resume_snip}\n---\n"
    )


def _sanitize_skill_gap_json(clean: str) -> str:
    try:
        data = json.loads(clean)
    except json.JSONDecodeError:
        return clean
    if not isinstance(data, dict):
        return clean

    for key in ("missing_hard_skills", "missing_soft_skills", "learning_roadmap"):
        if not isinstance(data.get(key), list):
            data[key] = []

    mr = data.get("missing_requirements")
    if not isinstance(mr, dict):
        data["missing_requirements"] = {
            "missing_skills": [],
            "missing_experience": [],
            "missing_keywords": [],
        }
    else:
        for key in ("missing_skills", "missing_experience", "missing_keywords"):
            v = mr.get(key)
            if v is None:
                mr[key] = []
            elif isinstance(v, str):
                mr[key] = [v]
            elif not isinstance(v, list):
                mr[key] = []
            else:
                mr[key] = [str(x).strip() for x in v if str(x).strip()]
        data["missing_requirements"] = mr

    return json.dumps(data)


async def analyze_gaps(ctx: AnalysisContext) -> SkillGapReport:
    from src.utils.skill_validation import filter_skill_gap_report

    raw = (await _gap_agent.run("Identify skill gaps.", deps=ctx)).output
    clean = _sanitize_skill_gap_json(unwrap_llm_json(raw))
    try:
        report = SkillGapReport.model_validate_json(clean)
        return filter_skill_gap_report(ctx, report)
    except Exception:
        print(f"\n[DEBUG] Raw skill gap output:\n{raw}\n[DEBUG] Sanitized:\n{clean}\n")
        raise
    