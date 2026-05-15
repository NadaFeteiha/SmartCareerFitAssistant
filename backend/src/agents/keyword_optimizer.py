"""PydanticAI agent: extract top ATS keywords from a job description."""

from pydantic import BaseModel, Field
from pydantic_ai import Agent, ModelSettings
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

from src.agents.utils import parse_model
from src.config import completion_settings, get_model, settings


class _KeywordOutput(BaseModel):
    top_keywords: list[str] = Field(default_factory=list)


def _default_model() -> OpenAIChatModel:
    """Ollama model used only for agent construction; overridden at run time via get_model()."""
    return OpenAIChatModel(
        settings.ollama_model,
        provider=OpenAIProvider(base_url=settings.ollama_base_url, api_key="ollama"),
    )


_keyword_agent = Agent(
    _default_model(),
    output_type=str,
    retries=2,
    model_settings=ModelSettings(**completion_settings(4000)),
    system_prompt="""
    You extract ATS-relevant keywords from job descriptions.
    Return ONLY a JSON object with this exact shape:
    {"top_keywords": ["keyword1", "keyword2", "..."]}

    Rules:
    - Exactly 10 distinct keywords or short phrases (1–3 words each)
    - Prefer hard skills, tools, methodologies, and domain terms from the posting
    - Lowercase except proper nouns (e.g. AWS, Kubernetes)
    - No markdown, no extra keys, just the JSON object
    """,
)


async def extract_top_jd_keywords(job_text: str) -> list[str]:
    """Return up to 10 high-value keywords for resume optimization."""
    raw = (
        await _keyword_agent.run(f"Job description:\n{job_text[:12000]}", model=get_model())
    ).output
    parsed = parse_model(raw, _KeywordOutput)

    out: list[str] = []
    seen: set[str] = set()
    for x in parsed.top_keywords:
        t = (x or "").strip()
        if not t:
            continue
        key = t.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(t)
        if len(out) >= 10:
            break
    return out
