"""Tests for gap-report filtering heuristics — no LLM."""

from types import SimpleNamespace

from src.models.analysis import LearningItem, MissingRequirements, SkillGapReport
from src.utils.skill_validation import filter_skill_gap_report, skill_evidence_on_resume


def test_skill_evidence_on_resume_text_substring():
    assert skill_evidence_on_resume("Python", "Used Python and FastAPI daily", [])


def test_skill_evidence_structured_alias():
    assert skill_evidence_on_resume("React.js", "frontend work", ["React"])


def test_filter_skill_gap_report_drops_evidence_skills():
    ctx = SimpleNamespace(
        resume_text="Expert in Kubernetes and Docker orchestration.",
        resume_data=SimpleNamespace(skills=[SimpleNamespace(name="SQL")]),
        job_data=SimpleNamespace(company="Acme"),
    )
    report = SkillGapReport(
        missing_hard_skills=["Kubernetes", "COBOL"],
        missing_soft_skills=[],
        missing_requirements=MissingRequirements(
            missing_skills=["Kubernetes"],
            missing_experience=[],
            missing_keywords=[],
        ),
        learning_roadmap=[LearningItem(skill="Kubernetes", priority="high", reason="r", suggestion="s")],
    )
    out = filter_skill_gap_report(ctx, report)
    assert "Kubernetes" not in out.missing_hard_skills
    assert "COBOL" in out.missing_hard_skills
    assert out.missing_requirements.missing_skills == []
    assert out.learning_roadmap == []


def test_truncate_to_token_budget_short():
    from src.agents.token_budget import truncate_to_token_budget

    assert truncate_to_token_budget("hello", 100) == "hello"
