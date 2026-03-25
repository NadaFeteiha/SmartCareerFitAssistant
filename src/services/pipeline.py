import asyncio

from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from src.agents.analyzer import analyze_gaps, score_candidate
from src.agents.context import AnalysisContext
from src.agents.extractor import extract_job, extract_resume
from src.agents.generator import cover_letter_writer, stream_optimized_resume_text
from src.agents.keyword_optimizer import extract_top_jd_keywords
from src.agents.skill_matching import build_skill_match_summary
from src.database.repository import get_user_skills, save_analysis
from src.models.analysis import FitScore, FullAnalysis, SkillGapReport
from src.models.resume import Skill
from src.utils.resume_sections import consolidate_small_skill_categories, inject_skill_into_markdown

_llm_retry = retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type(Exception),
    reraise=True,
)


@_llm_retry
async def _score_candidate_llm(ctx: AnalysisContext) -> FitScore:
    return await score_candidate(ctx)


@_llm_retry
async def _analyze_gaps_llm(ctx: AnalysisContext) -> SkillGapReport:
    return await analyze_gaps(ctx)


@_llm_retry
async def _cover_letter_writer_llm(ctx: AnalysisContext):
    return await cover_letter_writer.run("Write a cover letter.", deps=ctx)


def _merge_keywords_case_insensitive(top_kw: list[str], job_keywords: list[str], limit: int) -> list[str]:
    seen: dict[str, str] = {}
    for kw in top_kw + list(job_keywords):
        key = (kw or "").lower().strip()
        if key and key not in seen:
            seen[key] = kw.strip() if kw else kw
    return list(seen.values())[:limit]


async def build_analysis_context(resume_text: str, job_text: str) -> AnalysisContext:
    """
    Extract resume/JD, merge user survey skills, enrich keywords and optional embedding hints.
    """
    resume_data = await extract_resume(resume_text)

    user_name = resume_data.name
    if user_name:
        saved_skills = get_user_skills(user_name)
        existing_skills = {s.name.lower() for s in resume_data.skills}
        for sk in saved_skills:
            if sk.lower() not in existing_skills:
                resume_data.skills.append(Skill(name=sk, category="hard_skill", proficiency="intermediate"))
                resume_text = inject_skill_into_markdown(resume_text, sk)
                existing_skills.add(sk.lower())

    job_data = await extract_job(job_text)

    top_kw = await extract_top_jd_keywords(job_text)
    merged_keywords = _merge_keywords_case_insensitive(top_kw, list(job_data.keywords), 35)
    job_data = job_data.model_copy(update={"keywords": merged_keywords})

    skill_summary = await build_skill_match_summary(
        [s.name for s in resume_data.skills],
        [s.name for s in job_data.required_skills],
    )

    return AnalysisContext(
        resume_text=resume_text,
        job_text=job_text,
        resume_data=resume_data,
        job_data=job_data,
        skill_match_summary=skill_summary,
    )


async def analyze_fit_and_gaps(ctx: AnalysisContext) -> tuple[FitScore, SkillGapReport]:
    fit_score, skill_gaps = await asyncio.gather(
        _score_candidate_llm(ctx),
        _analyze_gaps_llm(ctx),
    )
    return fit_score, skill_gaps


async def run_pipeline_through_gap_analysis(
    resume_text: str,
    job_text: str,
) -> tuple[AnalysisContext, FitScore, SkillGapReport]:
    """Steps 1–2: extraction + parallel fit score and gap report (no resume/letter generation)."""
    print("Step 1/3: Extracting structured data...")
    ctx = await build_analysis_context(resume_text, job_text)

    print("Step 2/3: Analyzing fit and gaps...")
    fit_score, skill_gaps = await analyze_fit_and_gaps(ctx)
    return ctx, fit_score, skill_gaps


def run_pipeline_through_gap_analysis_sync(
    resume_text: str,
    job_text: str,
) -> tuple[AnalysisContext, FitScore, SkillGapReport]:
    return asyncio.run(run_pipeline_through_gap_analysis(resume_text, job_text))


async def finalize_resume_cover_letter_and_save(
    ctx: AnalysisContext,
    fit_score: FitScore,
    skill_gaps: SkillGapReport,
    optimized_resume_markdown: str,
) -> FullAnalysis:
    """Step 3: post-process resume, cover letter, persist. ``optimized_resume_markdown`` is full Markdown."""
    optimized_resume = consolidate_small_skill_categories(optimized_resume_markdown)
    cover_letter_result = await _cover_letter_writer_llm(ctx)
    cover_letter = cover_letter_result.output

    result = FullAnalysis(
        fit_score=fit_score,
        skill_gaps=skill_gaps,
        optimized_resume=optimized_resume,
        cover_letter=cover_letter,
    )

    save_analysis(result, job_title=ctx.job_data.title, company=ctx.job_data.company)
    print("Done! Results saved to database.")
    return result


def finalize_resume_cover_letter_and_save_sync(
    ctx: AnalysisContext,
    fit_score: FitScore,
    skill_gaps: SkillGapReport,
    optimized_resume_markdown: str,
) -> FullAnalysis:
    return asyncio.run(
        finalize_resume_cover_letter_and_save(ctx, fit_score, skill_gaps, optimized_resume_markdown)
    )


def stream_optimized_resume_for_streamlit(ctx: AnalysisContext):
    """Sync iterator of resume deltas for ``st.write_stream``."""
    yield from stream_optimized_resume_text(ctx)


async def recalculate_fit_and_gaps(ctx: AnalysisContext) -> tuple[FitScore, SkillGapReport]:
    """Re-run scorer and gap analysis on an updated context (e.g. after user confirms skills)."""
    return await analyze_fit_and_gaps(ctx)


def recalculate_fit_and_gaps_sync(ctx: AnalysisContext) -> tuple[FitScore, SkillGapReport]:
    return asyncio.run(recalculate_fit_and_gaps(ctx))
