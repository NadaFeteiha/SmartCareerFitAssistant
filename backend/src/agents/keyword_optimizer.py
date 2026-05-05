"""PydanticAI agent: extract top ATS keywords from a job description."""

import json

from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider

from src.agents.utils import unwrap_llm_json
from src.config import completion_settings, get_model, settings


def _default_model() -> OpenAIModel:
    """Ollama model used only for agent construction; overridden at run time via get_model()."""
    return OpenAIModel(
        settings.ollama_model,
        provider=OpenAIProvider(base_url=settings.ollama_base_url, api_key="ollama"),
    )


_keyword_agent = Agent(
    _default_model(),
    output_type=str,
    retries=2,
    model_settings=completion_settings(1500),
    system_prompt="""You extract ATS-relevant keywords from job descriptions.

Return ONLY a JSON object:
{ "top_keywords": ["keyword1", "keyword2", ...] }

Rules:
- Exactly 10 distinct keywords or short phrases (1–3 words each)
- Prefer hard skills, tools, methodologies, and domain terms from the posting
- Lowercase except proper nouns (e.g. AWS, Kubernetes)
- No markdown, no extra keys""",
)


async def extract_top_jd_keywords(job_text: str) -> list[str]:
    """Return up to 10 high-value keywords for resume optimization."""
    raw = (await _keyword_agent.run(f"Job description:\n{job_text[:12000]}", model=get_model())).output
    clean = unwrap_llm_json(raw)
    try:
        data = json.loads(clean)
    except json.JSONDecodeError:
        return []

    if not isinstance(data, dict):
        return []

    kws = data.get("top_keywords") or []
    if not isinstance(kws, list):
        return []

    out: list[str] = []
    seen: set[str] = set()
    for x in kws:
        if not isinstance(x, str):
            continue
        t = x.strip()
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
