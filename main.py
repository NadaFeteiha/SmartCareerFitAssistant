"""
CLI entry point — useful for testing the pipeline without the UI.
Usage: uv run python main.py
"""
import asyncio
from src.db.database import init_db
from src.services.pipeline import run_pipeline

SAMPLE_RESUME = """
John Smith
john.smith@email.com

SUMMARY
Software engineer with 3 years of experience in Python and web development.

SKILLS
Python, FastAPI, PostgreSQL, Git, REST APIs, Docker (basic)

EXPERIENCE
Junior Backend Developer — Acme Corp (2022–present)
- Built REST APIs using FastAPI and PostgreSQL
- Wrote unit tests with pytest, achieving 80% coverage
- Collaborated with frontend team on 3 product features

EDUCATION
B.S. Computer Science — State University, 2021
"""

SAMPLE_JD = """
Senior Python Developer — TechCorp

We are looking for a Python developer to join our data engineering team.

Required Skills:
- Python (5+ years)
- SQL and database design
- REST API development
- Docker and Kubernetes
- CI/CD pipelines

Preferred:
- FastAPI or Django
- Cloud experience (AWS or GCP)
- Data pipeline experience (Airflow, Spark)

Responsibilities:
- Design and maintain data pipelines
- Build internal APIs
- Mentor junior developers
"""

async def main():
    init_db()
    print("Running pipeline with sample data...\n")
    result = await run_pipeline(SAMPLE_RESUME, SAMPLE_JD)

    print(f"\n{'='*50}")
    print(f"FIT SCORE: {result.fit_score.overall}/100")
    print(f"  Skills:     {result.fit_score.skill_match}/40")
    print(f"  Experience: {result.fit_score.experience_alignment}/30")
    print(f"  Keywords:   {result.fit_score.keyword_coverage}/30")
    print(f"\nStrengths:")
    for s in result.fit_score.strengths:
        print(f"  + {s}")
    print(f"\nMissing skills:")
    for s in result.skill_gaps.missing_hard_skills:
        print(f"  - {s}")
    print(f"\nCover letter preview:")
    print(result.cover_letter[:300] + "...")

if __name__ == "__main__":
    asyncio.run(main())
    