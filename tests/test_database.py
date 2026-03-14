"""
Tests for the SQLite database layer — no LLM calls, pure CRUD.
"""
import json
import os
import pytest
from src.db.database import init_db, get_connection
from src.db.repository import save_analysis, get_all_analyses
from src.models.analysis import FullAnalysis, FitScore, SkillGapReport, LearningItem

TEST_DB = "data/test_career.db"


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def isolated_test_db(monkeypatch):
    """
    Each test gets a fresh isolated database.
    Patches settings.db_path so the real DB is never touched.
    """
    from src import config
    monkeypatch.setattr(config.settings, "db_path", TEST_DB)
    init_db()
    yield
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)


def _make_full_analysis(score: int = 80) -> FullAnalysis:
    return FullAnalysis(
        fit_score=FitScore(
            overall=score,
            skill_match=32,
            experience_alignment=26,
            keyword_coverage=22,
            strengths=["Python", "FastAPI"],
            explanation="Strong backend match.",
        ),
        skill_gaps=SkillGapReport(
            missing_hard_skills=["Kubernetes"],
            missing_soft_skills=["Leadership"],
            learning_roadmap=[
                LearningItem(
                    skill="Kubernetes",
                    priority="medium",
                    reason="Preferred skill in JD",
                    suggestion="Kubernetes official docs",
                )
            ],
        ),
        optimized_resume="Jane Doe\nPython Developer...",
        cover_letter="Dear Hiring Team,\nI bring strong Python skills...",
    )


# ── Save ──────────────────────────────────────────────────────────────────────

def test_save_returns_row_id():
    analysis = _make_full_analysis()
    row_id = save_analysis(analysis, job_title="Senior Engineer", company="TechCorp")
    assert row_id == 1

def test_save_multiple_increments_id():
    save_analysis(_make_full_analysis(75), job_title="Engineer", company="CorpA")
    row_id = save_analysis(_make_full_analysis(85), job_title="Lead", company="CorpB")
    assert row_id == 2


# ── Retrieve ──────────────────────────────────────────────────────────────────

def test_get_all_analyses_empty():
    rows = get_all_analyses()
    assert rows == []

def test_get_all_analyses_after_save():
    save_analysis(_make_full_analysis(), job_title="Engineer", company="TechCorp")
    rows = get_all_analyses()
    assert len(rows) == 1
    assert rows[0]["overall_score"] == 80
    assert rows[0]["job_title"] == "Engineer"
    assert rows[0]["company"] == "TechCorp"

def test_get_all_analyses_newest_first():
    save_analysis(_make_full_analysis(60), job_title="Junior", company="A")
    save_analysis(_make_full_analysis(90), job_title="Senior", company="B")
    rows = get_all_analyses()
    assert rows[0]["job_title"] == "Senior"   # newest first
    assert rows[1]["job_title"] == "Junior"


# ── JSON fields ───────────────────────────────────────────────────────────────

def test_strengths_stored_as_json():
    save_analysis(_make_full_analysis(), job_title="Dev", company="X")
    rows = get_all_analyses()
    strengths = json.loads(rows[0]["strengths"])
    assert "Python" in strengths

def test_learning_roadmap_stored_as_json():
    save_analysis(_make_full_analysis(), job_title="Dev", company="X")
    rows = get_all_analyses()
    roadmap = json.loads(rows[0]["learning_roadmap"])
    assert len(roadmap) == 1
    assert roadmap[0]["skill"] == "Kubernetes"
    assert roadmap[0]["priority"] == "medium"


# ── Score fields ──────────────────────────────────────────────────────────────

def test_all_score_fields_persisted():
    save_analysis(_make_full_analysis(80), job_title="Dev", company="X")
    rows = get_all_analyses()
    r = rows[0]
    assert r["skill_score"] == 32
    assert r["experience_score"] == 26
    assert r["keyword_score"] == 22

def test_resume_and_cover_letter_persisted():
    save_analysis(_make_full_analysis(), job_title="Dev", company="X")
    rows = get_all_analyses()
    assert rows[0]["optimized_resume"].startswith("Jane Doe")
    assert rows[0]["cover_letter"].startswith("Dear Hiring Team")
    