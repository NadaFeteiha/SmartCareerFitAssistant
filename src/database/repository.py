import json

from src.database.database import get_connection
from src.models.analysis import FullAnalysis


def save_analysis(analysis: FullAnalysis, job_title: str = "", company: str = "") -> int:
    """Save a FullAnalysis to the database. Returns the new row ID."""
    conn = get_connection()
    try:
        cursor = conn.execute(
            """INSERT INTO analyses
            (job_title, company, overall_score, skill_score, experience_score,
            keyword_score, strengths, missing_skills, learning_roadmap,
            optimized_resume, cover_letter)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                job_title,
                company,
                analysis.fit_score.overall,
                analysis.fit_score.skill_match,
                analysis.fit_score.experience_alignment,
                analysis.fit_score.keyword_coverage,
                json.dumps(analysis.fit_score.strengths),
                json.dumps(analysis.skill_gaps.missing_hard_skills),
                json.dumps([item.model_dump() for item in analysis.skill_gaps.learning_roadmap]),
                analysis.optimized_resume,
                analysis.cover_letter,
            ),
        )
        conn.commit()
        row_id = cursor.lastrowid
        return row_id
    finally:
        conn.close()


def get_all_analyses() -> list[dict]:
    """Fetch all saved analyses, newest first (by insert id)."""
    conn = get_connection()
    try:
        rows = conn.execute("SELECT * FROM analyses ORDER BY id DESC").fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()

def add_user_skill(user_name: str, skill_name: str) -> None:
    """Save a confirmed skill for a user."""
    if not user_name or not skill_name:
        return
    conn = get_connection()
    try:
        conn.execute(
            "INSERT OR IGNORE INTO user_skills (user_name, skill_name) VALUES (?, ?)",
            (user_name.strip(), skill_name.strip())
        )
        conn.commit()
    finally:
        conn.close()

def get_user_skills(user_name: str) -> list[str]:
    """Retrieve all permanently confirmed skills for a specific user."""
    if not user_name:
        return []
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT skill_name FROM user_skills WHERE user_name = ? ORDER BY skill_name COLLATE NOCASE",
            (user_name.strip(),),
        ).fetchall()
        return [r["skill_name"] for r in rows]
    finally:
        conn.close()
