from pydantic import BaseModel, Field, model_validator


class RequiredSkill(BaseModel):
    name: str
    importance: str = Field(default="required", description="'required' or 'preferred'")
    category: str = ""

    @model_validator(mode="before")
    @classmethod
    def _coerce(cls, data):
        if isinstance(data, str):
            return {"name": data}
        if isinstance(data, dict):
            if data.get("importance") in (None, ""):
                data["importance"] = "required"
            if data.get("category") is None:
                data["category"] = ""
        return data


class JobRequirements(BaseModel):
    """Structured extraction from a job description."""
    title: str = ""
    company: str = ""
    required_skills: list[RequiredSkill] = Field(default_factory=list)
    responsibilities: list[str] = Field(default_factory=list)
    experience_years: int = 0
    keywords: list[str] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def _coerce(cls, data):
        if isinstance(data, dict):
            for key in ("title", "company"):
                if data.get(key) is None:
                    data[key] = ""
            for key in ("required_skills", "responsibilities", "keywords"):
                if data.get(key) is None:
                    data[key] = []
            if data.get("experience_years") is None:
                data["experience_years"] = 0
        return data
