"""Shared dependency object for scorer, gap, and generator agents."""

from __future__ import annotations

from dataclasses import dataclass, field

from src.models.job import JobRequirements
from src.models.resume import ResumeData


@dataclass
class AnalysisContext:
    resume_text: str
    job_text: str
    resume_data: ResumeData
    job_data: JobRequirements
    # Pre-computed skill alignment summary; always populated by build_analysis_context.
    skill_match_summary: str = field(default="")
