"""Optional Ollama embedding similarity between JD required skills and resume skills."""

from __future__ import annotations

import logging
import math
from typing import Sequence

import httpx

from src.config import settings

logger = logging.getLogger(__name__)


def _ollama_api_root() -> str:
    base = (settings.ollama_base_url or "").rstrip("/")
    if base.endswith("/v1"):
        base = base[:-3].rstrip("/")
    return base or "http://localhost:11434"


async def _embed_one(client: httpx.AsyncClient, text: str) -> list[float] | None:
    try:
        r = await client.post(
            f"{_ollama_api_root()}/api/embeddings",
            json={"model": settings.ollama_model, "prompt": text},
            timeout=30.0,
        )
        r.raise_for_status()
        data = r.json()
        emb = data.get("embedding")
        if isinstance(emb, list) and emb:
            return [float(x) for x in emb]
    except Exception as e:
        logger.debug("Ollama embedding request failed: %s", e)
    return None


def _cosine(a: Sequence[float], b: Sequence[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


async def build_skill_match_summary(
    candidate_skill_names: list[str],
    required_skill_names: list[str],
) -> str:
    """
    Return a short bullet list of top semantic JD↔resume skill pairs for prompt context.
    Empty string if embeddings are disabled or unavailable.
    """
    if not settings.skill_embedding_enabled:
        return ""
    cand = sorted({(s or "").strip() for s in candidate_skill_names if (s or "").strip()}, key=len)[
        : settings.skill_embedding_max_skill_terms
    ]
    req = sorted({(s or "").strip() for s in required_skill_names if (s or "").strip()}, key=len)[
        : settings.skill_embedding_max_skill_terms
    ]
    if not cand or not req:
        return ""

    async with httpx.AsyncClient() as client:
        cand_emb: dict[str, list[float]] = {}
        for name in cand:
            e = await _embed_one(client, name)
            if e:
                cand_emb[name] = e
        if not cand_emb:
            return ""

        lines: list[str] = []
        floor = settings.skill_embedding_similarity_floor
        max_pairs = settings.skill_embedding_max_pairs_in_prompt

        for rname in req:
            if len(lines) >= max_pairs:
                break
            re_vec = await _embed_one(client, rname)
            if not re_vec:
                continue
            best_c: str | None = None
            best_sim = -1.0
            for cname, cvec in cand_emb.items():
                sim = _cosine(re_vec, cvec)
                if sim > best_sim:
                    best_sim = sim
                    best_c = cname
            if best_c is not None and best_sim >= floor:
                lines.append(f"- JD '{rname}' ↔ candidate '{best_c}' (cosine≈{best_sim:.2f})")

        if not lines:
            return ""

        return "Semantic skill alignment (embedding similarity; use alongside structured lists):\n" + "\n".join(lines)
