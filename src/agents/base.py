"""Shared LLM model factory for all pydantic-ai agents."""

from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

from src.config import settings


def make_llm_model() -> OpenAIChatModel:
    return OpenAIChatModel(
        settings.ollama_model,
        provider=OpenAIProvider(
            base_url=settings.ollama_base_url,
            api_key="ollama",
        ),
    )
