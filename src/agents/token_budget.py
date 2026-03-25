"""Estimate token counts and truncate text for LLM prompts (Unicode-safe vs raw char caps)."""

from __future__ import annotations

_encoding: object | None = None


def _get_encoding():
    global _encoding
    if _encoding is None:
        try:
            import tiktoken

            _encoding = tiktoken.get_encoding("cl100k_base")
        except Exception:
            _encoding = False
    if _encoding is False:
        return None
    return _encoding


def estimate_tokens(text: str) -> int:
    if not text:
        return 0
    enc = _get_encoding()
    if enc is not None:
        return len(enc.encode(text))
    # Rough heuristic: non‑Latin text often uses more tokens per character than ASCII.
    return max(1, len(text) // 4)


def truncate_to_token_budget(text: str, max_tokens: int) -> str:
    if max_tokens <= 0 or not text:
        return ""
    if estimate_tokens(text) <= max_tokens:
        return text
    lo, hi = 0, len(text)
    best = 0
    while lo <= hi:
        mid = (lo + hi) // 2
        if estimate_tokens(text[:mid]) <= max_tokens:
            best = mid
            lo = mid + 1
        else:
            hi = mid - 1
    return text[:best]
