"""Extract resume sections used for scoring fingerprinting (skills + experience only)."""

from __future__ import annotations

import hashlib
import re


_H2 = re.compile(r"^##\s+(.+?)\s*$", re.I | re.M)

# Headings treated as "experience" for scoring-relevant edits
_EXPERIENCE_HEADINGS = frozenset(
    {
        "experience",
        "work experience",
        "professional experience",
        "employment",
        "employment history",
    }
)
_SKILLS_HEADINGS = frozenset({"skills", "technical skills", "core competencies"})


def _normalize_heading(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def extract_h2_section(markdown: str, heading_name: str) -> str:
    """Return body under ``## Heading`` until the next ``##`` or EOF."""
    if not markdown:
        return ""
    target = _normalize_heading(heading_name)
    matches = list(_H2.finditer(markdown))
    for i, m in enumerate(matches):
        title = _normalize_heading(m.group(1))
        if title != target:
            continue
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(markdown)
        return markdown[start:end].strip()
    return ""


def scoring_relevant_excerpt(markdown: str) -> str:
    """Concatenate skills + experience blocks for change detection."""
    if not markdown:
        return ""
    parts: list[str] = []
    for h in _SKILLS_HEADINGS:
        block = extract_h2_section(markdown, h)
        if block:
            parts.append(f"## {h.upper()}\n{block}")
    for h in _EXPERIENCE_HEADINGS:
        block = extract_h2_section(markdown, h)
        if block:
            parts.append(f"## {h.upper()}\n{block}")
    return "\n\n".join(parts).strip()


def fingerprint_for_rescoring(markdown: str) -> str:
    """Hash of skills + experience regions; static sections do not affect this."""
    payload = scoring_relevant_excerpt(markdown).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()
