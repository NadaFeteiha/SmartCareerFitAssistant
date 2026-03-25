"""
Pipeline orchestrator — runs all agents in sequence and persists results.

Step 1: Extract structured data (resume + job, ATS keywords included in job extraction).
Step 2: Enrich resume with previously saved user skills.
Step 3: Score fit and identify skill gaps (parallel-safe; run sequentially for simplicity).
Step 4: Generate optimized resume and cover letter.
Step 5: Persist to SQLite.
"""
from __future__ import annotations

import asyncio

from src.agents.analyzer import AnalysisContext, analyze_gaps, score_candidate
from src.agents.extractor import extract_job, extract_resume
from src.agents.generator import cover_letter_writer, resume_writer
from src.database.repository import get_user_skills, save_analysis
from src.models.analysis import FitScore, FullAnalysis, SkillGapReport
from src.models.resume import Skill
from src.utils.resume_sections import (
    consolidate_small_skill_categories,
    inject_skill_into_markdown,
)


async def run_pipeline(
    resume_text: str, job_text: str
) -> tuple[FullAnalysis, AnalysisContext]:
    """Run the full 5-step pipeline and return (FullAnalysis, AnalysisContext)."""

    # ── Step 1: Extract ───────────────────────────────────────────────────────
    print("Step 1/4: Extracting structured data...")
    resume_data, (job_data, top_ats_keywords) = await asyncio.gather(
        extract_resume(resume_text),
        extract_job(job_text),
    )

    # ── Step 2: Enrich with saved user skills ─────────────────────────────────
    if resume_data.name:
        saved_skills = get_user_skills(resume_data.name)
        existing = {s.name.lower() for s in resume_data.skills}
        for sk in saved_skills:
            if sk.lower() not in existing:
                resume_data.skills.append(
                    Skill(name=sk, category="hard_skill", proficiency="intermediate")
                )
                resume_text = inject_skill_into_markdown(resume_text, sk)
                existing.add(sk.lower())

    # Merge extracted keywords with top ATS keywords (deduped, capped at 35)
    merged_keywords = list(
        dict.fromkeys(top_ats_keywords + list(job_data.keywords))
    )[:35]
    job_data = job_data.model_copy(update={"keywords": merged_keywords})

    ctx = AnalysisContext(
        resume_text=resume_text,
        job_text=job_text,
        resume_data=resume_data,
        job_data=job_data,
    )

    # ── Step 3: Analyze ───────────────────────────────────────────────────────
    print("Step 2/4: Analyzing fit and skill gaps...")
    fit_score, skill_gaps = await asyncio.gather(
        score_candidate(ctx),
        analyze_gaps(ctx),
    )

    # ── Step 4: Generate ──────────────────────────────────────────────────────
    print("Step 3/4: Generating resume and cover letter...")
    optimized_resume_raw, cover_letter = await asyncio.gather(
        resume_writer.run(
            "Rewrite this resume for the target job. Include a tailored ## SUMMARY section "
            "(2-4 sentences), then EXPERIENCE, EDUCATION, and SKILLS.",
            deps=ctx,
        ),
        cover_letter_writer.run("Write a cover letter.", deps=ctx),
    )
    optimized_resume = consolidate_small_skill_categories(optimized_resume_raw.output)

    result = FullAnalysis(
        fit_score=fit_score,
        skill_gaps=skill_gaps,
        optimized_resume=optimized_resume,
        cover_letter=cover_letter.output,
    )

    # ── Step 5: Persist ───────────────────────────────────────────────────────
    print("Step 4/4: Saving results...")
    save_analysis(result, job_title=job_data.title, company=job_data.company)
    print("Done.")

    return result, ctx


async def recalculate_fit_and_gaps(
    ctx: AnalysisContext,
) -> tuple[FitScore, SkillGapReport]:
    """Re-run fit score and gap analysis on the current context (e.g. after resume edits)."""
    new_fit, new_gaps = await asyncio.gather(
        score_candidate(ctx),
        analyze_gaps(ctx),
    )
    return new_fit, new_gaps


def recalculate_fit_and_gaps_sync(
    ctx: AnalysisContext,
) -> tuple[FitScore, SkillGapReport]:
    """Synchronous wrapper for Streamlit callbacks."""
    return asyncio.run(recalculate_fit_and_gaps(ctx))


def run_pipeline_sync(
    resume_text: str, job_text: str
) -> tuple[FullAnalysis, AnalysisContext]:
    """Synchronous wrapper for Streamlit (which cannot await coroutines directly)."""
    return asyncio.run(run_pipeline(resume_text, job_text))
