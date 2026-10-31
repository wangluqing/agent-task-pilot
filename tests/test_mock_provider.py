"""Offline contract tests for the deterministic MockProvider."""

import ast
import inspect
import socket

import pytest

from agent_task_pilot.domain import AgentReport, ApplicabilityVerdict, RiskCategory
from agent_task_pilot.providers import DiagnosisProvider, MockProvider
from agent_task_pilot.providers.mock import MOCK_NOTICE, MockScenario


@pytest.mark.parametrize(
    ("requirement", "expected_scenario"),
    [
        ("请对客服工单进行分类并分流", MockScenario.CUSTOMER_TICKET),
        ("建立企业知识库问答助手", MockScenario.KNOWLEDGE_QA),
        ("按固定格式汇总月度报表", MockScenario.FIXED_REPORT),
    ],
)
def test_known_scenarios_generate_complete_valid_reports(
    requirement: str, expected_scenario: MockScenario
) -> None:
    provider = MockProvider()

    report = provider.diagnose(requirement)

    assert isinstance(report, AgentReport)
    assert expected_scenario.value in report.requirement_summary
    assert report.applicability.reasons
    assert report.applicability.prerequisites
    assert report.workflow
    assert all(step.suggested_tools for step in report.workflow)
    assert all(step.human_review is not None for step in report.workflow)
    assert report.risks
    assert report.acceptance_metrics
    assert report.assumptions
    assert report.open_questions
    assert AgentReport.model_validate(report.model_dump()) == report


def test_unknown_scenario_is_conditional_and_explicitly_generic() -> None:
    report = MockProvider().diagnose("安排园区会议室绿植养护")

    assert MockScenario.GENERIC.value in report.requirement_summary
    assert report.applicability.verdict is ApplicabilityVerdict.CONDITIONALLY_SUITABLE
    assert any("人工适用性评估" in item for item in report.applicability.prerequisites)
    assert any("真实语义分析" in item for item in report.assumptions)


def test_same_input_produces_identical_report() -> None:
    provider = MockProvider()
    requirement = "建立企业知识库问答助手"

    first = provider.diagnose(requirement)
    second = provider.diagnose(requirement)

    assert first == second
    assert first.model_dump_json() == second.model_dump_json()


def test_calls_do_not_share_mutable_report_state() -> None:
    provider = MockProvider()
    first = provider.diagnose("请对客服工单分类")
    second = provider.diagnose("请对客服工单分类")

    first.assumptions.append("仅修改第一个结果")
    first.workflow[0].inputs.append("仅修改第一个结果")

    assert "仅修改第一个结果" not in second.assumptions
    assert "仅修改第一个结果" not in second.workflow[0].inputs


def test_mock_provider_satisfies_protocol() -> None:
    provider = MockProvider()

    assert isinstance(provider, DiagnosisProvider)
    assert isinstance(provider.diagnose("固定格式报表汇总"), AgentReport)


def test_provider_does_not_read_api_key_or_use_network(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_network(*args: object, **kwargs: object) -> None:
        raise AssertionError("MockProvider must not access the network")

    monkeypatch.setenv("DEEPSEEK_API_KEY", "must-not-be-read")
    monkeypatch.setattr(socket, "create_connection", fail_network)
    monkeypatch.setattr(socket.socket, "connect", fail_network)

    report = MockProvider().diagnose("建立企业知识库问答助手")

    assert isinstance(report, AgentReport)
    source = inspect.getsource(inspect.getmodule(MockProvider))
    tree = ast.parse(source)
    imported_roots = {
        node.module.split(".", maxsplit=1)[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module
    }
    assert not any(isinstance(node, ast.Import) for node in ast.walk(tree))
    assert imported_roots <= {"enum", "agent_task_pilot"}
    assert "DEEPSEEK_API_KEY" not in source


def test_conflicting_scenarios_use_documented_priority() -> None:
    provider = MockProvider()

    customer_first = provider.diagnose("客服知识库问答和报表汇总")
    knowledge_before_report = provider.diagnose("知识库问答与报表汇总")

    assert MockScenario.CUSTOMER_TICKET.value in customer_first.requirement_summary
    assert MockScenario.KNOWLEDGE_QA.value in knowledge_before_report.requirement_summary


@pytest.mark.parametrize(
    "requirement",
    [
        "请对客服工单进行分类",
        "建立企业知识库问答助手",
        "按固定格式汇总报表",
        "安排园区绿植养护",
    ],
)
def test_every_report_has_prominent_mock_notice(requirement: str) -> None:
    report = MockProvider().diagnose(requirement)

    assert MOCK_NOTICE in report.title
    assert MOCK_NOTICE in report.assumptions


@pytest.mark.parametrize(
    "requirement",
    [
        "请对客服工单进行分类",
        "建立企业知识库问答助手",
        "按固定格式汇总报表",
        "安排园区绿植养护",
    ],
)
def test_every_report_contains_required_risk_categories(requirement: str) -> None:
    report = MockProvider().diagnose(requirement)

    assert {risk.category for risk in report.risks} >= {
        RiskCategory.PRIVACY,
        RiskCategory.PERMISSION,
        RiskCategory.ERRONEOUS_OUTPUT,
    }


@pytest.mark.parametrize(
    "requirement",
    [
        "问答助手",
        "中文，问答助手！！！",
        "建立企业知识库问答助手",
        "按固定格式汇总报表需求",
        "未知需求未知需求未知文本",
    ],
)
def test_requirement_summary_is_semantic_and_does_not_copy_input(requirement: str) -> None:
    report = MockProvider().diagnose(requirement)

    assert report.requirement_summary != requirement
    assert requirement not in report.requirement_summary
    assert "业务摘要" in report.requirement_summary


def test_long_requirement_summary_is_semantic_and_not_truncated() -> None:
    requirement = "这是一个未识别的复杂业务需求。" * 100

    report = MockProvider().diagnose(requirement)

    assert requirement not in report.requirement_summary
    assert "需求未命中内置演示场景" in report.requirement_summary
    assert "…" not in report.requirement_summary
