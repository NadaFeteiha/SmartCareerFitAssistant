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
_OTHERS_TITLES = frozenset({"others", "other", "misc", "miscellaneous", "additional skills"})


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


# Keyword hints → preferred category heading (must match resume style: **Label:**)
_CATEGORY_RULES: list[tuple[str, tuple[str, ...]]] = [
    (
        "Languages & Frameworks",
        (
            "python", "java", "kotlin", "javascript", "typescript", "swift", "rust",
            "ruby", "php", "scala", "html", "css", "react", "angular", "vue", "svelte",
            "node", "nodejs", "flask", "django", "spring", "graphql", "golang", "go",
            "next.js", "nextjs", "express", "fastapi", "ktor", "android", "ios",
        ),
    ),
    (
        "Backend & Databases",
        (
            "sql", "mysql", "postgres", "postgresql", "mongodb", "redis", "kafka",
            "elasticsearch", "oracle", "sqlite", "nosql", "rest", "grpc", "backend",
            "api", "microservice",
        ),
    ),
    (
        "AI/ML & Data",
        (
            "tensorflow", "pytorch", "keras", "pandas", "numpy", "scikit", "sklearn",
            "ml", "nlp", "spark", "jupyter", "langchain", "huggingface", "opencv",
        ),
    ),
    (
        "Cloud & DevOps",
        (
            "aws", "azure", "gcp", "docker", "kubernetes", "k8s", "terraform",
            "jenkins", "prometheus", "grafana", "lambda", "ec2", "s3", "ci/cd",
            "devops", "ansible", "helm",
        ),
    ),
    (
        "Tools & Practices",
        (
            "git", "github", "gitlab", "jira", "agile", "scrum", "oop", "unix", "linux",
        ),
    ),
]


def _infer_category_label(skill: str) -> str:
    """Pick a category heading for a skill; unknown skills get their own one-skill category."""
    s = skill.lower().strip()
    if not s:
        return "Additional skills"
    for label, keys in _CATEGORY_RULES:
        for k in keys:
            if k in s or s == k:
                return label
    # No bucket fits: dedicated mini-category so the skill is never a stray bullet
    return skill.strip()


def _title_tokens(title: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", title.lower()))


def _titles_match(existing: str, inferred: str) -> bool:
    """True if an existing **Category:** header should receive this inferred label."""
    a, b = existing.strip().lower(), inferred.strip().lower()
    if a == b:
        return True
    ta, tb = _title_tokens(existing), _title_tokens(inferred)
    if ta and tb and (ta & tb):
        return True
    if len(a) >= 4 and (a in b or b in a):
        return True
    return False


def _parse_skills_body(body_lines: list[str]) -> list[dict]:
    """Split skills section into category blocks and preserved raw lines (bullets, blanks)."""
    blocks: list[dict] = []
    i = 0
    while i < len(body_lines):
        line = body_lines[i]
        m = re.match(r"^\s*\*\*(.+?):\*\*\s*(.*)$", line)
        if m:
            title = m.group(1).strip()
            rest = m.group(2).strip()
            parts: list[str] = []
            if rest:
                parts.append(rest)
            i += 1
            while i < len(body_lines):
                nxt = body_lines[i]
                if nxt.strip().startswith("##"):
                    break
                if re.match(r"^\s*\*\*.+?:\*\*", nxt):
                    break
                parts.append(nxt.strip())
                i += 1
            skills_flat: list[str] = []
            for p in parts:
                for seg in re.split(r"[,;]", p):
                    t = seg.strip()
                    if t:
                        skills_flat.append(t)
            blocks.append({"title": title, "skills": skills_flat})
        else:
            blocks.append({"raw": line})
            i += 1
    return blocks


def _skill_in_blocks(blocks: list[dict], skill: str) -> bool:
    sl = skill.lower().strip()
    if not sl:
        return True
    for b in blocks:
        if "skills" in b:
            for x in b["skills"]:
                if x.lower().strip() == sl:
                    return True
        elif "raw" in b:
            line = b["raw"].strip()
            m = re.match(r"^[-*•]\s*(.+)$", line)
            if m and m.group(1).strip().lower() == sl:
                return True
    return False


def consolidate_small_skill_categories(md: str, min_skills: int = 3) -> str:
    """
    Merge **Category:** blocks that have fewer than ``min_skills`` skills into a single **Others:** block.
    Large categories (>= min_skills) stay; skills from small categories are merged (deduped, order preserved).
    """
    if not md or min_skills < 2:
        return md

    lines = md.splitlines()
    skills_start = -1
    next_heading = -1
    for i, line in enumerate(lines):
        t = line.strip().lower()
        if t.startswith("## "):
            h = t[3:].strip()
            if h in {"skills", "technical skills", "core competencies"}:
                skills_start = i
                break
    if skills_start == -1:
        return md

    for j in range(skills_start + 1, len(lines)):
        if lines[j].strip().startswith("#"):
            next_heading = j
            break
    end = next_heading if next_heading != -1 else len(lines)
    body = lines[skills_start + 1 : end]
    if not body:
        return md

    blocks = _parse_skills_body(body)
    raws = [b["raw"] for b in blocks if "raw" in b]
    cats = [b for b in blocks if "title" in b]
    if not cats:
        return md

    big: list[dict] = []
    loose: list[str] = []
    others_big: dict | None = None

    for b in cats:
        n = len(b["skills"])
        tl = b["title"].strip().lower()
        if n >= min_skills:
            nb = {"title": b["title"], "skills": list(b["skills"])}
            big.append(nb)
            if tl in _OTHERS_TITLES:
                others_big = nb
        else:
            loose.extend(b["skills"])

    seen_l: set[str] = set()
    dedup_loose: list[str] = []
    for x in loose:
        xl = x.lower().strip()
        if xl and xl not in seen_l:
            seen_l.add(xl)
            dedup_loose.append(x.strip())

    if not dedup_loose:
        return md

    if others_big is not None:
        have = {x.lower() for x in others_big["skills"]}
        for x in dedup_loose:
            xl = x.lower()
            if xl not in have:
                others_big["skills"].append(x)
                have.add(xl)
    else:
        big.append({"title": "Others", "skills": dedup_loose})

    new_body = _render_skills_blocks(big)
    new_body.extend(raws)
    merged = lines[: skills_start + 1] + new_body + lines[end:]
    return "\n".join(merged)


def _render_skills_blocks(blocks: list[dict]) -> list[str]:
    out: list[str] = []
    for b in blocks:
        if "raw" in b:
            out.append(b["raw"])
            continue
        title = b["title"]
        skills = b.get("skills") or []
        out.append(f"**{title}:**")
        if skills:
            out.append(", ".join(skills))
    return out


def _inject_skill_into_body_lines(body_lines: list[str], skill: str) -> list[str]:
    skill = skill.strip()
    if not skill:
        return body_lines
    blocks = _parse_skills_body(body_lines)
    if _skill_in_blocks(blocks, skill):
        return body_lines

    inferred = _infer_category_label(skill)
    for b in blocks:
        if "title" not in b:
            continue
        if _titles_match(b["title"], inferred):
            have = {x.lower() for x in b["skills"]}
            if skill.lower() not in have:
                b["skills"].append(skill)
            return _render_skills_blocks(blocks)

    # New category block (either inferred bucket or single-skill category)
    blocks.append({"title": inferred, "skills": [skill]})
    return _render_skills_blocks(blocks)


def inject_skill_into_markdown(md: str, skill: str) -> str:
    """Append a skill under a matching **Category:** block, or create that category."""
    skill = skill.strip()
    if not skill:
        return md

    lines = md.splitlines()
    skills_start = -1
    next_heading = -1

    for i, line in enumerate(lines):
        text = line.strip().lower()
        if text.startswith("## "):
            heading = text[3:].strip()
            if heading in {"skills", "technical skills", "core competencies"}:
                skills_start = i
                break

    if skills_start != -1:
        for j in range(skills_start + 1, len(lines)):
            if lines[j].strip().startswith("#"):
                next_heading = j
                break
        end = next_heading if next_heading != -1 else len(lines)
        body = lines[skills_start + 1 : end]
        new_body = _inject_skill_into_body_lines(body, skill)
        merged = lines[: skills_start + 1] + new_body + lines[end:]
        return consolidate_small_skill_categories("\n".join(merged))

    sep = "" if md.endswith("\n") else "\n"
    label = _infer_category_label(skill)
    return consolidate_small_skill_categories(
        f"{md.rstrip()}{sep}\n## SKILLS\n**{label}:**\n{skill}\n"
    )
