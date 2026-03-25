from pydantic import BaseModel, Field


class FitScore(BaseModel):
    """Scoring breakdown for a resume vs. job description."""
    overall: int = Field(ge=0, le=100)
    skill_match: int = Field(ge=0, le=40)
    experience_alignment: int = Field(ge=0, le=30)
    keyword_coverage: int = Field(ge=0, le=30)
    strengths: list[str]
    explanation: str


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
