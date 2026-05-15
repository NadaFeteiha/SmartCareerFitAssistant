from typing import Any

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Ollama settings
    ollama_model: str = "llama3.2"
    ollama_base_url: str = "http://localhost:11434/v1"
    # Anthropic / Claude settings
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-6"
    # Active provider: "ollama" | "anthropic"
    llm_provider: str = "ollama"
    # Other settings
    db_path: str = "data/career_assistant.db"
    app_name: str = "Smart Career Fit Assistant"
    debug: bool = True
    llm_temperature: float = Field(default=0.0, ge=0.0, le=2.0)
    llm_seed: int | None = None

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()

# Runtime-overridable config (set via /api/config endpoint)
_runtime_provider: str | None = None
_runtime_api_key: str | None = None
_runtime_model_name: str | None = None


def set_runtime_config(provider: str, api_key: str = "", model_name: str = "") -> None:
    global _runtime_provider, _runtime_api_key, _runtime_model_name
    _runtime_provider = provider
    _runtime_api_key = api_key or None
    _runtime_model_name = model_name or None


def get_runtime_config() -> dict[str, str]:
    return {
        "provider": _runtime_provider or settings.llm_provider,
        "model_name": _runtime_model_name or (
            settings.anthropic_model if (_runtime_provider or settings.llm_provider) == "anthropic"
            else settings.ollama_model
        ),
        "has_api_key": bool(_runtime_api_key or settings.anthropic_api_key),
    }


def get_active_provider() -> str:
    return _runtime_provider or settings.llm_provider


def get_model():
    """Return the appropriate pydantic-ai model based on current runtime config.

    For Anthropic, attaches model-level settings that enable prompt caching on
    the (static) system instructions — system prompts are reused on every call,
    so caching them yields ~90% cost reduction and 5x lower latency on the
    cached prefix. User messages (resume / job text) change per request and
    are intentionally NOT cached.
    """
    provider = get_active_provider()

    if provider == "anthropic":
        from pydantic_ai.models.anthropic import AnthropicModel
        from pydantic_ai.providers.anthropic import AnthropicProvider

        api_key = _runtime_api_key or settings.anthropic_api_key
        if not api_key:
            raise ValueError("Anthropic API key is required. Set it via the settings panel or ANTHROPIC_API_KEY env var.")
        model_name = _runtime_model_name or settings.anthropic_model
        return AnthropicModel(
            model_name,
            provider=AnthropicProvider(api_key=api_key),
            settings={"anthropic_cache_instructions": True},
        )
    else:  # ollama
        from pydantic_ai.models.openai import OpenAIChatModel
        from pydantic_ai.providers.openai import OpenAIProvider

        model_name = _runtime_model_name or settings.ollama_model
        return OpenAIChatModel(
            model_name,
            provider=OpenAIProvider(
                base_url=settings.ollama_base_url,
                api_key="ollama",
            ),
        )


def completion_settings(max_tokens: int = 4000) -> dict[str, Any]:
    """Shared chat-completions options for all pydantic-ai agents."""
    out: dict[str, Any] = {"max_tokens": max_tokens, "temperature": settings.llm_temperature}
    # seed is only applied for Ollama (Anthropic doesn't support it)
    if settings.llm_seed is not None and get_active_provider() != "anthropic":
        out["seed"] = settings.llm_seed
    return out
