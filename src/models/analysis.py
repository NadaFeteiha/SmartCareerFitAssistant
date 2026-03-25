from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator


class FitScore(BaseModel):
    """Scoring breakdown for a resume vs. job description."""
    overall: int = Field(ge=0, le=100)
    skill_match: int = Field(ge=0, le=40)
    experience_alignment: int = Field(ge=0, le=30)
    keyword_coverage: int = Field(ge=0, le=30)
    strengths: list[str]
    explanation: str

    @model_validator(mode="after")
    def sync_overall_with_sub_scores(self) -> "FitScore":
        computed = self.skill_match + self.experience_alignment + self.keyword_coverage
        self.overall = min(computed, 100)
        return self


class LearningItem(BaseModel):
    skill: str
    priority: Literal["high", "medium", "low"]
    reason: str
    suggestion: str

    @field_validator("priority", mode="before")
    @classmethod
    def normalize_priority(cls, v: object) -> str:
        if v is None:
            return "medium"
        s = str(v).strip().lower()
        if s in ("high", "medium", "low"):
            return s
        if s in ("critical", "urgent", "highest"):
            return "high"
        if s in ("med", "normal", "mid"):
            return "medium"
        if s in ("lo", "minimum"):
            return "low"
        return "medium"


class MissingRequirements(BaseModel):
    """Structured gap list: skills, experience themes, and JD keywords absent from the resume."""
    missing_skills: list[str] = Field(default_factory=list)
    missing_experience: list[str] = Field(default_factory=list)
    missing_keywords: list[str] = Field(default_factory=list)


class SkillGapReport(BaseModel):
    """Missing skills, detailed requirements gap, and learning roadmap."""
    missing_hard_skills: list[str]
    missing_soft_skills: list[str]
    missing_requirements: MissingRequirements = Field(default_factory=MissingRequirements)
    learning_roadmap: list[LearningItem]


class FullAnalysis(BaseModel):
    """Complete pipeline output — all features in one model."""
    fit_score: FitScore
    skill_gaps: SkillGapReport
    optimized_resume: str
    cover_letter: str
