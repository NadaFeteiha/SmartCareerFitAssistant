"""Sidebar component — branding + user profile form."""

import streamlit as st


def render_sidebar() -> dict:
    """
    Render the sidebar with branding and profile form.
    Returns the current profile dict from session state.
    """
    with st.sidebar:
        st.markdown("""
        <div style="padding: 20px 0 16px; border-bottom: 1px solid #1e2535; margin-bottom: 20px;">
            <div class="sidebar-logo">SmartCareerFit</div>
            <div class="sidebar-sub">Your AI career co-pilot</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("**Your Profile**")
        st.caption("Personalizes your cover letter and resume tone.")

        # Pre-fill from session state if a profile was saved before
        saved = st.session_state.get("profile", {})

        with st.form("profile_form"):
            current_title = st.text_input(
                "Current Job Title",
                value=saved.get("current_title", ""),
                placeholder="e.g. Software Engineer",
            )
            target_roles = st.text_input(
                "Target Roles",
                value=saved.get("target_roles", ""),
                placeholder="e.g. Data Scientist, ML Engineer",
            )
            tone = st.selectbox(
                "Writing Tone",
                ["Professional", "Conversational", "Confident", "Enthusiastic"],
                index=["Professional", "Conversational", "Confident", "Enthusiastic"].index(
                    saved.get("tone", "Professional")
                ),
            )
            strengths = st.text_area(
                "Key Strengths",
                value=saved.get("strengths", ""),
                height=80,
                placeholder="What makes you stand out?",
            )
            goals = st.text_area(
                "Career Goals",
                value=saved.get("goals", ""),
                height=68,
                placeholder="Where do you want to be?",
            )

            if st.form_submit_button("Save Profile"):
                st.session_state["profile"] = {
                    "current_title": current_title,
                    "target_roles": target_roles,
                    "tone": tone,
                    "strengths": strengths,
                    "goals": goals,
                }
                st.success("Profile saved!")

    return st.session_state.get("profile", {})