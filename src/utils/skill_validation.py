"""Heuristics to keep gap / survey skills limited to plausible transferable skills."""

from __future__ import annotations

import re
from typing import Any

from src.models.analysis import SkillGapReport

_TECH_CATEGORIES: dict[str, tuple[str, ...]] = {
    "languages": (
        "python",
        "java",
        "javascript",
        "typescript",
        "kotlin",
        "swift",
        "rust",
        "go\\b",
        "golang",
        "scala",
        "php",
        "ruby",
        "elixir",
        "c\\+\\+",
        "c#",
        "csharp",
        "\\.net",
        "dotnet",
    ),
    "web": (
        "react",
        "angular",
        "vue",
        "svelte",
        "next\\.?js",
        "node\\.?js",
        "html",
        "css",
        "sass",
        "graphql",
        "rest",
        "grpc",
        "fastapi",
        "flask",
        "django",
        "spring",
        "express",
    ),
    "data": (
        "sql",
        "mysql",
        "postgres",
        "mongodb",
        "redis",
        "kafka",
        "elasticsearch",
        "sqlite",
        "nosql",
        "oracle",
        "etl",
        "spark",
        "pandas",
        "numpy",
    ),
    "ml": (
        "tensorflow",
        "pytorch",
        "keras",
        "scikit",
        "sklearn",
        "nlp",
        "opencv",
        "langchain",
        "huggingface",
        "machine\\s+learning",
        "deep\\s+learning",
    ),
    "cloud": (
        "aws",
        "azure",
        "gcp",
        "google\\s+cloud",
        "docker",
        "kubernetes",
        "k8s",
        "terraform",
        "ansible",
        "helm",
        "lambda",
        "ec2",
        "s3",
        "ci/cd",
        "devops",
        "jenkins",
        "prometheus",
        "grafana",
    ),
    "tools": (
        "git",
        "github",
        "gitlab",
        "jira",
        "agile",
        "scrum",
        "linux",
        "unix",
        "bash",
        "powershell",
        "figma",
    ),
    "platforms_apis": (
        "api",
        "json",
        "xml",
        "yaml",
        "oauth",
        "jwt",
        "ssl",
        "tls",
        "tcp",
        "http",
        "https",
        "ldap",
        "android",
        "ios",
        "jetpack",
        "compose",
        "webpack",
        "vite",
        "jest",
        "pytest",
        "junit",
        "gradle",
        "maven",
        "npm",
        "yarn",
        "ml\\b",
        "bi\\b",
        "tableau",
        "power\\s+bi",
        "excel",
        "vba",
        "data\\s+science",
        "computer\\s+vision",
    ),
}

_all_keywords = [kw for keywords in _TECH_CATEGORIES.values() for kw in keywords]
_TECH_MARKERS = re.compile(r"\b(" + "|".join(_all_keywords) + r")\b", re.I)


def _company_tokens(company: str) -> list[str]:
    return [w for w in re.findall(r"[a-z0-9]+", (company or "").lower()) if len(w) > 2]


def skill_embeds_company_name(skill: str, company: str) -> bool:
    """True if the string looks like employer / brand text (e.g. job company + random word)."""
    company = (company or "").strip()
    if len(company) < 3:
        return False
    sk = skill.lower()
    cw = _company_tokens(company)
    if len(cw) >= 2:
        a, b = cw[0], cw[1]
        if re.search(rf"\b{re.escape(a)}\b.*\b{re.escape(b)}\b", sk) or re.search(
            rf"\b{re.escape(b)}\b.*\b{re.escape(a)}\b", sk
        ):
            return True
    if len(cw) == 1 and len(cw[0]) >= 4:
        w = cw[0]
        if re.search(rf"\b{re.escape(w)}\b", sk) and not _TECH_MARKERS.search(sk):
            return True
    return False


def _normalize_skill_key(skill: str) -> str:
    s = (skill or "").lower()
    return re.sub(r"[^a-z0-9]+", "", s)


def skill_evidence_on_resume(gap_skill: str, resume_text: str, structured_skill_names: list[str]) -> bool:
    """
    True if the gap label likely corresponds to something already on the resume
    (structured skills or raw resume text).
    """
    g = (gap_skill or "").strip()
    if not g:
        return False
    rt = (resume_text or "").lower()
    if g.lower() in rt:
        return True
    g_key = _normalize_skill_key(g)
    if len(g_key) < 2:
        return False
    for name in structured_skill_names:
        n = (name or "").strip()
        if not n:
            continue
        if g.lower() in name.lower() or name.lower() in g.lower():
            return True
        nk = _normalize_skill_key(name)
        if not nk:
            continue
        if g_key == nk:
            return True
        if len(g_key) >= 4 and (g_key in nk or nk in g_key):
            return True
    return False


def is_plausible_gap_skill(skill: str, ctx: Any) -> bool:
    """
    Filter LLM gap output: reject company/product phrases and generic JD noise
    that are not real, transferable skills.
    """
    s = (skill or "").strip()
    if not s:
        return False

    if ctx is not None:
        jd = getattr(ctx, "job_data", None)
        company = (getattr(jd, "company", None) or "") if jd is not None else ""
        if skill_embeds_company_name(s, company):
            return False

    words = s.split()
    if len(words) >= 3 and not _TECH_MARKERS.search(s.lower()):
        return False

    return True


def filter_skill_gap_report(ctx: Any, report: SkillGapReport) -> SkillGapReport:
    """Drop implausible strings from gap lists (defense in depth after the LLM)."""
    rtext = ""
    snames: list[str] = []
    if ctx is not None:
        rtext = getattr(ctx, "resume_text", None) or ""
        rd = getattr(ctx, "resume_data", None)
        if rd is not None and getattr(rd, "skills", None):
            snames = [s.name for s in rd.skills]

    def _keep_skill_label(x: str) -> bool:
        if not is_plausible_gap_skill(x, ctx):
            return False
        if skill_evidence_on_resume(x, rtext, snames):
            return False
        return True

    mh = [x for x in report.missing_hard_skills if _keep_skill_label(x)]
    ms = [x for x in report.missing_soft_skills if _keep_skill_label(x)]

    mr = report.missing_requirements
    mskills = [x for x in mr.missing_skills if _keep_skill_label(x)]

    roadmap = [item for item in report.learning_roadmap if _keep_skill_label(item.skill)]

    return report.model_copy(
        update={
            "missing_hard_skills": mh,
            "missing_soft_skills": ms,
            "missing_requirements": mr.model_copy(update={"missing_skills": mskills}),
            "learning_roadmap": roadmap,
        }
    )
