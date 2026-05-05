from pydantic import BaseModel, Field


class RequiredSkill(BaseModel):
    name: str
    importance: str = Field(description="'required' or 'preferred'")
    category: str = ""


class JobRequirements(BaseModel):
    """Structured extraction from a job description."""
    title: str
    company: str = ""
    required_skills: list[RequiredSkill] = []
    responsibilities: list[str] = []
    experience_years: int = 0
    keywords: list[str] = []