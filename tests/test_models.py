"""
Tests for all Pydantic models — no LLM calls, pure validation.
"""
import pytest
from pydantic import ValidationError
from src.models.resume import ResumeData, Skill, Experience
from src.models.job import JobRequirements, RequiredSkill
from src.models.analysis import FitScore, SkillGapReport, LearningItem, FullAnalysis


# ── Skill ─────────────────────────────────────────────────────────────────────

def test_skill_valid():
    skill = Skill(name="Python", category="programming", proficiency="advanced")
    assert skill.name == "Python"
    assert skill.proficiency == "advanced"

def test_skill_defaults():
    skill = Skill(name="Communication", category="soft_skill", proficiency="intermediate")
    assert skill.category == "soft_skill"


# ── ResumeData ────────────────────────────────────────────────────────────────

def test_resume_data_full():
    resume = ResumeData(
        name="Jane Doe",
        email="jane@test.com",
        skills=[Skill(name="Python", category="programming", proficiency="advanced")],
        experiences=[
            Experience(
                title="Engineer",
                company="Acme",
                duration="2022-present",
                highlights=["Built APIs", "Improved performance by 30%"],
            )
        ],
        education=["B.S. Computer Science — State University, 2021"],
        summary="Experienced backend developer.",
    )
    assert resume.name == "Jane Doe"
    assert len(resume.skills) == 1
    assert len(resume.experiences) == 1
    assert resume.experiences[0].highlights[1] == "Improved performance by 30%"

def test_resume_email_optional():
    resume = ResumeData(
        name="John",
        email="",
        skills=[],
        experiences=[],
        education=[],
        summary="",
    )
    assert resume.email == ""


# ── JobRequirements ───────────────────────────────────────────────────────────

def test_job_requirements_valid():
    job = JobRequirements(
        title="Senior Python Developer",
        company="TechCorp",
        required_skills=[
            RequiredSkill(name="Python", importance="required", category="programming"),
            RequiredSkill(name="Docker", importance="preferred", category="devops"),
        ],
        responsibilities=["Build APIs", "Mentor juniors"],
        experience_years=5,
        keywords=["Python", "REST", "CI/CD"],
    )
    assert job.title == "Senior Python Developer"
    assert len(job.required_skills) == 2
    assert job.required_skills[0].importance == "required"

def test_job_experience_years_defaults():
    job = JobRequirements(
        title="Developer",
        required_skills=[],
        responsibilities=[],
        keywords=[],
    )
    assert job.experience_years == 0
    assert job.company == ""


# ── FitScore ──────────────────────────────────────────────────────────────────

def test_fit_score_valid():
    score = FitScore(
        overall=75,
        skill_match=30,
        experience_alignment=25,
        keyword_coverage=20,
        strengths=["Python expertise", "REST API experience"],
        explanation="Good match with some gaps in DevOps.",
    )
    assert score.overall == 75
    assert score.skill_match + score.experience_alignment + score.keyword_coverage == 75

def test_fit_score_bounds():
    with pytest.raises(ValidationError):
        FitScore(
            overall=110,  # exceeds 100
            skill_match=50,  # exceeds 40
            experience_alignment=35,  # exceeds 30
            keyword_coverage=25,
            strengths=[],
            explanation="",
        )


# ── SkillGapReport ────────────────────────────────────────────────────────────

def test_skill_gap_report():
    report = SkillGapReport(
        missing_hard_skills=["Kubernetes", "Terraform"],
        missing_soft_skills=["Public speaking"],
        learning_roadmap=[
            LearningItem(
                skill="Kubernetes",
                priority="high",
                reason="Listed as required in job posting",
                suggestion="Complete the official Kubernetes fundamentals course",
            )
        ],
    )
    assert len(report.missing_hard_skills) == 2
    assert report.learning_roadmap[0].priority == "high"


# ── FullAnalysis ──────────────────────────────────────────────────────────────

def test_full_analysis_assembles():
    analysis = FullAnalysis(
        fit_score=FitScore(
            overall=70,
            skill_match=28,
            experience_alignment=22,
            keyword_coverage=20,
            strengths=["Python"],
            explanation="Decent match.",
        ),
        skill_gaps=SkillGapReport(
            missing_hard_skills=["Docker"],
            missing_soft_skills=[],
            learning_roadmap=[
                LearningItem(
                    skill="Docker",
                    priority="high",
                    reason="Required",
                    suggestion="Docker getting started guide",
                )
            ],
        ),
        optimized_resume="Jane Doe\n\nSKILLS\nPython...",
        cover_letter="Dear Hiring Team,\n\nI am excited...",
    )
    assert analysis.fit_score.overall == 70
    assert analysis.skill_gaps.missing_hard_skills[0] == "Docker"
    assert analysis.optimized_resume.startswith("Jane Doe")
    assert analysis.cover_letter.startswith("Dear")
    