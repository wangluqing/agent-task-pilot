"""Tests for the framework-independent DiagnosisService pipeline."""

from copy import deepcopy

import pytest

from agent_task_pilot.domain import AgentReport
from agent_task_pilot.providers import (
    AuthenticationError,
    ConfigurationMissingError,
    DeepSeekProvider,
    ErrorCode,
    ReportValidationError,
    UnknownProviderError,
)
from agent_task_pilot.providers.mock import MOCK_NOTICE
from agent_task_pilot.services import (
    AnalysisMode,
    DiagnosisResult,
    DiagnosisService,
    InputValidationError,
)


class SpyProvider:
    """Return a configured value while recording calls."""

    def __init__(self, value: object) -> None:
        self.value = value
        self.calls: list[str] = []

    def diagnose(self, validated_requirement: str) -> object:
        self.calls.append(validated_requirement)
        return self.value


class RaisingProvider:
    """Raise a configured exception while recording calls."""

    def __init__(self, error: Exception) -> None:
        self.error = error
        self.calls = 0

    def diagnose(self, validated_requirement: str) -> AgentReport:
        self.calls += 1
        raise self.error


class StaticRenderer:
    """Render a fixed string and record the validated report."""

    def __init__(self, markdown: object = "# rendered\n") -> None:
        self.markdown = markdown
        self.reports: list[AgentReport] = []

    def render(self, report: AgentReport) -> object:
        self.reports.append(report)
        return self.markdown


class RaisingRenderer:
    """Always fail before a result object can be created."""

    def __init__(self, error: Exception) -> None:
        self.error = error
        self.calls = 0

    def render(self, report: AgentReport) -> str:
        self.calls += 1
        raise self.error


def _service_with_mock_provider(provider: object, renderer: object) -> DiagnosisService:
    return DiagnosisService(
        providers={AnalysisMode.MOCK: provider},
        renderer=renderer,
    )


def test_default_mock_pipeline_returns_complete_result() -> None:
    result = DiagnosisService().analyze("请对客服工单进行分类并分派")

    assert isinstance(result, DiagnosisResult)
    assert isinstance(result.report, AgentReport)
    assert result.report.applicability.verdict.value == "有条件适合"
    assert "## 1. 需求摘要" in result.markdown
    assert "## 8. 使用限制" in result.markdown


def test_valid_chinese_requirement_generates_report_and_markdown() -> None:
    result = DiagnosisService().analyze("建立企业知识库问答助手", mode="mock")

    assert "企业知识库问答" in result.report.requirement_summary
    assert "企业知识库问答" in result.markdown


@pytest.mark.parametrize("invalid_requirement", ["", " \t\n ", None, "需" * 2001])
def test_invalid_input_is_rejected_before_provider_call(invalid_requirement: object) -> None:
    provider = SpyProvider(None)
    service = _service_with_mock_provider(provider, StaticRenderer())

    with pytest.raises(InputValidationError):
        service.analyze(invalid_requirement)

    assert provider.calls == []


def test_unconfigured_deepseek_fails_without_mock_fallback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    mock_provider = SpyProvider(None)
    service = _service_with_mock_provider(mock_provider, StaticRenderer())

    with pytest.raises(ConfigurationMissingError) as caught:
        service.analyze("分析客服工单", mode="deepseek")

    assert caught.value.code is ErrorCode.CONFIG_MISSING
    assert mock_provider.calls == []


def test_default_service_registers_deepseek_provider_and_renders_result(
    minimal_report_data: dict[str, object],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    report = AgentReport.model_validate(minimal_report_data)
    calls: list[str] = []

    def fake_diagnose(self: DeepSeekProvider, validated_requirement: str) -> AgentReport:
        del self
        calls.append(validated_requirement)
        return report

    monkeypatch.setattr(DeepSeekProvider, "diagnose", fake_diagnose)

    result = DiagnosisService().analyze("  分析客服工单  ", mode="deepseek")

    assert calls == ["分析客服工单"]
    assert result.report == report
    assert "客服工单分流 Agent 诊断报告" in result.markdown


def test_known_provider_error_is_preserved(
    minimal_report_data: dict[str, object],
) -> None:
    error = AuthenticationError()
    provider = RaisingProvider(error)
    service = _service_with_mock_provider(provider, StaticRenderer())

    with pytest.raises(AuthenticationError) as caught:
        service.analyze("分析客服工单")

    assert caught.value is error
    assert caught.value.code is ErrorCode.AUTH_FAILED
    assert provider.calls == 1


def test_unknown_provider_error_is_safely_mapped() -> None:
    secret = "Authorization: Bearer private-secret"
    provider = RaisingProvider(RuntimeError(secret))
    service = _service_with_mock_provider(provider, StaticRenderer())

    with pytest.raises(UnknownProviderError) as caught:
        service.analyze("分析客服工单")

    assert caught.value.code is ErrorCode.UNKNOWN_ERROR
    assert secret not in str(caught.value)
    assert caught.value.__suppress_context__ is True


@pytest.mark.parametrize(
    "invalid_output",
    [{"title": "not a model"}, None, "error", 42, RuntimeError("returned error object")],
)
def test_non_report_provider_outputs_fail_validation(invalid_output: object) -> None:
    renderer = StaticRenderer()
    service = _service_with_mock_provider(SpyProvider(invalid_output), renderer)

    with pytest.raises(ReportValidationError) as caught:
        service.analyze("分析客服工单")

    assert caught.value.code is ErrorCode.REPORT_VALIDATION_ERROR
    assert renderer.reports == []


def test_constructed_invalid_report_is_revalidated_and_rejected() -> None:
    invalid_report = AgentReport.model_construct(title="绕过校验")
    renderer = StaticRenderer()
    service = _service_with_mock_provider(SpyProvider(invalid_report), renderer)

    with pytest.raises(ReportValidationError):
        service.analyze("分析客服工单")

    assert renderer.reports == []


def test_mutated_invalid_report_is_revalidated_and_rejected(
    minimal_report_data: dict[str, object],
) -> None:
    report = AgentReport.model_validate(minimal_report_data)
    report.workflow[0].step = 2
    renderer = StaticRenderer()
    service = _service_with_mock_provider(SpyProvider(report), renderer)

    with pytest.raises(ReportValidationError):
        service.analyze("分析客服工单")

    assert renderer.reports == []


def test_renderer_failure_never_returns_partial_success(
    minimal_report_data: dict[str, object],
) -> None:
    report = AgentReport.model_validate(minimal_report_data)
    secret = "API_KEY=private-secret"
    renderer = RaisingRenderer(RuntimeError(secret))
    service = _service_with_mock_provider(SpyProvider(report), renderer)

    with pytest.raises(UnknownProviderError) as caught:
        service.analyze("分析客服工单")

    assert caught.value.code is ErrorCode.UNKNOWN_ERROR
    assert secret not in str(caught.value)
    assert renderer.calls == 1


def test_non_string_renderer_output_is_rejected(
    minimal_report_data: dict[str, object],
) -> None:
    report = AgentReport.model_validate(minimal_report_data)
    service = _service_with_mock_provider(SpyProvider(report), StaticRenderer(None))

    with pytest.raises(UnknownProviderError):
        service.analyze("分析客服工单")


@pytest.mark.parametrize("empty_markdown", ["", " \t\n "])
def test_empty_renderer_output_is_rejected(
    minimal_report_data: dict[str, object], empty_markdown: str
) -> None:
    report = AgentReport.model_validate(minimal_report_data)
    service = _service_with_mock_provider(SpyProvider(report), StaticRenderer(empty_markdown))

    with pytest.raises(UnknownProviderError):
        service.analyze("分析客服工单")


def test_requests_do_not_share_previous_success_state() -> None:
    service = DiagnosisService()
    first = service.analyze("请对客服工单进行分类")
    second = service.analyze("建立企业知识库问答助手")

    first.report.assumptions.append("只修改第一次结果")

    assert first is not second
    assert first.report is not second.report
    assert first.markdown != second.markdown
    assert "只修改第一次结果" not in second.report.assumptions
    assert "客服工单分类" in first.report.requirement_summary
    assert "企业知识库问答" in second.report.requirement_summary


def test_mock_notice_and_suggested_metrics_remain_in_markdown() -> None:
    result = DiagnosisService().analyze("请对客服工单进行分类")

    assert MOCK_NOTICE in result.markdown
    assert "【Mock 演示结果】" in result.markdown
    assert "**建议目标：** 建议值" in result.markdown


def test_success_revalidates_report_before_rendering(
    minimal_report_data: dict[str, object],
) -> None:
    source_report = AgentReport.model_validate(deepcopy(minimal_report_data))
    renderer = StaticRenderer()
    service = _service_with_mock_provider(SpyProvider(source_report), renderer)

    result = service.analyze("  分析客服工单  ")

    assert result.report == source_report
    assert result.report is not source_report
    assert renderer.reports == [result.report]


def test_provider_receives_only_validated_requirement(
    minimal_report_data: dict[str, object],
) -> None:
    report = AgentReport.model_validate(minimal_report_data)
    provider = SpyProvider(report)
    service = _service_with_mock_provider(provider, StaticRenderer())

    service.analyze(" \t分析客服工单\n ")

    assert provider.calls == ["分析客服工单"]
