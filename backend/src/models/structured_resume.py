from pydantic import BaseModel, Field


class PersonalInfo(BaseModel):
    name: str = ""
    title: str = ""
    email: str = ""
    phone: str = ""
    location: str = ""
    portfolio: str = ""
    linkedin: str = ""
    github: str = ""
    summary: str = ""


class EducationEntry(BaseModel):
    id: str
    degree: str = ""
    school: str = ""
    link: str = ""
    start_date: str = ""
    end_date: str = ""
    location: str = ""
    description: str = ""
    hidden: bool = False


class ExperienceEntry(BaseModel):
    id: str
    title: str = ""
    company: str = ""
    link: str = ""
    start_date: str = ""
    end_date: str = ""
    location: str = ""
    description: str = ""
    hidden: bool = False


class ProjectEntry(BaseModel):
    id: str
    name: str = ""
    link: str = ""
    start_date: str = ""
    end_date: str = ""
    description: str = ""
    hidden: bool = False


class CustomEntry(BaseModel):
    id: str
    title: str = ""
    subtitle: str = ""
    start_date: str = ""
    end_date: str = ""
    description: str = ""
    hidden: bool = False


class CustomSection(BaseModel):
    id: str
    title: str = "Section"
    entries: list[CustomEntry] = Field(default_factory=list)


class StructuredResume(BaseModel):
    personal: PersonalInfo = Field(default_factory=PersonalInfo)
    skills: list[str] = Field(default_factory=list)
    education: list[EducationEntry] = Field(default_factory=list)
    experience: list[ExperienceEntry] = Field(default_factory=list)
    projects: list[ProjectEntry] = Field(default_factory=list)
    custom: list[CustomSection] = Field(default_factory=list)


def _date_range(start: str, end: str) -> str:
    s, e = start.strip(), end.strip()
    if s and e:
        return f"{s} – {e}"
    if s:
        return f"{s} – Present"
    return e


def to_markdown(resume: StructuredResume) -> str:
    """Compile a structured resume to markdown text suitable for the analyze pipeline.

    Entries with hidden=True are excluded from the output.
    """
    p = resume.personal
    lines: list[str] = []

    if p.name:
        title_suffix = f" — {p.title}" if p.title else ""
        lines.append(f"# {p.name}{title_suffix}")
    contact = " | ".join(x for x in [p.email, p.phone, p.location, p.portfolio, p.linkedin, p.github] if x)
    if contact:
        lines.append(contact)

    if p.summary:
        lines += ["", "## SUMMARY", p.summary]

    visible_exp = [e for e in resume.experience if not e.hidden]
    if visible_exp:
        lines += ["", "## EXPERIENCE"]
        for e in visible_exp:
            header = " | ".join(x for x in [e.title, e.company, _date_range(e.start_date, e.end_date), e.location] if x)
            if header:
                lines.append(f"### {header}")
            if e.description:
                lines.append(e.description)

    visible_edu = [ed for ed in resume.education if not ed.hidden]
    if visible_edu:
        lines += ["", "## EDUCATION"]
        for ed in visible_edu:
            header = " | ".join(x for x in [ed.degree, ed.school, _date_range(ed.start_date, ed.end_date), ed.location] if x)
            if header:
                lines.append(f"### {header}")
            if ed.description:
                lines.append(ed.description)

    visible_proj = [pr for pr in resume.projects if not pr.hidden]
    if visible_proj:
        lines += ["", "## PROJECTS"]
        for pr in visible_proj:
            name = pr.name + (f" ({pr.link})" if pr.link else "")
            header = " | ".join(x for x in [name, _date_range(pr.start_date, pr.end_date)] if x)
            if header:
                lines.append(f"### {header}")
            if pr.description:
                lines.append(pr.description)

    if resume.skills:
        lines += ["", "## SKILLS", ", ".join(resume.skills)]

    for section in resume.custom:
        visible_entries = [e for e in section.entries if not e.hidden]
        if not visible_entries and not section.title:
            continue
        lines += ["", f"## {section.title.upper()}"]
        for entry in visible_entries:
            header = " | ".join(x for x in [entry.title, entry.subtitle, _date_range(entry.start_date, entry.end_date)] if x)
            if header:
                lines.append(f"### {header}")
            if entry.description:
                lines.append(entry.description)

    return "\n".join(lines).strip()
