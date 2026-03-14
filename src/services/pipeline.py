import asyncio
from src.agents.extractor import extract_resume, extract_job
from src.agents.analyzer import score_candidate, analyze_gaps, AnalysisContext
from src.agents.generator import resume_writer, cover_letter_writer
from src.models.analysis import FullAnalysis
from src.db.repository import save_analysis


async def run_pipeline(resume_text: str, job_text: str) -> FullAnalysis:
    """
    One pipeline, four outputs.
    Step 1: Extract structured data from resume and job description.
    Step 2: Score fit and identify skill gaps.
    Step 3: Generate optimized resume and cover letter.
    Step 4: Persist results to SQLite.
    """

    print("Step 1/3: Extracting structured data...")
    resume_data = await extract_resume(resume_text)
    job_data = await extract_job(job_text)

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
    optimized_resume = (await resume_writer.run("Rewrite this resume.", deps=ctx)).output
    cover_letter = (await cover_letter_writer.run("Write a cover letter.", deps=ctx)).output

    result = FullAnalysis(
        fit_score=fit_score,
        skill_gaps=skill_gaps,
        optimized_resume=optimized_resume,
        cover_letter=cover_letter,
    )

    save_analysis(result, job_title=job_data.title, company=job_data.company)
    print("Done! Results saved to database.")

    return result


def run_pipeline_sync(resume_text: str, job_text: str) -> FullAnalysis:
    """Synchronous wrapper for use in Streamlit."""
    return asyncio.run(run_pipeline(resume_text, job_text))