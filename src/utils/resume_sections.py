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

def inject_skill_into_markdown(md: str, skill: str) -> str:
    """Intelligently append a skill to the main Skills section, avoiding isolated 'confirmed' sections."""
    lines = md.split('\n')
    skills_start = -1
    next_heading = -1
    
    for i, line in enumerate(lines):
        text = line.strip().lower()
        if text.startswith('## '):
            heading = text[3:].strip()
            if heading in {"skills", "technical skills", "core competencies"}:
                skills_start = i
                break
                
    if skills_start != -1:
        for i in range(skills_start + 1, len(lines)):
            if lines[i].strip().startswith('#'):
                next_heading = i
                break
        
        insert_pos = next_heading if next_heading != -1 else len(lines)
        
        while insert_pos > skills_start and not lines[insert_pos - 1].strip():
            insert_pos -= 1
            
        lines.insert(insert_pos, f"- {skill}")
        return "\n".join(lines)
    else:
        sep = "" if md.endswith("\n") else "\n"
        return f"{md.rstrip()}{sep}\n## SKILLS\n- {skill}\n"
