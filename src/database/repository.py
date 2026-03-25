"""SQLite repository — save analyses and manage per-user confirmed skills."""
from __future__ import annotations

import json

from src.database.database import get_connection
from src.models.analysis import FullAnalysis


def get_all_analyses() -> list:
    """Return all analysis rows, newest first (for tests / future history UI)."""
    conn = get_connection()
    rows = conn.execute(
        """
        SELECT id, job_title, company, overall_score, skill_score, experience_score,
               keyword_score, strengths, missing_skills, learning_roadmap,
               optimized_resume, cover_letter, created_at
        FROM analyses
        ORDER BY id DESC
        """
    ).fetchall()
    conn.close()
    return list(rows)


def save_analysis(
    analysis: FullAnalysis, job_title: str = "", company: str = ""
) -> int:
    """Persist a FullAnalysis. Returns the new row ID."""
    conn = get_connection()
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
            json.dumps(
                [item.model_dump() for item in analysis.skill_gaps.learning_roadmap]
            ),
            analysis.optimized_resume,
            analysis.cover_letter,
        ),
    )
    conn.commit()
    row_id = cursor.lastrowid
    conn.close()
    return row_id  # type: ignore[return-value]


def add_user_skill(user_name: str, skill_name: str) -> None:
    """Persist a confirmed skill for a user (idempotent)."""
    if not user_name or not skill_name:
        return
    conn = get_connection()
    conn.execute(
        "INSERT OR IGNORE INTO user_skills (user_name, skill_name) VALUES (?, ?)",
        (user_name.strip(), skill_name.strip()),
    )
    conn.commit()
    conn.close()


def get_user_skills(user_name: str) -> list[str]:
    """Return all confirmed skills for a user, sorted case-insensitively."""
    if not user_name:
        return []
    conn = get_connection()
    rows = conn.execute(
        "SELECT skill_name FROM user_skills WHERE user_name = ?"
        " ORDER BY skill_name COLLATE NOCASE",
        (user_name.strip(),),
    ).fetchall()
    conn.close()
    return [r["skill_name"] for r in rows]
