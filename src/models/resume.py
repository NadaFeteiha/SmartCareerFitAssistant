from pydantic import BaseModel, Field

"""
This class represents the structured extraction from a raw resume.
It is the output of the resume parsing step, and the input to the matching step.

it includes the candidate's name, contact information, skills, work experiences, education, and a summary.
using this structured data, we can compare it against the structured job requirements to determine how well the candidate matches the job.
"""

class Skill(BaseModel):
    name: str
    category: str = Field(description="e.g. 'programming', 'data', 'soft_skill'")
    proficiency: str = Field(default="intermediate", description="'beginner', 'intermediate', or 'advanced'")

class Experience(BaseModel):
    title: str
    company: str
    duration: str
    highlights: list[str]

class ResumeData(BaseModel):
    """Structured extraction from a raw resume."""
    name: str
    email: str = ""
    skills: list[Skill]
    experiences: list[Experience]
    education: list[str]
    summary: str