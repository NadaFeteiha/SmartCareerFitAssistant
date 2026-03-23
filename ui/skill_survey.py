"""Post-analysis skill check — callbacks only (no nested ``if st.button()``)."""

from __future__ import annotations

import streamlit as st

from src.agents.analyzer import AnalysisContext
from src.models.analysis import FullAnalysis
from src.models.resume import Skill
from src.services.pipeline import recalculate_fit_and_gaps_sync
from src.utils.resume_sections import inject_skill_into_markdown
from src.database.repository import add_user_skill


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
    st.session_state.analysis_result = ar.model_copy(update={"optimized_resume": new_md})
    st.session_state.resume_markdown_draft = new_md
    st.session_state.skill_chat.append({"role": "user", "content": f"Yes — I have: {skill_name}"})
    st.session_state.setdefault("skill_survey_confirmed", []).append(skill_name)
    st.session_state.setdefault("skill_survey_answered", set()).add(skill_name.lower())
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
    st.session_state.setdefault("skill_survey_answered", set()).add(skill_name.lower())
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
        
        # Scrub confirmed skills so AI doesn't hallucinate them back
        confirmed = st.session_state.get("skill_survey_confirmed", [])
        if confirmed:
            confirmed_lower = {c.lower() for c in confirmed}
            new_gaps.missing_hard_skills = [
                s for s in new_gaps.missing_hard_skills 
                if not any(c in str(s).lower() for c in confirmed_lower)
            ]
            new_gaps.missing_soft_skills = [
                s for s in new_gaps.missing_soft_skills 
                if not any(c in str(s).lower() for c in confirmed_lower)
            ]
            if new_gaps.missing_requirements and new_gaps.missing_requirements.missing_skills:
                new_gaps.missing_requirements.missing_skills = [
                    s for s in new_gaps.missing_requirements.missing_skills 
                    if not any(c in str(s).lower() for c in confirmed_lower)
                ]

        # Ensure overall score does not decrease upon adding a confirmed skill
        if new_fit.overall < old_fit.overall:
            new_fit.overall = old_fit.overall
            
        st.session_state.analysis_result = ar.model_copy(
            update={"fit_score": new_fit, "skill_gaps": new_gaps}
        )

        new_queue = _build_skill_queue(st.session_state.analysis_result)
        answered = st.session_state.get("skill_survey_answered", set())
        unanswered = [(s, k) for s, k in new_queue if s.lower() not in answered]

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
        queue = _build_skill_queue(result)
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
                    "When we're done, I'll recalculate your score globally."
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
            st.caption("Answer one skill at a time. Confirmed skills are appended under “Additional skills (self-confirmed)” on your optimized resume.")
            
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
