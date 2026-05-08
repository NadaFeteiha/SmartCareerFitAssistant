import json

from src.database.database import get_connection
from src.models.analysis import FullAnalysis


def save_analysis(
    analysis: FullAnalysis,
    job_title: str = "",
    company: str = "",
    user_id: int | None = None,
) -> int:
    """Save a FullAnalysis to the database. Returns the new row ID."""
    conn = get_connection()
    cursor = conn.execute(
        """INSERT INTO analyses
        (user_id, job_title, company, overall_score, skill_score, experience_score,
        keyword_score, strengths, missing_skills, learning_roadmap,
        optimized_resume, cover_letter)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            user_id,
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
    conn.close()
    return row_id


def get_resume(user_id: int) -> str | None:
    conn = get_connection()
    row = conn.execute(
        "SELECT content FROM resumes WHERE user_id = ?", (user_id,),
    ).fetchone()
    conn.close()
    return row["content"] if row else None


def upsert_resume(user_id: int, content: str) -> None:
    conn = get_connection()
    conn.execute(
        """INSERT INTO resumes (user_id, content, updated_at)
           VALUES (?, ?, CURRENT_TIMESTAMP)
           ON CONFLICT(user_id) DO UPDATE SET
               content = excluded.content,
               updated_at = CURRENT_TIMESTAMP""",
        (user_id, content),
    )
    conn.commit()
    conn.close()


def delete_resume(user_id: int) -> None:
    conn = get_connection()
    conn.execute("DELETE FROM resumes WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()


def get_all_analyses() -> list[dict]:
    """Fetch all saved analyses, newest first (by insert id)."""
    conn = get_connection()
    rows = conn.execute("SELECT * FROM analyses ORDER BY id DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]

def add_user_skill(user_name: str, skill_name: str) -> None:
    """Save a confirmed skill for a user."""
    if not user_name or not skill_name:
        return
    conn = get_connection()
    conn.execute(
        "INSERT OR IGNORE INTO user_skills (user_name, skill_name) VALUES (?, ?)",
        (user_name.strip(), skill_name.strip())
    )
    conn.commit()
    conn.close()

def get_user_skills(user_name: str) -> list[str]:
    """Retrieve all permanently confirmed skills for a specific user."""
    if not user_name:
        return []
    conn = get_connection()
    rows = conn.execute(
        "SELECT skill_name FROM user_skills WHERE user_name = ? ORDER BY skill_name COLLATE NOCASE",
        (user_name.strip(),),
    ).fetchall()
    conn.close()
    return [r["skill_name"] for r in rows]


def upsert_user_skill_confirmation(user_id: int, skill_name: str, has_skill: bool) -> None:
    """Persist whether a user has a specific skill."""
    normalized_skill = (skill_name or "").strip()
    if not normalized_skill:
        return
    conn = get_connection()
    conn.execute(
        """INSERT INTO user_skill_confirmations (user_id, skill_name, has_skill, updated_at)
           VALUES (?, ?, ?, CURRENT_TIMESTAMP)
           ON CONFLICT(user_id, skill_name) DO UPDATE SET
             has_skill = excluded.has_skill,
             updated_at = CURRENT_TIMESTAMP""",
        (user_id, normalized_skill, 1 if has_skill else 0),
    )
    conn.commit()
    conn.close()


def get_user_skill_confirmations(user_id: int) -> dict[str, bool]:
    """Return {skill_name: has_skill} decisions for one user."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT skill_name, has_skill FROM user_skill_confirmations WHERE user_id = ?",
        (user_id,),
    ).fetchall()
    conn.close()
    return {row["skill_name"]: bool(row["has_skill"]) for row in rows}


def get_user_confirmed_skills(user_id: int) -> list[str]:
    """Return skills explicitly confirmed as present by the user."""
    conn = get_connection()
    rows = conn.execute(
        """SELECT skill_name
           FROM user_skill_confirmations
           WHERE user_id = ? AND has_skill = 1
           ORDER BY skill_name COLLATE NOCASE""",
        (user_id,),
    ).fetchall()
    conn.close()
    return [row["skill_name"] for row in rows]


def get_user_profile(user_id: int) -> dict[str, str]:
    """Get persisted profile contact fields for one user."""
    conn = get_connection()
    row = conn.execute(
        "SELECT phone, linkedin, github FROM user_profiles WHERE user_id = ?",
        (user_id,),
    ).fetchone()
    conn.close()
    if not row:
        return {"phone": "", "linkedin": "", "github": ""}
    return {
        "phone": row["phone"] or "",
        "linkedin": row["linkedin"] or "",
        "github": row["github"] or "",
    }


def upsert_user_profile(user_id: int, phone: str = "", linkedin: str = "", github: str = "") -> None:
    """Persist profile contact fields for one user."""
    conn = get_connection()
    conn.execute(
        """INSERT INTO user_profiles (user_id, phone, linkedin, github, updated_at)
           VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
           ON CONFLICT(user_id) DO UPDATE SET
             phone = excluded.phone,
             linkedin = excluded.linkedin,
             github = excluded.github,
             updated_at = CURRENT_TIMESTAMP""",
        (
            user_id,
            (phone or "").strip(),
            (linkedin or "").strip(),
            (github or "").strip(),
        ),
    )
    conn.commit()
    conn.close()
