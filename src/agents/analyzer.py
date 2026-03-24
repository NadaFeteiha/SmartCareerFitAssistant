import json
from dataclasses import dataclass
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider
from src.models.resume import ResumeData
from src.models.job import JobRequirements
from src.models.analysis import FitScore, SkillGapReport
from src.agents.utils import unwrap_llm_json
from src.config import completion_settings, settings


@dataclass
class AnalysisContext:
    resume_text: str
    job_text: str
    resume_data: ResumeData
    job_data: JobRequirements


def _make_model() -> OpenAIModel:
    return OpenAIModel(
        settings.ollama_model,
        provider=OpenAIProvider(
            base_url=settings.ollama_base_url,
            api_key="ollama",
        ),
    )


# ── Scorer ────────────────────────────────────────────────────────────────────

_scorer_agent = Agent(
    _make_model(),
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
    "explanation": "A detailed 2-3 sentence breakdown explaining exactly why the score was given, what specific experience/skills are missing, and the primary reasons the score wasn't higher."
}

Rules:
- overall must equal skill_match + experience_alignment + keyword_coverage
- skill_match is 0-40, experience_alignment is 0-30, keyword_coverage is 0-30
- strengths is a list of strings
- explanation MUST clearly state the specific missing factors and why a higher score was not achieved
- No markdown, no wrapper keys, just the JSON object""",
)

@_scorer_agent.system_prompt
def _scorer_context(ctx: RunContext[AnalysisContext]) -> str:
    candidate_skills = [s.name for s in ctx.deps.resume_data.skills]
    required_skills = [s.name for s in ctx.deps.job_data.required_skills]
    body = (ctx.deps.resume_text or "")[:12000]
    return f"""
Candidate skills (structured): {candidate_skills}
Required skills: {required_skills}
Job title: {ctx.deps.job_data.title}
Candidate summary: {ctx.deps.resume_data.summary}

User-edited resume body (markdown; use for keyword and experience judgment):
---
{body}
---
"""


def _sanitize_fit_score(raw: str) -> str:
    """Normalize LLM scorer output to satisfy FitScore validation rules."""
    clean = unwrap_llm_json(raw)

    try:
        data = json.loads(clean)
    except json.JSONDecodeError:
        return clean

    if not isinstance(data, dict):
        return clean

    # Ensure required fields exist and have correct types
    if "strengths" not in data or data["strengths"] in (None, ""):
        data["strengths"] = []
    elif isinstance(data["strengths"], str):
        data["strengths"] = [data["strengths"]]

    if "explanation" not in data or data["explanation"] in (None, ""):
        data["explanation"] = ""

    def _clamp_int(value, min_val, max_val):
        try:
            iv = int(value)
        except Exception:
            return min_val
        return max(min_val, min(max_val, iv))

    data["skill_match"] = _clamp_int(data.get("skill_match", 0), 0, 40)
    data["experience_alignment"] = _clamp_int(data.get("experience_alignment", 0), 0, 30)
    data["keyword_coverage"] = _clamp_int(data.get("keyword_coverage", 0), 0, 30)

    # Ensure overall matches the sum of parts to satisfy the model constraint.
    data["overall"] = data["skill_match"] + data["experience_alignment"] + data["keyword_coverage"]

    return json.dumps(data)


async def score_candidate(ctx: AnalysisContext) -> FitScore:
    raw = (await _scorer_agent.run("Score this candidate.", deps=ctx)).output
    clean = _sanitize_fit_score(raw)

    try:
        return FitScore.model_validate_json(clean)
    except Exception:
        print(f"\n[DEBUG] Raw fit score LLM output:\n{raw}\n")
        print(f"[DEBUG] After sanitize:\n{clean}\n")
        raise


# ── Gap Analyzer ──────────────────────────────────────────────────────────────

_gap_agent = Agent(
    _make_model(),
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
    "missing_skills": ["Specific required skills not evidenced on resume"],
    "missing_experience": ["JD responsibilities or experience themes not shown in work history"],
    "missing_keywords": ["Important JD terms/keywords absent from resume text"]
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
- missing_requirements lists must be specific and non-overlapping with duplicate strings
- missing_hard_skills and missing_soft_skills must list ONLY genuine transferable skills (languages, frameworks,
  tools, platforms, methodologies). NEVER list employer names, store/brand names, company-specific product names,
  or multi-word phrases copied from the job ad that are not standard industry skills.
- No markdown, no wrapper keys, just the JSON object""",
)

@_gap_agent.system_prompt
def _gap_context(ctx: RunContext[AnalysisContext]) -> str:
    candidate_skills = [s.name for s in ctx.deps.resume_data.skills]
    required_skills = [s.name for s in ctx.deps.job_data.required_skills]
    resume_snip = (ctx.deps.resume_text or "")[:8000]
    return f"""
Candidate skills: {candidate_skills}
Required skills: {required_skills}
Job title: {ctx.deps.job_data.title}
Job responsibilities (if known from JD): {ctx.deps.job_data.responsibilities}
Resume excerpt:
---
{resume_snip}
---
"""


def _sanitize_skill_gap_json(clean: str) -> str:
    try:
        data = json.loads(clean)
    except json.JSONDecodeError:
        return clean
    if not isinstance(data, dict):
        return clean

    for key in ("missing_hard_skills", "missing_soft_skills", "learning_roadmap"):
        if key not in data or not isinstance(data[key], list):
            data[key] = []

    mr = data.get("missing_requirements")
    if mr is None or not isinstance(mr, dict):
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
        print(f"\n[DEBUG] Raw skill gap LLM output:\n{raw}\n")
        print(f"[DEBUG] After sanitize:\n{clean}\n")
        raise


# Keep old names so existing imports don't break
scorer = _scorer_agent
gap_analyzer = _gap_agent