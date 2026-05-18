"""Configuration for ELM connection."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    elm_url: str = "https://alm.dataprev.gov.br"
    elm_user: str = ""
    elm_password: str = ""

    model_config = {"env_prefix": "", "env_file": ".env"}


settings = Settings()
