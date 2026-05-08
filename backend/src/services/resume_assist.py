"""AI assist + import helpers for the structured resume editor."""

import uuid

from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider

from src.agents.extractor import extract_resume
from src.config import completion_settings, get_model, settings
from src.models.structured_resume import (
    EducationEntry,
    ExperienceEntry,
    PersonalInfo,
    StructuredResume,
)


def _default_model() -> OpenAIModel:
    return OpenAIModel(
        settings.ollama_model,
        provider=OpenAIProvider(base_url=settings.ollama_base_url, api_key="ollama"),
    )


_ACTIONS = {
    "improve_writing": (
        "Rewrite the text to be clearer, more concise, and more impactful. "
        "Use strong action verbs and quantify achievements where the source supports it. "
        "Do NOT invent facts. Preserve any existing markdown bullet structure."
    ),
    "suggest_content": (
        "Suggest 2-4 additional bullet points that plausibly fit the role described. "
        "Each suggestion must be marked clearly as a suggestion (do not assert as fact). "
        "Append them to the original text under a 'Suggested additions:' heading."
    ),
    "grammar_check": (
        "Fix grammar, spelling, and punctuation errors. "
        "Do NOT change meaning, tone, or structure. Return the corrected text only."
    ),
    "shorter": (
        "Tighten the text. Remove filler. Cut length by roughly 30-50% while preserving "
        "all key facts, metrics, and proper nouns."
    ),
}


_assist_agent = Agent(
    _default_model(),
    output_type=str,
    retries=2,
    model_settings=completion_settings(2000),
    system_prompt=(
        "You rewrite short pieces of resume text. "
        "Return ONLY the rewritten text in plain Markdown — no preamble, no quotes, "
        "no explanations, no surrounding code fences."
    ),
)


async def assist_text(text: str, action: str) -> str:
    instruction = _ACTIONS.get(action)
    if not instruction:
        raise ValueError(f"Unknown assist action: {action}")
    if not text.strip():
        return text
    prompt = f"INSTRUCTION: {instruction}\n\nORIGINAL TEXT:\n{text}"
    result = await _assist_agent.run(prompt, model=get_model())
    return result.output.strip()


async def import_text_to_structured(text: str) -> StructuredResume:
    """Parse raw resume text into a StructuredResume using the existing extractor."""
    parsed = await extract_resume(text)
    structured = StructuredResume(
        personal=PersonalInfo(
            name=parsed.name or "",
            email=parsed.email or "",
            summary=parsed.summary or "",
        ),
        skills=[s.name for s in parsed.skills if s.name],
        education=[
            EducationEntry(id=str(uuid.uuid4()), degree=line, description="")
            for line in (parsed.education or [])
            if line
        ],
        experience=[
            ExperienceEntry(
                id=str(uuid.uuid4()),
                title=exp.title or "",
                company=exp.company or "",
                start_date=exp.duration or "",
                description="\n".join(f"- {h}" for h in exp.highlights) if exp.highlights else "",
            )
            for exp in (parsed.experiences or [])
        ],
    )
    return structured
