from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Central application configuration.

    LLM_PROVIDER/LLM_MODEL/LLM_API_KEY configure the Challenger's model
    backend. challenger_service.py is the ONLY place that reads these -
    no other part of the app should know which provider is in use.
    """

    APP_NAME: str = "CapitalOS"
    DATABASE_URL: str = "sqlite:///./capitalos.db"

    LLM_PROVIDER: str = "gemini"
    LLM_MODEL: str = "gemini-2.5-flash"
    LLM_API_KEY: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
