"""Post-analysis skill check — callbacks only (no nested ``if st.button()``)."""

from __future__ import annotations

import copy

import streamlit as st

from src.agents.context import AnalysisContext
from src.models.analysis import FullAnalysis, SkillGapReport
from src.models.resume import Skill
from src.services.pipeline import recalculate_fit_and_gaps_sync
from src.utils.resume_sections import fingerprint_for_rescoring, inject_skill_into_markdown
from src.utils.skill_validation import is_plausible_gap_skill
from src.database.repository import add_user_skill


def _build_skill_queue(result: FullAnalysis, ctx: AnalysisContext | None = None) -> list[tuple[str, str]]:
    seen: set[str] = set()
    out: list[tuple[str, str]] = []
    for s in result.skill_gaps.missing_hard_skills:
        t = (s or "").strip()
        k = t.lower()
        if not k or k in seen:
            continue
        if not is_plausible_gap_skill(t, ctx):
            continue
        seen.add(k)
        out.append((t, "hard"))
    for s in result.skill_gaps.missing_soft_skills:
        t = (s or "").strip()
        k = t.lower()
        if not k or k in seen:
            continue
        if not is_plausible_gap_skill(t, ctx):
            continue
        seen.add(k)
        out.append((t, "soft"))
    return out


def _scrub_confirmed_gaps(new_gaps: SkillGapReport, confirmed: list[str]) -> SkillGapReport:
    """Remove confirmed skills from gap lists so the model does not list them again."""
    if not confirmed:
        return new_gaps
    confirmed_lower = {c.lower() for c in confirmed}
    mh = [
        s
        for s in new_gaps.missing_hard_skills
        if not any(c in str(s).lower() for c in confirmed_lower)
    ]
    ms = [
        s
        for s in new_gaps.missing_soft_skills
        if not any(c in str(s).lower() for c in confirmed_lower)
    ]
    mr = new_gaps.missing_requirements
    mskills = list(mr.missing_skills)
    if mskills:
        mskills = [
            s
            for s in mskills
            if not any(c in str(s).lower() for c in confirmed_lower)
        ]
    return new_gaps.model_copy(
        update={
            "missing_hard_skills": mh,
            "missing_soft_skills": ms,
            "missing_requirements": mr.model_copy(update={"missing_skills": mskills}),
        }
    )


def _advance_skill_yes() -> None:
    ctx = copy.deepcopy(st.session_state.get("pipeline_context"))
    if ctx is None:
        return
    q = st.session_state.skill_survey_queue
    idx = st.session_state.skill_survey_index
    if idx >= len(q):
        return
    skill_name, kind = q[idx]

    user_name = ctx.resume_data.name
    if user_name:
        add_user_skill(user_name, skill_name)

    names = {s.name.lower() for s in ctx.resume_data.skills}
    if skill_name.lower() not in names:
        cat = "hard_skill" if kind == "hard" else "soft_skill"
        ctx.resume_data.skills.append(
            Skill(name=skill_name, category=cat, proficiency="intermediate")
        )
    ar: FullAnalysis = st.session_state.analysis_result
    new_md = inject_skill_into_markdown(ar.optimized_resume, skill_name)

    st.session_state.setdefault("skill_survey_confirmed", []).append(skill_name)
    st.session_state.setdefault("skill_survey_answered", set()).add(skill_name.lower())

    st.session_state.skill_chat.append({"role": "user", "content": f"Yes — I have: {skill_name}"})
    st.session_state.skill_chat.append(
        {
            "role": "assistant",
            "content": f"Added **{skill_name}** to your optimized resume. Your fit score will update when you finish the survey.",
        }
    )

    st.session_state.analysis_result = ar.model_copy(update={"optimized_resume": new_md})
    st.session_state.resume_markdown_draft = new_md
    st.session_state._last_md_to_parse = new_md

    st.session_state.skill_survey_index = idx + 1
    st.session_state["pipeline_context"] = ctx


def _advance_skill_no() -> None:
    q = st.session_state.skill_survey_queue
    idx = st.session_state.skill_survey_index
    if idx >= len(q):
        return
    skill_name, _kind = q[idx]
    st.session_state.skill_chat.append(
        {"role": "user", "content": f"No — I don't have: {skill_name}"}
    )
    st.session_state.setdefault("skill_survey_answered", set()).add(skill_name.lower())
    st.session_state.skill_chat.append(
        {
            "role": "assistant",
            "content": "Okay — leaving that out. Next question when you're ready.",
        }
    )
    st.session_state.skill_survey_index = idx + 1


def _finalize_skill_survey() -> None:
    ctx = copy.deepcopy(st.session_state.get("pipeline_context"))
    if ctx is None:
        st.session_state.skill_survey_finished = True
        return
    try:
        ar: FullAnalysis = st.session_state.analysis_result
        old_fit = ar.fit_score
        ctx.resume_text = ar.optimized_resume
        new_fit, new_gaps = recalculate_fit_and_gaps_sync(ctx)
        st.session_state["pipeline_context"] = ctx

        confirmed = st.session_state.get("skill_survey_confirmed", [])
        new_gaps = _scrub_confirmed_gaps(new_gaps, confirmed)

        if new_fit.overall < old_fit.overall:
            new_fit = new_fit.model_copy(update={"overall": old_fit.overall})

        st.session_state.analysis_result = ar.model_copy(
            update={"fit_score": new_fit, "skill_gaps": new_gaps}
        )
        st.session_state.resume_markdown_draft = ar.optimized_resume
        st.session_state._last_md_to_parse = ar.optimized_resume
        st.session_state["_resume_score_fp"] = fingerprint_for_rescoring(ar.optimized_resume)

        new_queue = _build_skill_queue(st.session_state.analysis_result, ctx)
        answered = st.session_state.get("skill_survey_answered", set())
        already_queued = {s.lower() for s, _ in st.session_state.skill_survey_queue}
        unanswered = [
            (s, k)
            for s, k in new_queue
            if s.lower() not in answered and s.lower() not in already_queued
        ]

        if unanswered:
            st.session_state.skill_survey_queue.extend(unanswered)
            st.session_state.skill_chat.append(
                {
                    "role": "assistant",
                    "content": (
                        f"I've rescored your resume. **New overall score: {new_fit.overall}/100**.\n\n"
                        f"However, the AI identified a few more missing requirements. Let's verify them."
                    ),
                }
            )
            st.toast("Score updated, but more skills were found!", icon="🔄")
        else:
            st.session_state.skill_chat.append(
                {
                    "role": "assistant",
                    "content": (
                        f"All set. **Final overall score: {new_fit.overall}/100** "
                        f"(skill match {new_fit.skill_match}/40, "
                        f"experience {new_fit.experience_alignment}/30, "
                        f"keywords {new_fit.keyword_coverage}/30).\n\n"
                        f"{new_fit.explanation}"
                    ),
                }
            )
            st.toast("Scores & Learning Roadmap successfully updated! 🎯", icon="✅")
            st.session_state.skill_survey_finished = True

    except Exception as e:
        st.session_state.skill_chat.append(
            {
                "role": "assistant",
                "content": f"Could not refresh score after the survey: {e}",
            }
        )
        st.session_state.skill_survey_finished = True


def render_chat_assistant() -> None:
    result = st.session_state.get("analysis_result")
    ctx = st.session_state.get("pipeline_context")

    if "chat_expanded" not in st.session_state:
        st.session_state.chat_expanded = False

    def toggle_chat():
        st.session_state.chat_expanded = not st.session_state.chat_expanded

    chat_box = st.container()

    if not result or not ctx:
        if "global_chat_pre" not in st.session_state:
            st.session_state.global_chat_pre = [
                {
                    "role": "assistant",
                    "content": "Hi! I am your AI Career Assistant. To get started, you need to **upload your resume** and then **add the job description** you want to apply for in the main panel. Once you do that, click analyzing to get your results."
                }
            ]
        with chat_box:
            st.markdown("<span class='chat-container-anchor'></span>", unsafe_allow_html=True)
            if not st.session_state.chat_expanded:
                st.button("💬 Chat with AI Assistant", on_click=toggle_chat, use_container_width=True, key="btn_chat_pre")
            else:
                c1, c2 = st.columns([5, 1])
                c1.markdown("### 💬 AI Assistant")
                c2.button("✖", on_click=toggle_chat, key="btn_close_pre")
                with st.container(height=400, border=False):
                    for msg in st.session_state.global_chat_pre:
                        with st.chat_message(msg["role"]):
                            st.markdown(msg["content"])
        return

    # Post-analysis state
    if "skill_survey_queue" not in st.session_state:
        queue = _build_skill_queue(result, ctx)
        st.session_state.skill_survey_queue = queue
        st.session_state.skill_survey_index = 0
        st.session_state.skill_survey_finished = False
        st.session_state.skill_chat = [
            {
                "role": "assistant",
                "content": (
                    f"**Analysis Complete!**\n\n"
                    f"🎯 **Overall Fit Score: {result.fit_score.overall}/100**\n"
                    f"*{result.fit_score.explanation}*\n\n"
                    "---\n"
                ) + (
                    "I'll go through each **missing skill** from the analysis. "
                    "If you actually have it, say **Yes** and I'll add it to your optimized resume. "
                    "When you **finish** all questions, I'll **recalculate your fit score** and update gaps; "
                    "if the model finds more missing skills, I'll ask about those next."
                    if queue else "You have no missing skills to verify. Great job!"
                ),
            }
        ]
        if not queue:
            st.session_state.skill_survey_finished = True

    q = st.session_state.skill_survey_queue
    idx = st.session_state.skill_survey_index

    with chat_box:
        st.markdown("<span class='chat-container-anchor'></span>", unsafe_allow_html=True)
        if not st.session_state.chat_expanded:
            st.button("💬 Chat with AI Assistant", on_click=toggle_chat, use_container_width=True, key="btn_chat_post")
        else:
            c1, c2 = st.columns([5, 1])
            c1.markdown("### 💬 Skill Check")
            c2.button("✖", on_click=toggle_chat, key="btn_close_post")
            st.caption(
                "Answer one skill at a time. Confirmed skills are added under the best-matching skill category, "
                "or under **Others** when a category would have fewer than three items."
            )
            
            with st.container(height=400, border=False):
                for msg in st.session_state.skill_chat:
                    with st.chat_message(msg["role"]):
                        st.markdown(msg["content"])

                if getattr(st.session_state, "skill_survey_finished", False):
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
                        f"Do you have **{skill_name}**?"
                    )

                c3, c4 = st.columns(2)
                with c3:
                    st.button("Yes — Add", key=f"skill_yes_{idx}", type="primary", use_container_width=True, on_click=_advance_skill_yes)
                with c4:
                    st.button("No / skip", key=f"skill_no_{idx}", use_container_width=True, on_click=_advance_skill_no)
