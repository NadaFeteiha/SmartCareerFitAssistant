from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider
from src.agents.analyzer import AnalysisContext
from src.config import completion_settings, settings


def _default_model() -> OpenAIModel:
    """Ollama model used only for agent construction; overridden at run time via get_model()."""
    return OpenAIModel(
        settings.ollama_model,
        provider=OpenAIProvider(base_url=settings.ollama_base_url, api_key="ollama"),
    )


# ── Resume Writer ─────────────────────────────────────────────────────────────

resume_writer = Agent(
    _default_model(),
    output_type=str,
    deps_type=AnalysisContext,
    retries=2,
    model_settings=completion_settings(8000),
    system_prompt="""
    You are an expert resume writer.
        Rewrite the candidate's resume to be ATS-optimized for the target job.

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
        10. Section order must be: `## SUMMARY`, then `## EXPERIENCE`, then `## EDUCATION`, then `## SKILLS` (add other sections like PROJECTS only if present in the source resume).
        11. For the SKILLS section, ALWAYS group skills into logical sub-categories instead of writing one long list. Prefer this format (category on its own line; skills follow on the same line or the next line, comma-separated):
           - `**[Category Label]:**` then skills such as `Python, Java, Kotlin` (e.g., `**Languages & Frameworks:**` then `Python, Java, TypeScript`)
           - Use clear labels similar to: Languages & Frameworks, Backend & Databases, AI/ML, Cloud & DevOps, Tools & Practices — adapted to what the candidate actually has.
        12. ALWAYS include an EDUCATION section with the candidate's actual education from their original resume.
        13. Include EXPERIENCE, EDUCATION, and SKILLS at minimum (plus SUMMARY as above).

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
    return f"""
                Original resume:
                {ctx.deps.resume_text}

                Target job: {ctx.deps.job_data.title} at {ctx.deps.job_data.company}
                Full keyword list from JD extraction: {ctx.deps.job_data.keywords}{education_info}

                Top 10 ATS keywords to weave in where truthful (skills, bullets, summary):
                {top_ats}

                WARNING: Do NOT add "{ctx.deps.job_data.company}" as work experience.
                Only use experience from the original resume above.
            """


# ── Cover Letter Writer ───────────────────────────────────────────────────────

cover_letter_writer = Agent(
    _default_model(),
    output_type=str,
    deps_type=AnalysisContext,
    retries=2,
    model_settings=completion_settings(4000),
    system_prompt="""You are a professional cover letter writer.
Write a tailored, concise cover letter (3-4 paragraphs).

Rules:
- Reference the candidate's strongest matching qualifications
- Do not use generic openers like "I am writing to apply"
- Address it to the hiring team at the specific company
- Return the cover letter in professional plaintext format. You may use `**bold**` or `*italic*` for emphasis if needed.""",
)

@cover_letter_writer.system_prompt
def _cover_letter_context(ctx: RunContext[AnalysisContext]) -> str:
    top_skills = [s.name for s in ctx.deps.resume_data.skills[:5]]
    return f"""
                Candidate name: {ctx.deps.resume_data.name}
                Target job: {ctx.deps.job_data.title} at {ctx.deps.job_data.company}
                Candidate's top skills: {top_skills}
                Candidate summary: {ctx.deps.resume_data.summary}
            """
