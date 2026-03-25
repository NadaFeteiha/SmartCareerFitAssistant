"""Re-run fit scoring when resume skills/experience (markdown) changes."""

from __future__ import annotations

import asyncio

from src.agents.analyzer import AnalysisContext, score_candidate
from src.models.analysis import FitScore


def rescore_resume_draft_sync(ctx: AnalysisContext, markdown: str) -> FitScore:
    """Update context resume text and return a new ``FitScore`` (local LLM call)."""
    ctx.resume_text = markdown
    return asyncio.run(score_candidate(ctx))
