from pydantic import BaseModel, Field

"""
Models for the analysis pipeline output. These are used to structure the data returned by the API endpoints.
it includes:- FitScore: A breakdown of the resume's fit against the job description, with an overall score and sub-scores for skills, experience, and keywords.
- SkillGapReport: A report on missing hard and soft skills, along with a learning roadmap that prioritizes which skills to acquire and why.
- FullAnalysis: A comprehensive model that combines the fit score, skill gap report, optimized resume, and cover letter into a single structured response for the API.

"""

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

class SkillGapReport(BaseModel):
    """Missing skills and learning recommendations."""
    missing_hard_skills: list[str]
    missing_soft_skills: list[str]
    learning_roadmap: list[LearningItem]

class FullAnalysis(BaseModel):
    """Complete pipeline output — all 4 features in one model."""
    fit_score: FitScore
    skill_gaps: SkillGapReport
    optimized_resume: str
    cover_letter: str
