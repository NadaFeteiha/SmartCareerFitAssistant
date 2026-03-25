from pydantic_ai import Agent, RunContext

from src.agents.base import make_llm_model
from src.agents.context import AnalysisContext
from src.agents.token_budget import truncate_to_token_budget
from src.config import completion_settings, settings

RESUME_WRITER_PROMPT_VERSION = "v1.2"
COVER_LETTER_PROMPT_VERSION = "v1.0"

RESUME_WRITER_USER_PROMPT = (
    "Rewrite this resume for the target job. Include a tailored ## SUMMARY section "
    "(2–4 sentences) based on the resume and job description, then EXPERIENCE, EDUCATION, and SKILLS."
)

# ── Resume Writer ─────────────────────────────────────────────────────────────

resume_writer = Agent(
    make_llm_model(),
    output_type=str,
    deps_type=AnalysisContext,
    retries=2,
    model_settings=completion_settings(8000),
    system_prompt=f"""
    You are an expert resume writer.
        Rewrite the candidate's resume to be ATS-optimized for the target job.
        (prompt_version={RESUME_WRITER_PROMPT_VERSION})

        CRITICAL RULES:
        1. NEVER fabricate experience, skills, or education - ONLY use what exists in the original resume
        2. Do NOT add the target company as work experience under any circumstances
        3. Do not add companies, job titles, or dates that are not in the original resume
        4. NEVER create fake internships or positions at the company the user is applying to
        5. Reframe existing skills using the job's language
        6. Naturally integrate the employer's top ATS keywords (provided below) where they align with real experience — do not invent experience to place a keyword
        7. Use strong action verbs and quantify results where possible
        8. Return the resume in structured Markdown format. Use exactly the following markdown headers:
           - `# [Candidate Name]` at the very top
           - Contact info separated by `|` right below the name using their actual details from the original resume (e.g., `123-456-7890 | email@example.com | linkedin.com/in/user`)
           - `## [Section Name]` for main sections
           - `### [Job Title] | [Company] | [Dates] | [Location]` for experience entries
           - `### [Degree] | [University] | [Dates] | [Location]` for education entries
           - `- [Bullet point]` for bullet points
        9. SUMMARY (required): Immediately after the contact line, include `## SUMMARY` as the first body section (before EXPERIENCE). Write 2–4 tight sentences that:
           - Align the candidate's real strengths and years/domain with the target role and company context from the job description
           - Naturally weave in a few of the top ATS keywords where they reflect truth from the resume (do not claim skills or experience that are not in the original resume)
           - Use confident, third-person or implied subject professional tone (no "I" if it sounds awkward; "Experienced …" / "Results-driven …" is fine)
           - Do not repeat the job title verbatim as the only content; add concrete hooks from their background
        10. SKILL FILTERING (required): When generating the SKILLS section, omit skills that are clearly
            irrelevant to the target job domain. Keep all skills that appear in the job description or have
            reasonable relevance to the role. See the dynamic skill filtering context appended below for details.
        11. Section order must be: `## SUMMARY`, then `## EXPERIENCE`, then `## EDUCATION`, then `## SKILLS` (add other sections like PROJECTS only if present in the source resume).
        12. For the SKILLS section, ALWAYS group skills into logical sub-categories instead of writing one long list. Prefer this format (category on its own line; skills follow on the same line or the next line, comma-separated):
           - `**[Category Label]:**` then skills such as `Python, Java, Kotlin` (e.g., `**Languages & Frameworks:**` then `Python, Java, TypeScript`)
           - Use clear labels similar to: Languages & Frameworks, Backend & Databases, AI/ML, Cloud & DevOps, Tools & Practices — adapted to what the candidate actually has.
        13. ALWAYS include an EDUCATION section with the candidate's actual education from their original resume.
        14. Include EXPERIENCE, EDUCATION, and SKILLS at minimum (plus SUMMARY as above).
        
        ABSOLUTELY NO FABRICATION: Your job is to reformat and optimize existing content ONLY.
        Do NOT create new experience, especially not at the target company.
    """,
)


@resume_writer.system_prompt
def _resume_context(ctx: RunContext[AnalysisContext]) -> str:
    education_info = ""
    if ctx.deps.resume_data.education:
        education_info = f"\nCandidate's education: {', '.join(ctx.deps.resume_data.education)}"

    top_ats = ctx.deps.job_data.keywords[:10] if ctx.deps.job_data.keywords else []
    source_resume = truncate_to_token_budget(
        (ctx.deps.resume_text or ""),
        settings.resume_writer_source_tokens,
    )
    return f"""
                Original resume:
                {source_resume}

                Target job: {ctx.deps.job_data.title} at {ctx.deps.job_data.company}
                Full keyword list from JD extraction: {ctx.deps.job_data.keywords}{education_info}

                Top 10 ATS keywords to weave in where truthful (skills, bullets, summary):
                {top_ats}

                WARNING: Do NOT add "{ctx.deps.job_data.company}" as work experience.
                Only use experience from the original resume above.
            """


@resume_writer.system_prompt
def _resume_writer_skill_filter_context(ctx: RunContext[AnalysisContext]) -> str:
    candidate_skills = [s.name for s in ctx.deps.resume_data.skills]
    job_title = ctx.deps.job_data.title
    job_keywords = list(ctx.deps.job_data.keywords)
    required_skill_names = [s.name for s in ctx.deps.job_data.required_skills]

    return f"""
SKILL FILTERING RULES (apply during resume generation):

Target job title: {job_title}
Job keywords: {", ".join(job_keywords)}
Required/preferred skills from JD: {", ".join(required_skill_names)}
Candidate's current skills: {", ".join(candidate_skills)}

When writing the SKILLS section:
1. KEEP a skill if it appears in the job keywords, required skills, OR is broadly relevant to the job domain/role.
2. REMOVE a skill if it is completely unrelated to the target role AND does not appear in the job description.
   - Example: Applying for Android Developer → remove RAG, LLM fine-tuning, data pipelines, R, MATLAB unless the JD mentions them.
   - Example: Applying for Backend Python Engineer → remove iOS/Swift, Unity, mobile UI frameworks unless the JD mentions them.
3. When in doubt about relevance, KEEP the skill — only remove skills that are clearly irrelevant domain mismatch.
4. NEVER remove skills that appear in the job description or required skills list.
5. Do NOT add new skills not present in the original resume.
6. You may reorganize remaining skills into cleaner categories suited to the target role.
"""


# ── Cover Letter Writer ───────────────────────────────────────────────────────

cover_letter_writer = Agent(
    make_llm_model(),
    output_type=str,
    deps_type=AnalysisContext,
    retries=2,
    model_settings=completion_settings(4000),
    system_prompt=f"""You are a professional cover letter writer.
(prompt_version={COVER_LETTER_PROMPT_VERSION})
Write a tailored, concise cover letter (3-4 paragraphs).

Rules:
- Reference the candidate's strongest matching qualifications
- Use concrete accomplishments and themes from the resume excerpt when they support fit
- Relate your narrative to the job responsibilities where relevant
- Do not use generic openers like "I am writing to apply"
- Address it to the hiring team at the specific company
- Return the cover letter in professional plaintext format. You may use `**bold**` or `*italic*` for emphasis if needed.""",
)


@cover_letter_writer.system_prompt
def _cover_letter_context(ctx: RunContext[AnalysisContext]) -> str:
    top_skills = [s.name for s in ctx.deps.resume_data.skills[:5]]
    resume_body = truncate_to_token_budget(
        (ctx.deps.resume_text or ""),
        settings.cover_letter_resume_excerpt_tokens,
    )
    resp_lines = ctx.deps.job_data.responsibilities or []
    resp_blob = "\n".join(str(r) for r in resp_lines)
    responsibilities = truncate_to_token_budget(
        resp_blob,
        settings.cover_letter_jd_responsibilities_tokens,
    )
    return f"""
                Candidate name: {ctx.deps.resume_data.name}
                Target job: {ctx.deps.job_data.title} at {ctx.deps.job_data.company}
                Candidate's top skills: {top_skills}
                Candidate summary: {ctx.deps.resume_data.summary}

                Resume excerpt (ground truth for accomplishments; do not invent beyond this):
                ---
                {resume_body}
                ---

                Key job responsibilities from the posting:
                ---
                {responsibilities}
                ---
            """


def stream_optimized_resume_text(ctx: AnalysisContext):
    """
    Stream resume Markdown deltas for UIs (e.g. Streamlit ``st.write_stream``).
    Post-process with ``consolidate_small_skill_categories`` on the final string.
    """
    response = resume_writer.run_stream_sync(
        RESUME_WRITER_USER_PROMPT,
        deps=ctx,
    )
    yield from response.stream_text(delta=True, debounce_by=None)
