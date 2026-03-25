from typing import Literal

from pydantic import BaseModel, field_validator


class RequiredSkill(BaseModel):
    name: str
    importance: Literal["required", "preferred"]
    category: str = ""

    @field_validator("importance", mode="before")
    @classmethod
    def normalize_importance(cls, v: object) -> str:
        """Coerce common extractor / LLM variants to allowed literals."""
        if v is None:
            return "required"
        s = str(v).strip().lower()
        if s in ("preferred", "optional", "nice to have", "nice-to-have", "nice_to_have", "desirable"):
            return "preferred"
        return "required"


class JobRequirements(BaseModel):
    """Structured extraction from a job description."""
    title: str
    company: str = ""
    required_skills: list[RequiredSkill] = []
    responsibilities: list[str] = []
    experience_years: int = 0
    keywords: list[str] = []
