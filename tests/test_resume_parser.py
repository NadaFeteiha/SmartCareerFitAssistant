from src.utils.resume_parser import parse_markdown_to_form, build_markdown_from_form

SAMPLE_MD = """# Jane Doe
Software Engineer
jane@example.com | linkedin.com/in/janedoe | Seattle, WA

## SUMMARY
Experienced software engineer with 5 years in backend development.

## EXPERIENCE
### Backend Engineer | Acme Corp | Jan 2021 - Present | Seattle, WA
- Built REST APIs serving 1M+ requests/day
- Reduced latency by 40% via caching

## SKILLS
**Languages:** Python, Go
**Tools:** Docker, Kubernetes
"""


def test_round_trip_preserves_name():
    parsed = parse_markdown_to_form(SAMPLE_MD)
    assert parsed["name"] == "Jane Doe"


def test_round_trip_preserves_sections():
    parsed = parse_markdown_to_form(SAMPLE_MD)
    headings = [s["heading"] for s in parsed["sections"]]
    assert "SUMMARY" in headings
    assert "EXPERIENCE" in headings
    assert "SKILLS" in headings


def test_round_trip_rebuild():
    parsed = parse_markdown_to_form(SAMPLE_MD)
    rebuilt = build_markdown_from_form(parsed)
    reparsed = parse_markdown_to_form(rebuilt)
    # Name and section headings must survive a full round-trip
    assert reparsed["name"] == parsed["name"]
    original_headings = {s["heading"] for s in parsed["sections"]}
    rebuilt_headings = {s["heading"] for s in reparsed["sections"]}
    assert original_headings == rebuilt_headings
