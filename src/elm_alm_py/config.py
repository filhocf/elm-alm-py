"""Configuration for ELM connection."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    elm_url: str = "https://www-elm.prevnet"
    elm_user: str = ""
    elm_password: str = ""

    model_config = {"env_prefix": "ELM_", "env_file": ".env"}


settings = Settings()
