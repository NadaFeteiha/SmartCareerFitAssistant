"""Tests for resume section fingerprinting (scoring trigger)."""

from src.utils.resume_sections import (
    consolidate_small_skill_categories,
    fingerprint_for_rescoring,
    inject_skill_into_markdown,
    scoring_relevant_excerpt,
)
from src.utils.skill_validation import is_plausible_gap_skill
from src.utils.resume_parser import parse_markdown_to_form


def test_scoring_excerpt_pulls_skills_and_experience():
    md = """# Name
contact | here

## SKILLS
- Python

## EXPERIENCE
- Did things
"""
    ex = scoring_relevant_excerpt(md)
    assert "Python" in ex
    assert "Did things" in ex


def test_fingerprint_ignores_header_only_edits():
    base = """## SKILLS
- Go
## EXPERIENCE
- Built APIs
"""
    fp1 = fingerprint_for_rescoring("# Alice\n\n" + base)
    fp2 = fingerprint_for_rescoring("# Bob\n\n" + base)
    assert fp1 == fp2


def test_fingerprint_changes_when_skill_changes():
    a = "## SKILLS\n- A\n## EXPERIENCE\n- X\n"
    b = "## SKILLS\n- B\n## EXPERIENCE\n- X\n"
    assert fingerprint_for_rescoring(a) != fingerprint_for_rescoring(b)


def test_parse_markdown_no_spurious_empty_summary():
    """First section was incorrectly flushed as empty SUMMARY before EXPERIENCE."""
    md = """# Jane Doe
engineer@x.com | 555-0100

## EXPERIENCE
### Dev | Co | 2020 - Present | NY
- Built things

## SUMMARY
Strong engineer.
"""
    form = parse_markdown_to_form(md)
    headings = [s["heading"] for s in form["sections"]]
    assert headings == ["EXPERIENCE", "SUMMARY"]
    summary_sections = [s for s in form["sections"] if s.get("heading", "").upper() == "SUMMARY"]
    assert len(summary_sections) == 1
    assert summary_sections[0]["content"].strip() == "Strong engineer."


def test_inject_skill_adds_to_matching_category():
    md = """# A
a@b.com

## SKILLS
**Languages & Frameworks:**
Python, Java
"""
    out = inject_skill_into_markdown(md, "Kotlin")
    assert "Kotlin" in out
    assert out.count("**Languages & Frameworks:**") == 1
    assert "- Kotlin" not in out


def test_inject_skill_creates_bucket_for_unmapped_skill():
    md = """# A
a@b.com

## SKILLS
**Languages & Frameworks:**
Python
"""
    out = inject_skill_into_markdown(md, "RareVendorTool42")
    assert "RareVendorTool42" in out
    assert "**Others:**" in out


def test_inject_skill_cloud_category_for_docker():
    md = """# A
a@b.com

## SKILLS
**Languages & Frameworks:**
Python
"""
    out = inject_skill_into_markdown(md, "Docker")
    assert "Docker" in out
    assert "**Others:**" in out


def test_inject_skill_idempotent():
    md = """## SKILLS
**Languages & Frameworks:**
Python
"""
    once = inject_skill_into_markdown(md, "Java")
    twice = inject_skill_into_markdown(once, "Java")
    assert once.count("Java") == twice.count("Java")


def test_consolidate_merges_small_categories_to_others():
    md = """# N
n@n.com

## SKILLS
**Languages & Frameworks:**
Python, Java, Kotlin
**Misc:**
ZebraTool
"""
    out = consolidate_small_skill_categories(md)
    assert out.count("**Languages & Frameworks:**") == 1
    assert "**Others:**" in out
    assert "ZebraTool" in out
    assert "Python" in out


def test_parse_markdown_multiline_contact_block():
    md = """# Alex Smith
Senior Engineer
+1 234 567 8901
linkedin.com/in/alexsmith
engineer@example.com

## EXPERIENCE
### Dev | Co | 2020 - Present |
- Work
"""
    form = parse_markdown_to_form(md)
    assert form["title"] == "Senior Engineer"
    assert form["phone"]
    assert "234" in form["phone"]
    assert "linkedin" in form["linkedin"].lower()
    assert "@" in form["email"]


def test_is_plausible_gap_skill_rejects_jd_noise():
    class JD:
        company = "Honey Mart"

    class Ctx:
        job_data = JD()

    assert is_plausible_gap_skill("Honey Mart Server", Ctx()) is False
    assert is_plausible_gap_skill("Python", Ctx()) is True
