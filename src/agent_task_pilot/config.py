"""Safe, side-effect-free configuration loading for the DeepSeek provider."""

from __future__ import annotations

import os
from collections.abc import Mapping
from typing import Literal
from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict, Field, SecretStr, field_validator

from agent_task_pilot.providers import ConfigurationMissingError

DEFAULT_DEEPSEEK_MODEL = "deepseek-flash"
DEFAULT_DEEPSEEK_BASE_URL = "https://api.deepseek.com"
DEEPSEEK_TIMEOUT_SECONDS = 60
DEEPSEEK_MAX_RETRIES = 0


class DeepSeekConfig(BaseModel):
    """Validated DeepSeek settings with secret-safe display behaviour."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    api_key: SecretStr = Field(repr=False)
    model: str = DEFAULT_DEEPSEEK_MODEL
    base_url: str = DEFAULT_DEEPSEEK_BASE_URL
    timeout_seconds: Literal[60] = DEEPSEEK_TIMEOUT_SECONDS
    max_retries: Literal[0] = DEEPSEEK_MAX_RETRIES

    @field_validator("api_key")
    @classmethod
    def validate_api_key(cls, value: SecretStr) -> SecretStr:
        """Reject empty secrets without exposing their contents."""
        if not value.get_secret_value().strip():
            raise ValueError("API Key 不能为空")
        return value

    @field_validator("model")
    @classmethod
    def validate_model(cls, value: str) -> str:
        """Require a non-empty configurable model identifier."""
        normalized = value.strip()
        if not normalized:
            raise ValueError("模型标识不能为空")
        return normalized

    @field_validator("base_url")
    @classmethod
    def validate_base_url(cls, value: str) -> str:
        """Allow only credential-free HTTPS API base URLs."""
        normalized = value.strip().rstrip("/")
        parsed = urlsplit(normalized)
        if (
            parsed.scheme != "https"
            or not parsed.hostname
            or parsed.username is not None
            or parsed.password is not None
            or parsed.query
            or parsed.fragment
        ):
            raise ValueError("API 地址必须是安全的 HTTPS 地址")
        return normalized


def load_deepseek_config(
    environ: Mapping[str, str] | None = None,
) -> DeepSeekConfig:
    """Load DeepSeek settings on demand and map failures to a safe error."""
    source = os.environ if environ is None else environ
    api_key = source.get("DEEPSEEK_API_KEY", "").strip()
    if not api_key:
        raise ConfigurationMissingError() from None

    model = source.get("DEEPSEEK_MODEL", DEFAULT_DEEPSEEK_MODEL).strip()
    base_url = source.get("DEEPSEEK_BASE_URL", DEFAULT_DEEPSEEK_BASE_URL).strip()

    try:
        return DeepSeekConfig(
            api_key=SecretStr(api_key),
            model=model,
            base_url=base_url,
        )
    except (TypeError, ValueError):
        raise ConfigurationMissingError() from None
