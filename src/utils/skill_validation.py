"""Heuristics to keep gap / survey skills limited to plausible transferable skills."""

from __future__ import annotations

import re
from typing import Any

from src.models.analysis import SkillGapReport

# Common tech / methodology tokens — multi-word “skills” must hit one of these to pass without company match
_TECH_MARKERS = re.compile(
    r"\b("
    r"python|java|javascript|typescript|sql|aws|azure|gcp|google\s+cloud|docker|kubernetes|k8s|react|node\.?js|angular|vue|"
    r"svelte|next\.?js|graphql|rest|grpc|api|json|xml|yaml|linux|unix|bash|powershell|spring|flask|django|fastapi|"
    r"mongodb|postgres|mysql|mariadb|redis|elasticsearch|kafka|tensorflow|pytorch|keras|spark|pandas|numpy|"
    r"scikit|sklearn|ml|nlp|opencv|langchain|rust|go\b|golang|kotlin|swift|php|ruby|scala|elixir|c\+\+|csharp|c#|\.net|dotnet|"
    r"terraform|ansible|helm|jenkins|ci/cd|devops|git|github|gitlab|jira|agile|scrum|oauth|jwt|ssl|tcp|http|https|"
    r"html|css|sass|less|webpack|vite|jest|pytest|junit|gradle|maven|npm|yarn|figma|sketch|oauth|ldap|ssl|tls|"
    r"kubernetes|prometheus|grafana|lambda|ec2|s3|nosql|oracle|sqlite|android|ios|jetpack|compose|"
    r"machine\s+learning|deep\s+learning|data\s+science|computer\s+vision|nlp|etl|bi\b|tableau|power\s+bi|excel|vba"
    r")\b",
    re.I,
)


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
    mh = [x for x in report.missing_hard_skills if is_plausible_gap_skill(x, ctx)]
    ms = [x for x in report.missing_soft_skills if is_plausible_gap_skill(x, ctx)]

    mr = report.missing_requirements
    mskills = [x for x in mr.missing_skills if is_plausible_gap_skill(x, ctx)]

    roadmap = [item for item in report.learning_roadmap if is_plausible_gap_skill(item.skill, ctx)]

    return report.model_copy(
        update={
            "missing_hard_skills": mh,
            "missing_soft_skills": ms,
            "missing_requirements": mr.model_copy(update={"missing_skills": mskills}),
            "learning_roadmap": roadmap,
        }
    )