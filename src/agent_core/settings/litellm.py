from pydantic_settings import BaseSettings, SettingsConfigDict


class LiteLLMSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="LITELLM_")

    api_key: str | None = None
    api_base: str | None = None
    api_version: str | None = None
    chat_model: str | None = None
    embedding_model: str | None = None
