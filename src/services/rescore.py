"""Re-run fit scoring when resume skills/experience (markdown) changes."""

from __future__ import annotations

import asyncio
from dataclasses import replace

from src.agents.analyzer import score_candidate
from src.agents.context import AnalysisContext
from src.models.analysis import FitScore


def rescore_resume_draft_sync(ctx: AnalysisContext, markdown: str) -> FitScore:
    """Return a new ``FitScore`` without mutating ``ctx`` (local LLM call)."""
    updated_ctx = replace(ctx, resume_text=markdown)
    return asyncio.run(score_candidate(updated_ctx))
