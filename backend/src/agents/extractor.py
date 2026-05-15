from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.settings import ModelSettings

from src.agents.utils import parse_model
from src.models.resume import ResumeData
from src.models.job import JobRequirements
from src.config import completion_settings, get_model, settings


def _default_model() -> OpenAIChatModel:
    """Ollama model used only for agent construction; overridden at run time via get_model()."""
    return OpenAIChatModel(
        settings.ollama_model,
        provider=OpenAIProvider(base_url=settings.ollama_base_url, api_key="ollama"),
    )


_resume_agent = Agent(
    _default_model(),
    output_type=str,
    retries=3,
    model_settings=ModelSettings(**completion_settings(4000)),
    system_prompt="""You are a resume parser. Return ONLY a JSON object with this exact shape:
{
  "name": "Full Name",
  "email": "email or empty string",
  "summary": "1-2 sentence professional summary",
  "education": ["degree and school as a single string"],
  "skills": [
    {"name": "skill", "category": "programming|data|soft_skill|other", "proficiency": "beginner|intermediate|advanced"}
  ],
  "experiences": [
    {
      "title": "job title",
      "company": "company",
      "duration": "date range",
      "highlights": ["achievement 1", "achievement 2"]
    }
  ]
}

No markdown, no commentary, no wrapper keys — just the JSON object.""",
)


async def extract_resume(text: str) -> ResumeData:
    raw = (await _resume_agent.run(text, model=get_model())).output
    return parse_model(raw, ResumeData)


_job_agent = Agent(
    _default_model(),
    output_type=str,
    retries=3,
    model_settings=ModelSettings(**completion_settings(4000)),
    system_prompt="""
      You are a job description parser. Return ONLY a JSON object with this exact shape:
      {
        "title": "job title",
        "company": "company or empty string",
        "experience_years": 0,
        "keywords": ["keyword1", "keyword2"],
        "responsibilities": ["responsibility 1", "responsibility 2"],
        "required_skills": [
          {"name": "skill", "importance": "required|preferred", "category": "programming|data|soft_skill|other"}
        ]
      }
      No markdown, no commentary, no wrapper keys — just the JSON object.
    """,
)


async def extract_job(text: str) -> JobRequirements:
    raw = (await _job_agent.run(text, model=get_model())).output
    return parse_model(raw, JobRequirements)


resume_extractor = _resume_agent
job_extractor = _job_agent
