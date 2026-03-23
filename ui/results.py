"""Results tabs — scores stay synced with ``st.session_state.analysis_result``."""

from __future__ import annotations

import html
import re

import streamlit as st

from src.models.analysis import FullAnalysis
from ui.components import render_result_box, render_score_cards, render_skill_chips, render_pdf_preview, render_cover_letter_pdf_preview
from ui.resume_handlers import on_resume_markdown_changed, on_cover_letter_changed
from src.utils.pdf import (
    create_cover_letter_docx,
    create_cover_letter_pdf,
    create_resume_docx,
    create_resume_pdf,
)


def render_results() -> None:
    result: FullAnalysis = st.session_state["analysis_result"]

    if "resume_markdown_draft" not in st.session_state:
        from src.utils.resume_sections import fingerprint_for_rescoring

        st.session_state.resume_markdown_draft = result.optimized_resume
        st.session_state["_resume_score_fp"] = fingerprint_for_rescoring(result.optimized_resume)

    err = st.session_state.pop("_rescore_error", None)
    if err:
        st.error(f"Re-score failed: {err}")

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    render_score_cards(result.fit_score)

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    ctx = st.session_state.get("pipeline_context")
    if ctx is not None:
        result = st.session_state["analysis_result"]

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Fit Analysis",
        "📝 Optimized Resume",
        "💌 Cover Letter",
        "📚 Learning Roadmap",
    ])

    with tab1:
        _render_fit_tab(result)

    with tab2:
        _render_resume_tab(result)

    with tab3:
        _render_cover_letter_tab(result)

    with tab4:
        _render_roadmap_tab(result)


def _render_missing_requirements(result: FullAnalysis) -> None:
    mr = result.skill_gaps.missing_requirements
    if not (mr.missing_skills or mr.missing_experience or mr.missing_keywords):
        return

    st.markdown("#### Missing requirements")
    st.caption("Compared to the job description — close gaps to move toward a stronger match.")
    parts = []
    if mr.missing_skills:
        li = "".join(f"<li>{html.escape(x)}</li>" for x in mr.missing_skills)
        parts.append(f"<h4>Skills</h4><ul>{li}</ul>")
    if mr.missing_experience:
        li = "".join(f"<li>{html.escape(x)}</li>" for x in mr.missing_experience)
        parts.append(f"<h4>Experience</h4><ul>{li}</ul>")
    if mr.missing_keywords:
        li = "".join(f"<li>{html.escape(x)}</li>" for x in mr.missing_keywords)
        parts.append(f"<h4>Keywords</h4><ul>{li}</ul>")
    st.markdown(
        f'<div class="missing-req-panel">{" ".join(parts)}</div>',
        unsafe_allow_html=True,
    )


def _render_fit_tab(result: FullAnalysis) -> None:
    render_skill_chips(
        strengths=result.fit_score.strengths,
        missing_hard=result.skill_gaps.missing_hard_skills,
        missing_soft=result.skill_gaps.missing_soft_skills,
    )
    _render_missing_requirements(result)


def _resume_download_basename(markdown: str) -> str:
    candidate_name = "resume"
    for line in markdown.split("\n"):
        if line.strip().startswith("# "):
            candidate_name = re.sub(r"[^\w\s-]", "", line.strip()[2:].strip()).strip().replace(" ", "_")
            break
    return candidate_name


def __sync_resume_form():
    from src.utils.resume_parser import build_markdown_from_form
    from ui.resume_handlers import on_resume_markdown_changed
    
    updated_form = {
        "name": st.session_state.get("r_name", ""),
        "title": st.session_state.get("r_title", ""),
        "email": st.session_state.get("r_email", ""),
        "phone": st.session_state.get("r_phone", ""),
        "location": st.session_state.get("r_location", ""),
        "linkedin": st.session_state.get("r_linkedin", ""),
        "portfolio": st.session_state.get("r_portfolio", "")
    }
    
    sections = []
    old_sections = st.session_state.parsed_resume_form.get("sections", [])
    for idx, sec in enumerate(old_sections):
        heading = st.session_state.get(f"r_sec_h_{idx}", sec["heading"])
        section_type = st.session_state.get(f"r_sec_type_{idx}", sec.get("type", "text"))
        
        if section_type == "list":
            # Handle list sections (EXPERIENCE/EDUCATION/PROJECTS)
            items = []
            item_count = len(sec.get("items", []))
            for item_idx in range(item_count):
                items.append({
                    "title": st.session_state.get(f"r_sec_{idx}_item_{item_idx}_title", sec["items"][item_idx].get("title", "")),
                    "subtitle": st.session_state.get(f"r_sec_{idx}_item_{item_idx}_subtitle", sec["items"][item_idx].get("subtitle", "")),
                    "location": st.session_state.get(f"r_sec_{idx}_item_{item_idx}_location", sec["items"][item_idx].get("location", "")),
                    "start_date": st.session_state.get(f"r_sec_{idx}_item_{item_idx}_start_date", sec["items"][item_idx].get("start_date", "")),
                    "end_date": st.session_state.get(f"r_sec_{idx}_item_{item_idx}_end_date", sec["items"][item_idx].get("end_date", "")),
                    "date": st.session_state.get(f"r_sec_{idx}_item_{item_idx}_date", sec["items"][item_idx].get("date", "")),  # Keep for compatibility
                    "description": st.session_state.get(f"r_sec_{idx}_item_{item_idx}_desc", sec["items"][item_idx].get("description", ""))
                })
            sections.append({
                "heading": heading,
                "type": "list",
                "items": items
            })
        elif section_type == "skills":
            # Handle skills sections
            items = []
            item_count = len(sec.get("items", []))
            for item_idx in range(item_count):
                items.append({
                    "category": st.session_state.get(f"r_sec_{idx}_item_{item_idx}_category", sec["items"][item_idx].get("category", "")),
                    "sub_skills": st.session_state.get(f"r_sec_{idx}_item_{item_idx}_subskills", sec["items"][item_idx].get("sub_skills", ""))
                })
            sections.append({
                "heading": heading,
                "type": "skills",
                "items": items
            })
        else:
            # Handle text sections (SUMMARY/Custom)
            content = st.session_state.get(f"r_sec_c_{idx}", sec.get("content", ""))
            sections.append({
                "heading": heading,
                "type": "text",
                "content": content
            })
    
    updated_form["sections"] = sections
    
    new_draft = build_markdown_from_form(updated_form)
    st.session_state.resume_markdown_draft = new_draft
    st.session_state.parsed_resume_form = updated_form
    st.session_state._last_md_to_parse = new_draft
    
    on_resume_markdown_changed()

def _render_resume_tab(result: FullAnalysis) -> None:
    st.caption("Edit your personal details and content below. Saving changes to **Skills** or **Experience** triggers a fit re-score.")
    col_edit, col_prev = st.columns(2)
    
    md = st.session_state.get("resume_markdown_draft", result.optimized_resume)
    candidate_name = _resume_download_basename(md)
    
    from src.utils.resume_parser import parse_markdown_to_form
    if "parsed_resume_form" not in st.session_state or st.session_state.get("_last_md_to_parse") != md:
        st.session_state.parsed_resume_form = parse_markdown_to_form(md)
        st.session_state._last_md_to_parse = md
        
    form = st.session_state.parsed_resume_form
    
    with col_edit:
        with st.container(height=600, border=False):
            st.markdown("#### Personal Details")
            c1, c2 = st.columns(2)
            c1.text_input("Full name", value=form["name"], key="r_name")
            c2.text_input("Professional title", value=form["title"], key="r_title")
            
            c3, c4 = st.columns(2)
            c3.text_input("Email", value=form["email"], key="r_email")
            c4.text_input("Phone", value=form["phone"], key="r_phone")
            
            c5, c6 = st.columns(2)
            c5.text_input("Location", value=form["location"], key="r_location")
            c6.text_input("LinkedIn", value=form["linkedin"], key="r_linkedin")
            
            st.text_input("Portfolio / Website", value=form["portfolio"], key="r_portfolio")
            
            st.markdown("#### Resume Sections")
            st.caption("Edit individual sections below. Click 'Save Changes' to update the preview.")
            
            # Add save button at the top of sections
            if st.button("💾 Save Changes", key="save_resume_changes", type="primary"):
                __sync_resume_form()
                st.success("Resume updated successfully!")
                st.rerun()
            
            for idx, sec in enumerate(form.get("sections", [])):
                with st.expander(f"Section: {sec['heading']}", expanded=True):
                    st.text_input(
                        "Heading", 
                        value=sec["heading"], 
                        key=f"r_sec_h_{idx}", 
                        label_visibility="collapsed"
                    )
                    
                    # Store section type for sync function
                    st.session_state[f"r_sec_type_{idx}"] = sec.get("type", "text")
                    
                    # Render different UI based on section type
                    if sec.get("type") == "list":
                        # Render list items (EXPERIENCE/EDUCATION/PROJECTS)
                        st.markdown(f"**{sec['heading']} Entries**")
                        for item_idx, item in enumerate(sec.get("items", [])):
                            st.markdown(f"**Entry {item_idx + 1}**")
                            
                            # Create grid for the fields
                            col1, col2 = st.columns(2)
                            with col1:
                                st.text_input(
                                    "Title/Role" if sec['heading'] != 'EDUCATION' else "Degree", 
                                    value=item.get("title", ""), 
                                    key=f"r_sec_{idx}_item_{item_idx}_title"
                                )
                                st.text_input(
                                    "Start Date" if sec['heading'] == 'EXPERIENCE' else "Start Date", 
                                    value=item.get("start_date", ""), 
                                    key=f"r_sec_{idx}_item_{item_idx}_start_date"
                                )
                            with col2:
                                st.text_input(
                                    "Employer/School" if sec['heading'] != 'EDUCATION' else "School", 
                                    value=item.get("subtitle", ""), 
                                    key=f"r_sec_{idx}_item_{item_idx}_subtitle"
                                )
                                end_date_label = "End Date" if sec['heading'] == 'EXPERIENCE' else ("Graduation Date" if sec['heading'] == 'EDUCATION' else "End Date")
                                st.text_input(
                                    end_date_label, 
                                    value=item.get("end_date", ""), 
                                    key=f"r_sec_{idx}_item_{item_idx}_end_date",
                                    help=f"Enter '{end_date_label}' or 'Present' for current position"
                                )
                            
                            st.text_input(
                                "Location", 
                                value=item.get("location", ""), 
                                key=f"r_sec_{idx}_item_{item_idx}_location"
                            )
                            
                            st.text_area(
                                "Description", 
                                value=item.get("description", ""), 
                                height=100, 
                                key=f"r_sec_{idx}_item_{item_idx}_desc"
                            )
                            st.divider()
                            
                    elif sec.get("type") == "skills":
                        # Render skills categories
                        st.markdown(f"**{sec['heading']} Categories**")
                        
                        # Debug: Show items count
                        items_list = sec.get("items", [])
                        if not items_list:
                            st.info("No skills categories found. The skills section might be in a different format.")
                        else:
                            for item_idx, item in enumerate(items_list):
                                st.markdown(f"**Skill Category {item_idx + 1}**")
                                
                                st.text_input(
                                    "Category Name", 
                                    value=item.get("category", ""), 
                                    key=f"r_sec_{idx}_item_{item_idx}_category"
                                )
                                
                                st.text_area(
                                    "Skills List", 
                                    value=item.get("sub_skills", ""), 
                                    height=100, 
                                    key=f"r_sec_{idx}_item_{item_idx}_subskills",
                                    help="Enter skills separated by newlines or commas"
                                )
                                st.divider()
                            
                    else:
                        # Render standard text area for text sections (SUMMARY/Custom)
                        st.text_area(
                            "Content", 
                            value=sec.get("content", ""), 
                            height=200, 
                            key=f"r_sec_c_{idx}", 
                            label_visibility="collapsed"
                        )

    with col_prev:
        with st.container(height=600, border=False):
            render_pdf_preview(md)

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)


def _render_cover_letter_tab(result: FullAnalysis) -> None:
    st.caption("Edit your cover letter below. Click 'Save Changes' to update preview.")
    
    if "cover_letter_draft" not in st.session_state:
        st.session_state.cover_letter_draft = result.cover_letter
        
    col_edit, col_prev = st.columns(2)
    with col_edit:
        st.text_area(
            "Editable cover letter",
            height=600,
            key="cover_letter_draft",
            label_visibility="collapsed",
        )
        
        # Add save button for cover letter
        if st.button("💾 Save Changes", key="save_cover_letter_changes", type="primary"):
            on_cover_letter_changed()
            st.success("Cover letter updated successfully!")
            st.rerun()
        
    cl = st.session_state.get("cover_letter_draft", result.cover_letter)
    
    with col_prev:
        with st.container(height=600, border=False):
            render_cover_letter_pdf_preview(cl)

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)


def _render_roadmap_tab(result: FullAnalysis) -> None:
    st.markdown("#### Prioritized Learning Roadmap")
    if not result.skill_gaps.learning_roadmap:
        st.info("No learning items identified — you're already a strong match!")
        return

    for item in result.skill_gaps.learning_roadmap:
        icon = "🔴" if item.priority == "high" else ("🟡" if item.priority == "medium" else "🟢")
        badge = f'<span class="step-badge">{item.priority.upper()}</span>'
        with st.expander(f"{icon} {item.skill}"):
            st.markdown(
                f"{badge} **Why it matters:** {item.reason}",
                unsafe_allow_html=True,
            )
            st.markdown(f"**How to learn it:** {item.suggestion}")
