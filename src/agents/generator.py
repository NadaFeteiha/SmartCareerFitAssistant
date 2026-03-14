from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider
from src.agents.analyzer import AnalysisContext
from src.config import settings


def _make_model() -> OpenAIModel:
    return OpenAIModel(
        settings.ollama_model,
        provider=OpenAIProvider(
            base_url=settings.ollama_base_url,
            api_key="ollama",
        ),
    )


# ── Resume Writer ─────────────────────────────────────────────────────────────

resume_writer = Agent(
    _make_model(),
    output_type=str,
    deps_type=AnalysisContext,
    retries=2,
    system_prompt="""
    You are an expert resume writer.
        Rewrite the candidate's resume to be ATS-optimized for the target job.

        Rules:
        1. NEVER fabricate experience or skills
        2. Reframe existing skills using the job's language
        3. Add missing keywords naturally where the candidate has relevant experience
        4. Use strong action verbs and quantify results where possible
        5. Return the resume in structured Markdown format. Use exactly the following markdown headers:
           - `# [Candidate Name]` at the very top
           - Contact info separated by `|` right below the name (e.g., `phone | email | linkedin`)
           - `## [Section Name]` for main sections (e.g., `## EXPERIENCE`, `## SKILLS`)
           - `### [Job Title] | [Company] | [Dates] | [Location]` for experience entries
           - `- [Bullet point]` for bullet points
           - `**[Skill Category]:** [Skills]` for skills lists
    """,
)

@resume_writer.system_prompt
def _resume_context(ctx: RunContext[AnalysisContext]) -> str:
    return f"""
                Original resume:
                {ctx.deps.resume_text}

                Target job: {ctx.deps.job_data.title} at {ctx.deps.job_data.company}
                Key keywords to include: {ctx.deps.job_data.keywords}
            """


# ── Cover Letter Writer ───────────────────────────────────────────────────────

cover_letter_writer = Agent(
    _make_model(),
    output_type=str,
    deps_type=AnalysisContext,
    retries=2,
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

try:
    from pipeline.generator import generate_with_prompt
except ImportError:
    pass # To not break the existing script since this module is unknown
import os

def generate_resume(resume_text: str, job_description: str) -> str:
    """
    Generates a new, tailored resume to align with the given job description.
    """
    prompt_path = os.path.join(os.path.dirname(__file__), "..", "prompts", "resume_prompt.txt")
    
    variables = {
        "job_description": job_description,
        "resume_text": resume_text
    }
    
    return generate_with_prompt(prompt_path, variables)