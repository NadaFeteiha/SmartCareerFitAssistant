"""Post-analysis skill check — callbacks only (no nested ``if st.button()``)."""

from __future__ import annotations

import streamlit as st

from src.agents.analyzer import AnalysisContext
from src.models.analysis import FullAnalysis
from src.models.resume import Skill
from src.services.pipeline import recalculate_fit_and_gaps_sync

_CONFIRM_SECTION = "## Additional skills (self-confirmed)\n"


def _append_confirmed_skill_to_resume(md: str, skill: str) -> str:
    entry = f"- {skill}\n"
    if _CONFIRM_SECTION in md:
        idx = md.index(_CONFIRM_SECTION) + len(_CONFIRM_SECTION)
        return md[:idx] + entry + md[idx:]
    sep = "" if md.endswith("\n") else "\n"
    return f"{md.rstrip()}{sep}\n{_CONFIRM_SECTION}{entry}"


def _build_skill_queue(result: FullAnalysis) -> list[tuple[str, str]]:
    seen: set[str] = set()
    out: list[tuple[str, str]] = []
    for s in result.skill_gaps.missing_hard_skills:
        t = (s or "").strip()
        k = t.lower()
        if k and k not in seen:
            seen.add(k)
            out.append((t, "hard"))
    for s in result.skill_gaps.missing_soft_skills:
        t = (s or "").strip()
        k = t.lower()
        if k and k not in seen:
            seen.add(k)
            out.append((t, "soft"))
    return out


def _advance_skill_yes() -> None:
    ctx = st.session_state.get("pipeline_context")
    if ctx is None:
        return
    q = st.session_state.skill_survey_queue
    idx = st.session_state.skill_survey_index
    if idx >= len(q):
        return
    skill_name, kind = q[idx]
    names = {s.name.lower() for s in ctx.resume_data.skills}
    if skill_name.lower() not in names:
        cat = "hard_skill" if kind == "hard" else "soft_skill"
        ctx.resume_data.skills.append(
            Skill(name=skill_name, category=cat, proficiency="intermediate")
        )
    ar: FullAnalysis = st.session_state.analysis_result
    new_md = _append_confirmed_skill_to_resume(ar.optimized_resume, skill_name)
    st.session_state.analysis_result = ar.model_copy(update={"optimized_resume": new_md})
    st.session_state.resume_markdown_draft = new_md
    st.session_state.skill_chat.append({"role": "user", "content": f"Yes — I have: {skill_name}"})
    st.session_state.skill_chat.append(
        {
            "role": "assistant",
            "content": f"Added **{skill_name}** to your optimized resume.",
        }
    )
    st.session_state.skill_survey_index = idx + 1


def _advance_skill_no() -> None:
    q = st.session_state.skill_survey_queue
    idx = st.session_state.skill_survey_index
    if idx >= len(q):
        return
    skill_name, _kind = q[idx]
    st.session_state.skill_chat.append(
        {"role": "user", "content": f"No — I don't have: {skill_name}"}
    )
    st.session_state.skill_chat.append(
        {
            "role": "assistant",
            "content": "Okay — leaving that out. Next question when you're ready.",
        }
    )
    st.session_state.skill_survey_index = idx + 1


def _finalize_skill_survey() -> None:
    ctx = st.session_state.get("pipeline_context")
    if ctx is None:
        st.session_state.skill_survey_finished = True
        return
    try:
        ar: FullAnalysis = st.session_state.analysis_result
        old_fit = ar.fit_score
        new_fit, new_gaps = recalculate_fit_and_gaps_sync(ctx)
        
        # Ensure overall score does not decrease upon adding a confirmed skill
        if new_fit.overall < old_fit.overall:
            new_fit.overall = old_fit.overall
            
        st.session_state.analysis_result = ar.model_copy(
            update={"fit_score": new_fit, "skill_gaps": new_gaps}
        )
        st.session_state.skill_chat.append(
            {
                "role": "assistant",
                "content": (
                    f"All set. **New overall score: {new_fit.overall}/100** "
                    f"(skill match {new_fit.skill_match}/40, "
                    f"experience {new_fit.experience_alignment}/30, "
                    f"keywords {new_fit.keyword_coverage}/30).\n\n"
                    f"{new_fit.explanation}"
                ),
            }
        )
    except Exception as e:
        st.session_state.skill_chat.append(
            {
                "role": "assistant",
                "content": f"Could not refresh score after the survey: {e}",
            }
        )
    st.session_state.skill_survey_finished = True


def render_skill_check_assistant(result: FullAnalysis, ctx: AnalysisContext) -> None:
    if "skill_survey_queue" not in st.session_state:
        queue = _build_skill_queue(result)
        if not queue:
            return
        st.session_state.skill_survey_queue = queue
        st.session_state.skill_survey_index = 0
        st.session_state.skill_survey_finished = False
        st.session_state.skill_chat = [
            {
                "role": "assistant",
                "content": (
                    "Hi — I'll go through each **missing skill** from the analysis. "
                    "If you actually have it (including equivalent experience), say **Yes** and I'll add it to your optimized resume. "
                    "When we're done, I'll **recalculate your fit score**."
                ),
            }
        ]

    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
    st.markdown("### 💬 Skill check assistant")
    st.caption(
        "Answer one skill at a time. Confirmed skills are appended under "
        "“Additional skills (self-confirmed)” on your optimized resume."
    )

    q = st.session_state.skill_survey_queue
    idx = st.session_state.skill_survey_index

    with st.container(border=True):
        for msg in st.session_state.skill_chat:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        if st.session_state.skill_survey_finished:
            return

        if idx >= len(q):
            _finalize_skill_survey()
            st.rerun()
            return

        skill_name, kind = q[idx]
        kind_label = "technical" if kind == "hard" else "soft"
        with st.chat_message("assistant"):
            st.markdown(
                f"**Skill {idx + 1} of {len(q)}** ({kind_label})\n\n"
                f"Do you have **{skill_name}** (or close equivalent experience you could truthfully put on a resume)?"
            )

        c1, c2 = st.columns(2)
        with c1:
            st.button(
                "Yes — add to resume",
                key=f"skill_yes_{idx}",
                type="primary",
                on_click=_advance_skill_yes,
            )
        with c2:
            st.button(
                "No / skip",
                key=f"skill_no_{idx}",
                on_click=_advance_skill_no,
            )
