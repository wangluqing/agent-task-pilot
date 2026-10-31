"""Tests for safe, lazy DeepSeek environment configuration."""

import importlib
import logging

import pytest
from pydantic import SecretStr, ValidationError

from agent_task_pilot.config import (
    DEEPSEEK_MAX_RETRIES,
    DEEPSEEK_TIMEOUT_SECONDS,
    DEFAULT_DEEPSEEK_BASE_URL,
    DEFAULT_DEEPSEEK_MODEL,
    DeepSeekConfig,
    load_deepseek_config,
)
from agent_task_pilot.providers import ConfigurationMissingError, ErrorCode, MockProvider

FAKE_API_KEY = "test-only-deepseek-key-123456"


@pytest.mark.parametrize("value", [None, "", " ", "\t\n"])
def test_missing_or_blank_api_key_maps_to_config_missing(value: str | None) -> None:
    environment = {} if value is None else {"DEEPSEEK_API_KEY": value}

    with pytest.raises(ConfigurationMissingError) as caught:
        load_deepseek_config(environment)

    assert caught.value.code is ErrorCode.CONFIG_MISSING
    assert FAKE_API_KEY not in str(caught.value)


def test_defaults_match_verified_official_configuration() -> None:
    config = load_deepseek_config({"DEEPSEEK_API_KEY": FAKE_API_KEY})

    assert config.model == DEFAULT_DEEPSEEK_MODEL == "deepseek-flash"
    assert config.base_url == DEFAULT_DEEPSEEK_BASE_URL == "https://api.deepseek.com"
    assert config.timeout_seconds == DEEPSEEK_TIMEOUT_SECONDS == 60
    assert config.max_retries == DEEPSEEK_MAX_RETRIES == 0


def test_model_and_official_https_base_url_are_configurable() -> None:
    config = load_deepseek_config(
        {
            "DEEPSEEK_API_KEY": FAKE_API_KEY,
            "DEEPSEEK_MODEL": "deepseek-custom-test",
            "DEEPSEEK_BASE_URL": "https://api.deepseek.com/v1/",
        }
    )

    assert config.model == "deepseek-custom-test"
    assert config.base_url == "https://api.deepseek.com/v1"


@pytest.mark.parametrize(
    "base_url",
    [
        "",
        "http://api.deepseek.com",
        "api.deepseek.com",
        "https://user:password@api.deepseek.com",
        "https://api.deepseek.com?api_key=unsafe",
        "https://api.deepseek.com#fragment",
        "https://gateway.example.test/deepseek",
        "https://api.deepseek.com.evil.example",
        "https://api.deepseek.com/other",
        "https://api.deepseek.com:444",
    ],
)
def test_invalid_or_unsafe_base_url_fails_safely(base_url: str) -> None:
    with pytest.raises(ConfigurationMissingError) as caught:
        load_deepseek_config(
            {
                "DEEPSEEK_API_KEY": FAKE_API_KEY,
                "DEEPSEEK_BASE_URL": base_url,
            }
        )

    assert caught.value.code is ErrorCode.CONFIG_MISSING
    assert FAKE_API_KEY not in str(caught.value)
    if base_url:
        assert base_url not in str(caught.value)


def test_empty_model_fails_safely() -> None:
    with pytest.raises(ConfigurationMissingError) as caught:
        load_deepseek_config({"DEEPSEEK_API_KEY": FAKE_API_KEY, "DEEPSEEK_MODEL": "  "})

    assert caught.value.code is ErrorCode.CONFIG_MISSING
    assert FAKE_API_KEY not in str(caught.value)


def test_secret_is_masked_from_display_serialization_errors_and_logs(
    caplog: pytest.LogCaptureFixture,
) -> None:
    config = load_deepseek_config({"DEEPSEEK_API_KEY": FAKE_API_KEY})

    with caplog.at_level(logging.DEBUG):
        logging.getLogger("agent_task_pilot.config.test").debug("config=%r", config)

    visible_outputs = (
        repr(config),
        str(config),
        config.model_dump_json(),
        caplog.text,
    )
    assert all(FAKE_API_KEY not in output for output in visible_outputs)
    assert config.api_key.get_secret_value() == FAKE_API_KEY


def test_direct_config_repr_omits_secret_field() -> None:
    config = DeepSeekConfig(api_key=SecretStr(FAKE_API_KEY))

    assert "api_key" not in repr(config)
    assert FAKE_API_KEY not in repr(config)


@pytest.mark.parametrize(
    "override",
    [{"timeout_seconds": 61}, {"max_retries": 1}],
)
def test_timeout_and_retry_policy_cannot_be_overridden(
    override: dict[str, int],
) -> None:
    with pytest.raises(ValidationError):
        DeepSeekConfig(api_key=SecretStr(FAKE_API_KEY), **override)


def test_import_has_no_environment_read_side_effect(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    config_module = importlib.import_module("agent_task_pilot.config")
    importlib.reload(config_module)
    monkeypatch.setenv("DEEPSEEK_API_KEY", FAKE_API_KEY)

    config = config_module.load_deepseek_config()

    assert config.api_key.get_secret_value() == FAKE_API_KEY


def test_mock_provider_remains_independent_of_deepseek_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)

    report = MockProvider().diagnose("请对客服工单进行分类")

    assert report.workflow
    assert FAKE_API_KEY not in report.model_dump_json()
