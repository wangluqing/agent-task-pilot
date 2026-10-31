"""Contract and safe-error tests for diagnostic providers."""

from collections.abc import Callable

import pytest

from agent_task_pilot.domain import AgentReport
from agent_task_pilot.providers import (
    AuthenticationError,
    ConfigurationMissingError,
    DiagnosisProvider,
    ErrorCode,
    NetworkError,
    ParseError,
    ProviderError,
    RateLimitedError,
    ReportValidationError,
    ServiceError,
    TimeoutError,
    UnknownProviderError,
    map_provider_exception,
)
from agent_task_pilot.providers.errors import ERROR_MESSAGES


class FakeProvider:
    """Small in-memory provider proving structural protocol compatibility."""

    def __init__(self, report: AgentReport) -> None:
        self.report = report
        self.received_requirement: str | None = None

    def diagnose(self, validated_requirement: str) -> AgentReport:
        self.received_requirement = validated_requirement
        return self.report


def invoke_provider(provider: DiagnosisProvider, validated_requirement: str) -> AgentReport:
    """Represent an upper layer that depends only on the provider protocol."""
    return provider.diagnose(validated_requirement)


def test_fake_provider_satisfies_protocol_and_returns_valid_report(
    minimal_report_data: dict[str, object],
) -> None:
    expected_report = AgentReport.model_validate(minimal_report_data)
    provider = FakeProvider(expected_report)

    report = invoke_provider(provider, "对客服工单进行分类")

    assert isinstance(provider, DiagnosisProvider)
    assert provider.received_requirement == "对客服工单进行分类"
    assert report is expected_report
    assert AgentReport.model_validate(report.model_dump()) == report


@pytest.mark.parametrize(
    ("error_factory", "code"),
    [
        (ConfigurationMissingError, ErrorCode.CONFIG_MISSING),
        (AuthenticationError, ErrorCode.AUTH_FAILED),
        (RateLimitedError, ErrorCode.RATE_LIMITED),
        (TimeoutError, ErrorCode.TIMEOUT),
        (NetworkError, ErrorCode.NETWORK_ERROR),
        (ServiceError, ErrorCode.SERVICE_ERROR),
        (ParseError, ErrorCode.PARSE_ERROR),
        (ReportValidationError, ErrorCode.REPORT_VALIDATION_ERROR),
        (UnknownProviderError, ErrorCode.UNKNOWN_ERROR),
    ],
)
def test_each_provider_error_has_stable_code_and_safe_chinese_message(
    error_factory: Callable[[], ProviderError], code: ErrorCode
) -> None:
    error = error_factory()

    assert error.code is code
    assert error.user_message == ERROR_MESSAGES[code]
    assert str(error) == ERROR_MESSAGES[code]
    assert error.user_message
    assert any("\u4e00" <= character <= "\u9fff" for character in error.user_message)


def test_known_provider_error_is_preserved_by_mapping() -> None:
    original = TimeoutError()

    mapped = map_provider_exception(original)

    assert mapped is original


@pytest.mark.parametrize(
    "unknown_error",
    [
        RuntimeError("Authorization: Bearer secret-api-key"),
        ValueError("完整业务需求：收集客户身份证号"),
        Exception('{"raw_response":"private customer data"}'),
    ],
)
def test_unknown_exception_maps_to_safe_error_without_sensitive_details(
    unknown_error: Exception,
) -> None:
    mapped = map_provider_exception(unknown_error)

    assert type(mapped) is UnknownProviderError
    assert mapped.code is ErrorCode.UNKNOWN_ERROR
    assert str(mapped) == ERROR_MESSAGES[ErrorCode.UNKNOWN_ERROR]
    assert str(unknown_error) not in str(mapped)
    assert mapped.__cause__ is None
    assert mapped.__context__ is None


def test_user_visible_errors_cannot_accept_untrusted_messages() -> None:
    with pytest.raises(TypeError):
        AuthenticationError("Authorization: Bearer secret-api-key")


def test_unknown_error_is_a_failure_not_a_report() -> None:
    mapped = map_provider_exception(RuntimeError("unexpected defect"))

    assert isinstance(mapped, ProviderError)
    assert not isinstance(mapped, AgentReport)


def test_error_code_values_are_complete_and_stable() -> None:
    assert {code.value for code in ErrorCode} == {
        "CONFIG_MISSING",
        "AUTH_FAILED",
        "RATE_LIMITED",
        "TIMEOUT",
        "NETWORK_ERROR",
        "SERVICE_ERROR",
        "PARSE_ERROR",
        "REPORT_VALIDATION_ERROR",
        "UNKNOWN_ERROR",
    }
