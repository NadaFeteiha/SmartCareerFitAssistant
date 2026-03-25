from typing import Any
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

"""
This module defines the configuration settings for the Smart Career Fit Assistant application.
It uses Pydantic's BaseSettings to manage environment variables and default values for various settings.
"""


class Settings(BaseSettings):
    ollama_model: str = "llama3.2"
    ollama_base_url: str = "http://localhost:11434/v1"
    db_path: str = "data/career_assistant.db"
    app_name: str = "Smart Career Fit Assistant"
    debug: bool = True
    # LLM sampling: 0.0 maximizes reproducibility for the same resume + JD (default was stochastic).
    llm_temperature: float = Field(default=0.0, ge=0.0, le=2.0)
    # Optional seed for OpenAI-compatible backends that support it (e.g. some Ollama builds). Set in .env for strict runs.
    llm_seed: int | None = None

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()


def completion_settings(max_tokens: int = 4000) -> dict[str, Any]:
    """Shared chat-completions options for all pydantic-ai agents (deterministic by default)."""
    out: dict[str, Any] = {"max_tokens": max_tokens, "temperature": settings.llm_temperature}
    if settings.llm_seed is not None:
        out["seed"] = settings.llm_seed
    return out
