from typing import Required, TypedDict, cast

from langgraph.graph import StateGraph, START, END

from src.agents.analyzer import AnalysisContext, analyze_gaps, score_candidate
from src.agents.extractor import extract_job, extract_resume
from src.agents.generator import cover_letter_writer, resume_writer
from src.agents.keyword_optimizer import extract_top_jd_keywords
from src.config import get_model
from src.database.repository import get_user_confirmed_skills, save_analysis
from src.models.analysis import FitScore, FullAnalysis, SkillGapReport
from src.models.job import JobRequirements
from src.models.resume import ResumeData, Skill
from src.utils.resume_sections import consolidate_small_skill_categories, inject_skill_into_markdown


class PipelineState(TypedDict, total=False):
    # Inputs
    resume_text: Required[str]
    job_text: Required[str]
    user_id: int | None

    # Extraction outputs (written by parallel nodes)
    resume_data: ResumeData
    job_data: JobRequirements
    top_keywords: list[str]

    # Built once all extractions complete
    ctx: Required[AnalysisContext]

    # Analysis + generation outputs (written in parallel)
    fit_score: FitScore
    skill_gaps: SkillGapReport
    optimized_resume: str
    cover_letter: str

    # Final
    result: FullAnalysis


# ── Nodes ─────────────────────────────────────────────────────────────────────

async def _extract_resume_node(state: PipelineState) -> dict:
    resume_text = state["resume_text"]
    resume_data = await extract_resume(resume_text)

    user_id = state.get("user_id")
    if user_id is not None:
        saved_skills = get_user_confirmed_skills(user_id)
        existing = {s.name.lower() for s in resume_data.skills}
        for sk in saved_skills:
            if sk.lower() not in existing:
                resume_data.skills.append(
                    Skill(name=sk, category="hard_skill", proficiency="intermediate")
                )
                resume_text = inject_skill_into_markdown(resume_text, sk)
                existing.add(sk.lower())

    return {"resume_data": resume_data, "resume_text": resume_text}


async def _extract_job_node(state: PipelineState) -> dict:
    return {"job_data": await extract_job(state["job_text"])}


async def _extract_keywords_node(state: PipelineState) -> dict:
    return {"top_keywords": await extract_top_jd_keywords(state["job_text"])}


def _build_context_node(state: PipelineState) -> dict:
    assert "resume_data" in state, "build_context requires resume_data"
    assert "job_data" in state, "build_context requires job_data"

    job_data = state["job_data"]
    top_kw = state.get("top_keywords", [])
    merged_keywords = list(dict.fromkeys(top_kw + list(job_data.keywords)))[:35]
    job_data = job_data.model_copy(update={"keywords": merged_keywords})

    ctx = AnalysisContext(
        resume_text=state["resume_text"],
        job_text=state["job_text"],
        resume_data=state["resume_data"],
        job_data=job_data,
    )
    return {"ctx": ctx, "job_data": job_data}


async def _score_node(state: PipelineState) -> dict:
    return {"fit_score": await score_candidate(state["ctx"])}


async def _gaps_node(state: PipelineState) -> dict:
    return {"skill_gaps": await analyze_gaps(state["ctx"])}


async def _generate_resume_node(state: PipelineState) -> dict:
    ctx = state["ctx"]
    raw = (
        await resume_writer.run(
            "Rewrite this resume for the target job. Include a tailored ## SUMMARY section "
            "(2–4 sentences) based on the resume and job description, then EXPERIENCE, "
            "EDUCATION, and SKILLS.",
            deps=ctx,
            model=get_model(),
        )
    ).output
    return {"optimized_resume": consolidate_small_skill_categories(raw)}


async def _generate_cover_letter_node(state: PipelineState) -> dict:
    ctx = state["ctx"]
    cover = (
        await cover_letter_writer.run("Write a cover letter.", deps=ctx, model=get_model())
    ).output
    return {"cover_letter": cover}


def _persist_node(state: PipelineState) -> dict:
    assert "fit_score" in state, "persist requires fit_score"
    assert "skill_gaps" in state, "persist requires skill_gaps"
    assert "optimized_resume" in state, "persist requires optimized_resume"
    assert "cover_letter" in state, "persist requires cover_letter"

    result = FullAnalysis(
        fit_score=state["fit_score"],
        skill_gaps=state["skill_gaps"],
        optimized_resume=state["optimized_resume"],
        cover_letter=state["cover_letter"],
    )
    ctx = state["ctx"]
    save_analysis(
        result,
        job_title=ctx.job_data.title,
        company=ctx.job_data.company,
        user_id=state.get("user_id"),
    )
    return {"result": result}


# ── Graph ─────────────────────────────────────────────────────────────────────

def _build_graph():
    """Build the analysis pipeline DAG.

    START
      ├──> extract_resume ─────────────┐
      ├──> extract_job ────────────────┤
      └──> extract_keywords ───────────┤
                                       ▼
                                  build_context
                                       │
              ┌─────────────┬──────────┴─────────┬────────────────┐
              ▼             ▼                    ▼                ▼
            score         gaps          generate_resume   generate_cover_letter
              │             │                    │                │
              └─────────────┴──────────┬─────────┴────────────────┘
                                       ▼
                                    persist ──> END
    """
    g = StateGraph(PipelineState)

    g.add_node("extract_resume", _extract_resume_node)
    g.add_node("extract_job", _extract_job_node)
    g.add_node("extract_keywords", _extract_keywords_node)
    g.add_node("build_context", _build_context_node)
    g.add_node("score", _score_node)
    g.add_node("gaps", _gaps_node)
    g.add_node("generate_resume", _generate_resume_node)
    g.add_node("generate_cover_letter", _generate_cover_letter_node)
    g.add_node("persist", _persist_node)

    g.add_edge(START, "extract_resume")
    g.add_edge(START, "extract_job")
    g.add_edge(START, "extract_keywords")

    g.add_edge("extract_resume", "build_context")
    g.add_edge("extract_job", "build_context")
    g.add_edge("extract_keywords", "build_context")

    g.add_edge("build_context", "score")
    g.add_edge("build_context", "gaps")
    g.add_edge("build_context", "generate_resume")
    g.add_edge("build_context", "generate_cover_letter")

    g.add_edge("score", "persist")
    g.add_edge("gaps", "persist")
    g.add_edge("generate_resume", "persist")
    g.add_edge("generate_cover_letter", "persist")

    g.add_edge("persist", END)
    return g.compile()


_GRAPH = _build_graph()


async def run_pipeline(
    resume_text: str,
    job_text: str,
    user_id: int | None = None,
) -> tuple[FullAnalysis, AnalysisContext]:
    """Run the full analysis pipeline. Returns (result, context)."""
    final_state = await _GRAPH.ainvoke(
        cast(PipelineState, {
            "resume_text": resume_text,
            "job_text": job_text,
            "user_id": user_id,
        })
    )
    return final_state["result"], final_state["ctx"]
