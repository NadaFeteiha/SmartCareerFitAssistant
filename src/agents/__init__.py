"""
Public surface of the agents package.

Removed:
  - scorer / gap_analyzer  (internal implementation details, not public API)
  - resume_extractor / job_extractor  (same reason; use extract_resume / extract_job)
  - extract_top_jd_keywords  (merged into extract_job; keyword_optimizer.py deleted)
"""
from .analyzer import AnalysisContext, analyze_gaps, score_candidate
from .extractor import extract_job, extract_resume
from .generator import cover_letter_writer, resume_writer
from .utils import unwrap_llm_json

__all__ = [
    "AnalysisContext",
    "analyze_gaps",
    "score_candidate",
    "extract_resume",
    "extract_job",
    "resume_writer",
    "cover_letter_writer",
    "unwrap_llm_json",
]
