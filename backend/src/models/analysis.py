from pydantic import BaseModel, Field, model_validator


def _clamp_int(value, min_val: int, max_val: int) -> int:
    try:
        iv = int(value)
    except Exception:
        return min_val
    return max(min_val, min(max_val, iv))


class FitScore(BaseModel):
    """Scoring breakdown for a resume vs. job description."""
    overall: int = Field(ge=0, le=100)
    skill_match: int = Field(ge=0, le=40)
    experience_alignment: int = Field(ge=0, le=30)
    keyword_coverage: int = Field(ge=0, le=30)
    strengths: list[str] = Field(default_factory=list)
    explanation: str = ""

    @model_validator(mode="before")
    @classmethod
    def _normalize(cls, data):
        if not isinstance(data, dict):
            return data
        data["skill_match"] = _clamp_int(data.get("skill_match", 0), 0, 40)
        data["experience_alignment"] = _clamp_int(data.get("experience_alignment", 0), 0, 30)
        data["keyword_coverage"] = _clamp_int(data.get("keyword_coverage", 0), 0, 30)
        data["overall"] = data["skill_match"] + data["experience_alignment"] + data["keyword_coverage"]

        strengths = data.get("strengths")
        if strengths in (None, ""):
            data["strengths"] = []
        elif isinstance(strengths, str):
            data["strengths"] = [strengths]

        if data.get("explanation") is None:
            data["explanation"] = ""
        return data


class LearningItem(BaseModel):
    skill: str
    priority: str = Field(description="'high', 'medium', or 'low'")
    reason: str
    suggestion: str


class MissingRequirements(BaseModel):
    """Structured gap list: skills, experience themes, and JD keywords absent from the resume."""
    missing_skills: list[str] = Field(default_factory=list)
    missing_experience: list[str] = Field(default_factory=list)
    missing_keywords: list[str] = Field(default_factory=list)


class SkillGapReport(BaseModel):
    """Missing skills, detailed requirements gap, and learning roadmap."""
    missing_hard_skills: list[str] = Field(default_factory=list)
    missing_soft_skills: list[str] = Field(default_factory=list)
    missing_requirements: MissingRequirements = Field(default_factory=MissingRequirements)
    learning_roadmap: list[LearningItem] = Field(default_factory=list)


class FullAnalysis(BaseModel):
    """Complete pipeline output — all features in one model."""
    fit_score: FitScore
    skill_gaps: SkillGapReport
    optimized_resume: str
    cover_letter: str
