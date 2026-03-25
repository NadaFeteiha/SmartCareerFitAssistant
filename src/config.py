"""
Application settings and shared LLM helpers.
All agents import _make_model() and completion_settings() from here —
never define their own copies.
"""
from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    ollama_model: str = "llama3.2"
    ollama_base_url: str = "http://localhost:11434/v1"
    db_path: str = "data/career_assistant.db"
    debug: bool = True

    # Prompt token budgets (see ``truncate_to_token_budget`` in agents)
    resume_writer_source_tokens: int = 8192
    cover_letter_resume_excerpt_tokens: int = 4096
    cover_letter_jd_responsibilities_tokens: int = 2048

    # Optional Ollama embedding skill alignment (``skill_matching.py``)
    skill_embedding_enabled: bool = False
    skill_embedding_max_skill_terms: int = 48
    skill_embedding_similarity_floor: float = 0.45
    skill_embedding_max_pairs_in_prompt: int = 12


settings = Settings()


def make_model() -> OpenAIModel:
    """Shared factory — one place to swap the backend for all agents."""
    return OpenAIModel(
        settings.ollama_model,
        provider=OpenAIProvider(
            base_url=settings.ollama_base_url,
            api_key="ollama",
        ),
    )


def completion_settings(max_tokens: int = 4000) -> dict:
    return {"max_tokens": max_tokens}