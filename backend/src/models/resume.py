from pydantic import BaseModel, Field, model_validator


class Skill(BaseModel):
    name: str
    category: str = Field(default="other", description="e.g. 'programming', 'data', 'soft_skill'")
    proficiency: str = Field(default="intermediate", description="'beginner', 'intermediate', or 'advanced'")

    @model_validator(mode="before")
    @classmethod
    def _coerce(cls, data):
        # Small models occasionally emit a bare string instead of an object.
        if isinstance(data, str):
            return {"name": data}
        if isinstance(data, dict):
            if data.get("category") in (None, ""):
                data["category"] = "other"
            if data.get("proficiency") in (None, ""):
                data["proficiency"] = "intermediate"
        return data


class Experience(BaseModel):
    title: str
    company: str = ""
    duration: str = ""
    highlights: list[str] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def _coerce(cls, data):
        if isinstance(data, dict):
            if data.get("highlights") is None:
                data["highlights"] = []
            if data.get("company") is None:
                data["company"] = ""
            if data.get("duration") is None:
                data["duration"] = ""
        return data


class ResumeData(BaseModel):
    """Structured extraction from a raw resume."""
    name: str = ""
    email: str = ""
    skills: list[Skill] = Field(default_factory=list)
    experiences: list[Experience] = Field(default_factory=list)
    education: list[str] = Field(default_factory=list)
    summary: str = ""

    @model_validator(mode="before")
    @classmethod
    def _coerce(cls, data):
        if isinstance(data, dict):
            for key in ("name", "email", "summary"):
                if data.get(key) is None:
                    data[key] = ""
            for key in ("skills", "experiences", "education"):
                if data.get(key) is None:
                    data[key] = []
        return data
