from dataclasses import dataclass
from typing import Any, cast

from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.settings import ModelSettings

from src.agents.utils import parse_model
from src.models.resume import ResumeData
from src.models.job import JobRequirements
from src.models.analysis import FitScore, SkillGapReport
from src.config import completion_settings, get_model, settings
from inspect import signature


@dataclass
class AnalysisContext:
    resume_text: str
    job_text: str
    resume_data: ResumeData
    job_data: JobRequirements


def _default_model() -> OpenAIChatModel:
    """Ollama model used only for agent construction; overridden at run time via get_model()."""
    return OpenAIChatModel(
        settings.ollama_model,
        provider=OpenAIProvider(base_url=settings.ollama_base_url, api_key="ollama"),
    )


# ── Scorer ────────────────────────────────────────────────────────────────────

_scorer_agent = Agent(
    model= _default_model(),
    name="scorer",  
    output_type=str,
    deps_type=AnalysisContext,
    retries=3,
    model_settings=ModelSettings(**completion_settings(4000)),
    system_prompt="""
                    You are a career analyst. Score the candidate's fit for a job.
                    Return ONLY a JSON object with this exact shape:
                    {
                    "overall": 75,
                    "skill_match": 30,
                    "experience_alignment": 25,
                    "keyword_coverage": 20,
                    "strengths": ["strength 1", "strength 2"],
                    "explanation": "A 2-3 sentence explanation of the score, what specific skills/experience are missing, and why the score wasn't higher."
                    }

                    Rules:
                    - overall must equal skill_match + experience_alignment + keyword_coverage
                    - skill_match is 0-40, experience_alignment is 0-30, keyword_coverage is 0-30
                    - No markdown, no wrapper keys, just the JSON object
                    """,
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


async def score_candidate(ctx: AnalysisContext) -> FitScore:
    raw = (await _scorer_agent.run("Score this candidate.", deps=ctx, model=get_model())).output
    return parse_model(raw, FitScore)


# ── Gap Analyzer ──────────────────────────────────────────────────────────────

_gap_agent = Agent(
    _default_model(),
    output_type=str,
    deps_type=AnalysisContext,
    retries=3,
    model_settings=ModelSettings(**completion_settings(4000)),
    system_prompt="""
    You are a career coach. Identify skill gaps and create a learning roadmap.
    Return ONLY a JSON object with this exact shape:
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
    - missing_hard_skills / missing_soft_skills must list ONLY genuine transferable skills (languages, frameworks,
    tools, platforms, methodologies). NEVER list employer names, store/brand names, company-specific product names,
    or multi-word phrases copied from the job ad that are not standard industry skills.
    - No markdown, no wrapper keys, just the JSON object
""",
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


async def analyze_gaps(ctx: AnalysisContext) -> SkillGapReport:
    from src.utils.skill_validation import filter_skill_gap_report

    raw = (await _gap_agent.run("Identify skill gaps.", deps=ctx, model=get_model())).output
    report = parse_model(raw, SkillGapReport)
    return filter_skill_gap_report(ctx, report)


scorer = _scorer_agent
gap_analyzer = _gap_agent
