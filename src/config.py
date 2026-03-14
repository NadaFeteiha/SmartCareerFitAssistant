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

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
