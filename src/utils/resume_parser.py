import re

def parse_section_content(heading: str, content: str) -> dict:
    """Parse section content into granular structure based on section type."""
    heading_upper = heading.upper().strip()
    
    # EXPERIENCE / EDUCATION / PROJECTS sections
    if heading_upper in ["EXPERIENCE", "EDUCATION", "PROJECTS"]:
        items = []
        # Split content using ### as delimiter
        entries = content.split("###")
        for entry in entries:
            entry = entry.strip()
            if not entry:
                continue
                
            lines = entry.split("\n")
            if not lines:
                continue
                
            # Parse header line
            header_line = lines[0].strip()
            parts = [p.strip() for p in header_line.split("|")]
            
            title = parts[0] if len(parts) > 0 else ""
            subtitle = parts[1] if len(parts) > 1 else ""
            date = parts[2] if len(parts) > 2 else ""
            location = parts[3] if len(parts) > 3 else ""
            
            # Parse dates more intelligently
            start_date = ""
            end_date = ""
            if date:
                # Handle formats like "Jan 2024 - Present", "2022-2024", "2022 - Current"
                if " - " in date or " - " in date or "–" in date:
                    # Replace different dash types
                    clean_date = date.replace("–", "-").replace(" — ", "-").replace(" – ", "-")
                    date_parts = clean_date.split("-")
                    if len(date_parts) >= 2:
                        start_date = date_parts[0].strip()
                        end_date = date_parts[1].strip()
                    else:
                        start_date = date.strip()
                else:
                    # Single date (for education graduation or current job)
                    if heading_upper == "EDUCATION":
                        end_date = date.strip()  # Graduation date
                    else:
                        start_date = date.strip()  # Start date for experience
            
            # Description is remaining lines
            description = "\n".join(lines[1:]).strip()
            
            items.append({
                "title": title,
                "subtitle": subtitle,
                "location": location,
                "start_date": start_date,
                "end_date": end_date,
                "date": date,  # Keep original for backward compatibility
                "description": description
            })
        
        return {
            "heading": heading,
            "type": "list",
            "items": items
        }
    
    # SKILLS section
    elif heading_upper == "SKILLS":
        items = []
        lines = content.split("\n")
        current_category = ""
        current_subskills = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Check for category lines starting with **Category:** or **Category** (without colon)
            if line.startswith("**") and (":**" in line or line.endswith("**")):
                # Save previous category if exists
                if current_category:
                    items.append({
                        "category": current_category,
                        "sub_skills": "\n".join(current_subskills).strip()
                    })
                
                # Start new category
                if ":**" in line:
                    _idx = line.index(":**")
                    current_category = line[2:_idx].strip()
                else:
                    current_category = line[2:-2].strip()  # Remove ** only
                current_subskills = []
            elif line.startswith(("- ", "* ", "• ")) and current_category:
                # Bullet point skill under current category
                skill = line[2:].strip()
                if skill:
                    current_subskills.append(skill)
            elif current_category and not line.startswith("**"):
                # Regular skill line (comma-separated or single skill)
                # Handle comma-separated skills on same line
                skills_on_line = [s.strip() for s in line.split(",") if s.strip()]
                current_subskills.extend(skills_on_line)
        
        # Don't forget the last category
        if current_category:
            items.append({
                "category": current_category,
                "sub_skills": "\n".join(current_subskills).strip()
            })
        
        # If no categories found, treat as simple skills list
        if not items and content.strip():
            items.append({
                "category": "Skills",
                "sub_skills": content.strip()
            })
        
        return {
            "heading": heading,
            "type": "skills",
            "items": items
        }
    
    # SUMMARY / Custom sections - keep as raw text
    else:
        return {
            "heading": heading,
            "type": "text",
            "content": content
        }


def _append_parsed_section(parsed: dict, heading: str, content_lines: list[str]) -> None:
    """Append one section; skip empty text blocks; merge consecutive duplicate ## SUMMARY."""
    body = "\n".join(content_lines).strip()
    section_data = parse_section_content(heading, body)
    if section_data.get("type") == "text" and not section_data.get("content", "").strip():
        return
    if (
        section_data.get("type") == "text"
        and section_data.get("heading", "").strip().upper() == "SUMMARY"
        and parsed["sections"]
        and parsed["sections"][-1].get("type") == "text"
        and parsed["sections"][-1].get("heading", "").strip().upper() == "SUMMARY"
    ):
        prev = parsed["sections"][-1]
        c1 = prev.get("content", "").strip()
        c2 = section_data.get("content", "").strip()
        prev["content"] = "\n\n".join(x for x in (c1, c2) if x).strip()
        return
    parsed["sections"].append(section_data)


def parse_markdown_to_form(md: str) -> dict:
    """Parses standard markdown resume header into a structured form dictionary."""
    lines = md.splitlines()
    i = 0
    parsed = {
        "name": "",
        "title": "",
        "email": "",
        "phone": "",
        "location": "",
        "linkedin": "",
        "portfolio": "",
        "sections": []
    }
    
    saw_name = False
    saw_title = False
    saw_contact = False

    while i < len(lines):
        line = lines[i].strip()
        
        if not line:
            if saw_contact:
                break # Body starts after contact line
            i += 1
            continue

        if line.startswith("# ") and not saw_name:
            parsed["name"] = line[2:].strip()
            saw_name = True
            i += 1
            continue
            
        if saw_name and not saw_title and not saw_contact and not line.startswith("#"):
            is_contact = (
                "@" in line or "linkedin" in line.lower()
                or "github" in line.lower() or "portfolio" in line.lower() or "|" in line
                or re.search(r'\+?\d[\d\s\-().]{6,}', line)
            )
            if not is_contact:
                parsed["title"] = line
                saw_title = True
                i += 1
                continue
                
        if saw_name and not saw_contact and not line.startswith("#"):
            # Parse contact line components
            parts = [p.strip() for p in line.split("|")]
            for p in parts:
                lower_p = p.lower()
                if "@" in p:
                    parsed["email"] = p
                elif "linkedin" in lower_p:
                    parsed["linkedin"] = p
                elif "github" in lower_p or "portfolio" in lower_p or "http" in lower_p:
                    parsed["portfolio"] = p
                elif re.search(r'\+?\d[\d\s\-().]{6,}', p):
                    parsed["phone"] = p
                else:
                    parsed["location"] = p
                    
            saw_contact = True
            i += 1
            break
            
        # Fallback if no contact line is found before the first real section
        if not saw_name and line.startswith("## "):
            break

        i += 1

    # No implicit SUMMARY bucket: only create SUMMARY from explicit ## SUMMARY or orphan lines
    # before the first ## (otherwise the first ## EXPERIENCE flushed a bogus empty SUMMARY).
    current_heading: str | None = None
    current_content: list[str] = []

    for line in lines[i:]:
        strip_line = line.strip()
        if strip_line.startswith("## "):
            new_heading = strip_line[3:].strip()
            if current_heading is None:
                orphan = "\n".join(current_content).strip()
                if orphan:
                    _append_parsed_section(parsed, "SUMMARY", current_content)
                current_content = []
            else:
                _append_parsed_section(parsed, current_heading, current_content)
                current_content = []
            current_heading = new_heading
        else:
            current_content.append(line)

    if current_heading is not None:
        _append_parsed_section(parsed, current_heading, current_content)

    return parsed

def build_markdown_from_form(form_data: dict) -> str:
    """Reconstructs the standard Markdown string from the UI dictionary."""
    md_lines = []
    
    if form_data.get("name"):
        md_lines.append(f"# {form_data['name']}")
    
    if form_data.get("title"):
        md_lines.append(f"{form_data['title']}")
        
    contacts = []
    for field in ["email", "phone", "location", "linkedin", "portfolio"]:
        val = form_data.get(field, "").strip()
        if val:
            contacts.append(val)
            
    if contacts:
        md_lines.append(" | ".join(contacts))
        
    md_lines.append("")
    
    if "sections" in form_data:
        for sec in form_data["sections"]:
            head = sec["heading"].strip()
            if head:
                md_lines.append(f"## {head}")
            
            # Handle different section types
            if sec.get("type") == "list":
                # Reconstruct list items (EXPERIENCE/EDUCATION/PROJECTS)
                for item in sec.get("items", []):
                    # Reconstruct date from start_date and end_date
                    date_str = ""
                    if item.get("start_date") and item.get("end_date"):
                        date_str = f"{item['start_date']} - {item['end_date']}"
                    elif item.get("start_date"):
                        date_str = item["start_date"]
                    elif item.get("end_date"):
                        date_str = item["end_date"]
                    elif item.get("date"):
                        date_str = item["date"]  # Fallback to original
                    
                    # Rejoin Title | Subtitle | Date | Location ignoring empty values
                    parts = []
                    if item.get("title"):
                        parts.append(item["title"].strip())
                    if item.get("subtitle"):
                        parts.append(item["subtitle"].strip())
                    if date_str:
                        parts.append(date_str.strip())
                    if item.get("location"):
                        parts.append(item["location"].strip())
                    
                    if parts:
                        md_lines.append(f"### {' | '.join(parts)}")
                    
                    if item.get("description"):
                        md_lines.append(item["description"].strip())
                    
                    md_lines.append("")  # Add spacing between items
                    
            elif sec.get("type") == "skills":
                # Rebuild category **Category:** skills lists
                for item in sec.get("items", []):
                    if item.get("category"):
                        md_lines.append(f"**{item['category'].strip()}:**")
                    
                    if item.get("sub_skills"):
                        sub_skills = item["sub_skills"].strip()
                        # Split by newlines and add each line
                        for line in sub_skills.split("\n"):
                            if line.strip():
                                md_lines.append(line.strip())
                    
                    md_lines.append("")  # Add spacing between categories
                    
            else:
                # Handle text content (SUMMARY/Custom sections)
                content = sec.get("content", "").strip()
                if content:
                    md_lines.append(content)
                
            md_lines.append("")  # Add spacing between sections
            
    elif "body" in form_data:
        md_lines.append(form_data["body"])
    
    return "\n".join(md_lines).strip()
