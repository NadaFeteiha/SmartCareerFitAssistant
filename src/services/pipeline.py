import asyncio

from src.agents.analyzer import AnalysisContext, analyze_gaps, score_candidate
from src.agents.extractor import extract_job, extract_resume
from src.agents.generator import cover_letter_writer, resume_writer
from src.agents.keyword_optimizer import extract_top_jd_keywords
from src.database.repository import get_user_skills, save_analysis
from src.models.analysis import FitScore, FullAnalysis, SkillGapReport
from src.models.resume import Skill
from src.utils.resume_sections import consolidate_small_skill_categories, inject_skill_into_markdown


async def run_pipeline(resume_text: str, job_text: str) -> tuple[FullAnalysis, AnalysisContext]:
    """
    One pipeline, four outputs.
    Step 1: Extract structured data from resume and job description.
    Step 2: Score fit and identify skill gaps.
    Step 3: Generate optimized resume and cover letter.
    Step 4: Persist results to SQLite.
    """

    print("Step 1/3: Extracting structured data...")
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
    merged_keywords = list(dict.fromkeys(top_kw + list(job_data.keywords)))[:35]
    job_data = job_data.model_copy(update={"keywords": merged_keywords})

    ctx = AnalysisContext(
        resume_text=resume_text,
        job_text=job_text,
        resume_data=resume_data,
        job_data=job_data,
    )

    print("Step 2/3: Analyzing fit and gaps...")
    fit_score = await score_candidate(ctx)
    skill_gaps = await analyze_gaps(ctx)

    print("Step 3/3: Generating resume and cover letter...")
    optimized_resume = (
        await resume_writer.run(
            "Rewrite this resume for the target job. Include a tailored ## SUMMARY section "
            "(2–4 sentences) based on the resume and job description, then EXPERIENCE, EDUCATION, and SKILLS.",
            deps=ctx,
        )
    ).output
    optimized_resume = consolidate_small_skill_categories(optimized_resume)
    cover_letter = (await cover_letter_writer.run("Write a cover letter.", deps=ctx)).output

    result = FullAnalysis(
        fit_score=fit_score,
        skill_gaps=skill_gaps,
        optimized_resume=optimized_resume,
        cover_letter=cover_letter,
    )

    save_analysis(result, job_title=job_data.title, company=job_data.company)
    print("Done! Results saved to database.")

    return result, ctx


def run_pipeline_sync(resume_text: str, job_text: str) -> tuple[FullAnalysis, AnalysisContext]:
    """Synchronous wrapper for use in Streamlit."""
    return asyncio.run(run_pipeline(resume_text, job_text))


async def recalculate_fit_and_gaps(ctx: AnalysisContext) -> tuple[FitScore, SkillGapReport]:
    """Re-run scorer and gap analysis on an updated context (e.g. after user confirms skills)."""
    fit_score = await score_candidate(ctx)
    skill_gaps = await analyze_gaps(ctx)
    return fit_score, skill_gaps


def recalculate_fit_and_gaps_sync(ctx: AnalysisContext) -> tuple[FitScore, SkillGapReport]:
    return asyncio.run(recalculate_fit_and_gaps(ctx))