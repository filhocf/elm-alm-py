"""Configuration for ELM connection."""

import base64
import json
import os

from pydantic_settings import BaseSettings


def _load_creds_file() -> dict:
    """Load credentials from ~/.elm_creds.json if it exists."""
    path = os.path.expanduser("~/.elm_creds.json")
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return {}


def _decode_password(value: str) -> str:
    """Decode password — supports plaintext or base64-encoded."""
    if not value:
        return value
    try:
        decoded = base64.b64decode(value, validate=True).decode()
        # Heuristic: if decoded is printable ASCII, it was base64
        if decoded.isprintable():
            return decoded
    except Exception:
        pass
    return value


class Settings(BaseSettings):
    elm_url: str = ""
    elm_user: str = ""
    elm_password: str = ""

    model_config = {"env_prefix": "", "env_file": ".env"}

    def model_post_init(self, __context) -> None:
        # Load from ~/.elm_creds.json as fallback
        if not self.elm_user:
            creds = _load_creds_file()
            if creds:
                object.__setattr__(self, "elm_user", creds.get("username", ""))
                object.__setattr__(self, "elm_password", _decode_password(creds.get("password", "")))
                if not self.elm_url:
                    url = creds.get("url")
                    if url:
                        object.__setattr__(self, "elm_url", url)
        else:
            # Decode password from env var (may be base64)
            object.__setattr__(self, "elm_password", _decode_password(self.elm_password))


settings = Settings()
