import json
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider
from src.agents.utils import unwrap_llm_json
from src.models.resume import ResumeData
from src.models.job import JobRequirements
from src.config import settings


def _make_model() -> OpenAIModel:
    return OpenAIModel(
        settings.ollama_model,
        provider=OpenAIProvider(
            base_url=settings.ollama_base_url,
            api_key="ollama",
        ),
    )


def _unwrap_tool_call(raw: str) -> str:
    """Unwrap llama3.2 tool-call envelopes to raw JSON data."""
    try:
        parsed = json.loads(raw)
        if isinstance(parsed, dict) and "parameters" in parsed:
            return json.dumps(parsed["parameters"])
        # Already flat JSON — return as-is
        return raw
    except json.JSONDecodeError:
        return raw


def _sanitize_job_requirements(raw: str) -> str:
    """Normalize LLM job-extractor output to satisfy JobRequirements schema."""
    clean = unwrap_llm_json(raw)

    try:
        data = json.loads(clean)
    except json.JSONDecodeError:
        return clean

    if not isinstance(data, dict):
        return clean

    if not isinstance(data.get("required_skills"), list):
        data["required_skills"] = []

    for idx, skill in enumerate(data.get("required_skills", [])):
        if not isinstance(skill, dict):
            data["required_skills"][idx] = {"name": str(skill), "importance": "required", "category": ""}
            continue

        # Ensure fields exist and are strings
        name = skill.get("name")
        importance = skill.get("importance")
        category = skill.get("category")

        if name is None:
            name = ""
        if importance is None:
            importance = "required"
        if category is None:
            category = ""

        data["required_skills"][idx] = {
            "name": str(name),
            "importance": str(importance),
            "category": str(category),
        }

    return json.dumps(data)


# --- Resume extractor ---
_resume_agent = Agent(
    _make_model(),
    output_type=str,   # Get raw string first, parse manually
    retries=3,
    system_prompt="""You are a resume parser. Extract structured data from the resume text.

Return ONLY a JSON object with exactly these fields:
{
  "name": "full name as string",
  "email": "email or empty string",
  "summary": "1-2 sentence professional summary",
  "education": ["degree and school as string"],
  "skills": [
    {"name": "skill name", "category": "programming|data|soft_skill|other", "proficiency": "beginner|intermediate|advanced"}
  ],
  "experiences": [
    {
      "title": "job title",
      "company": "company name",
      "duration": "date range",
      "highlights": ["achievement 1", "achievement 2"]
    }
  ]
}

No markdown. No explanation. No wrapper keys. Just the JSON object.""",
)


async def extract_resume(text: str) -> ResumeData:
    """Run the resume extractor and validate the output as ResumeData."""
    raw = (await _resume_agent.run(text)).output
    clean = unwrap_llm_json(raw)

    try:
        return ResumeData.model_validate_json(clean)
    except Exception as e:
        print(f"\n[DEBUG] Raw resume LLM output:\n{raw}\n")
        print(f"[DEBUG] After unwrap:\n{clean}\n")
        raise


# --- Job description extractor ---
_job_agent = Agent(
    _make_model(),
    output_type=str,   # Get raw string first, parse manually
    retries=3,
    system_prompt="""You are a job description parser. Extract structured data.

Return ONLY a JSON object with exactly these fields:
{
  "title": "job title",
  "company": "company name or empty string",
  "experience_years": 0,
  "keywords": ["keyword1", "keyword2"],
  "responsibilities": ["responsibility 1", "responsibility 2"],
  "required_skills": [
    {"name": "skill name", "importance": "required|preferred", "category": "programming|data|soft_skill|other"}
  ]
}

No markdown. No explanation. No wrapper keys. Just the JSON object.""",
)


async def extract_job(text: str) -> JobRequirements:
    """Run the job extractor and validate the output as JobRequirements."""
    raw = (await _job_agent.run(text)).output
    clean = _sanitize_job_requirements(raw)

    try:
        return JobRequirements.model_validate_json(clean)
    except Exception:
        print(f"\n[DEBUG] Raw JD LLM output:\n{raw}\n")
        print(f"[DEBUG] After sanitize:\n{clean}\n")
        raise


# Keep these names for backward compatibility with pipeline.py
resume_extractor = _resume_agent
job_extractor = _job_agent