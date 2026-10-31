"""Contract tests for Agent diagnostic report domain models."""

import pytest
from pydantic import ValidationError

from agent_task_pilot.domain import AgentReport, ApplicabilityVerdict, RiskCategory


def test_minimal_report_is_valid(minimal_report_data: dict[str, object]) -> None:
    report = AgentReport.model_validate(minimal_report_data)

    assert report.applicability.verdict is ApplicabilityVerdict.SUITABLE
    assert len(report.workflow) == 1
    assert {risk.category for risk in report.risks} >= {
        RiskCategory.PRIVACY,
        RiskCategory.PERMISSION,
        RiskCategory.ERRONEOUS_OUTPUT,
    }


def test_full_report_is_valid(full_report_data: dict[str, object]) -> None:
    report = AgentReport.model_validate(full_report_data)

    assert report.applicability.verdict is ApplicabilityVerdict.CONDITIONALLY_SUITABLE
    assert len(report.workflow) == 2
    assert report.workflow[0].human_review.required is True
    assert report.risks[-1].category is RiskCategory.OTHER


@pytest.mark.parametrize("verdict", ["部分适合", "", "SUITABLE"])
def test_invalid_applicability_verdict_is_rejected(
    minimal_report_data: dict[str, object], verdict: str
) -> None:
    minimal_report_data["applicability"]["verdict"] = verdict

    with pytest.raises(ValidationError):
        AgentReport.model_validate(minimal_report_data)


@pytest.mark.parametrize("reason", ["", " ", "\t\n"])
def test_blank_reason_is_rejected(minimal_report_data: dict[str, object], reason: str) -> None:
    minimal_report_data["applicability"]["reasons"] = [reason]

    with pytest.raises(ValidationError):
        AgentReport.model_validate(minimal_report_data)


def test_conditional_suitability_requires_prerequisite(
    minimal_report_data: dict[str, object],
) -> None:
    minimal_report_data["applicability"] = {
        "verdict": "有条件适合",
        "reasons": ["需要满足业务前提。"],
        "prerequisites": [],
    }

    with pytest.raises(ValidationError, match="prerequisites"):
        AgentReport.model_validate(minimal_report_data)


@pytest.mark.parametrize("missing_category", ["隐私", "权限", "错误输出"])
def test_each_required_risk_category_is_enforced(
    minimal_report_data: dict[str, object], missing_category: str
) -> None:
    minimal_report_data["risks"] = [
        risk for risk in minimal_report_data["risks"] if risk["category"] != missing_category
    ]

    with pytest.raises(ValidationError):
        AgentReport.model_validate(minimal_report_data)


@pytest.mark.parametrize("steps", [[2], [1, 3], [1, 1]])
def test_workflow_steps_must_be_consecutive(
    full_report_data: dict[str, object], steps: list[int]
) -> None:
    workflow = full_report_data["workflow"]
    assert isinstance(workflow, list)
    if len(steps) == 1:
        full_report_data["workflow"] = [workflow[0]]
        workflow = full_report_data["workflow"]
    for item, step in zip(workflow, steps, strict=True):
        item["step"] = step

    with pytest.raises(ValidationError, match="连续递增"):
        AgentReport.model_validate(full_report_data)


@pytest.mark.parametrize("missing_field", ["checkpoint", "reviewer", "pass_criteria"])
def test_required_human_review_needs_all_details(
    minimal_report_data: dict[str, object], missing_field: str
) -> None:
    human_review = {
        "required": True,
        "checkpoint": "发布之前",
        "reviewer": "业务负责人",
        "pass_criteria": "内容准确且无敏感数据",
    }
    del human_review[missing_field]
    minimal_report_data["workflow"][0]["human_review"] = human_review

    with pytest.raises(ValidationError, match="人工审核"):
        AgentReport.model_validate(minimal_report_data)


def test_acceptance_metric_requires_measurement(
    minimal_report_data: dict[str, object],
) -> None:
    del minimal_report_data["acceptance_metrics"][0]["measurement"]

    with pytest.raises(ValidationError):
        AgentReport.model_validate(minimal_report_data)


@pytest.mark.parametrize("target", ["", "  ", "准确率不低于 90%"])
def test_acceptance_metric_requires_suggested_checkable_target(
    minimal_report_data: dict[str, object], target: str
) -> None:
    minimal_report_data["acceptance_metrics"][0]["target"] = target

    with pytest.raises(ValidationError):
        AgentReport.model_validate(minimal_report_data)


@pytest.mark.parametrize(
    ("path", "field"),
    [
        ((), "unexpected"),
        (("applicability",), "confidence"),
        (("workflow", 0, "human_review"), "notes"),
    ],
)
def test_unknown_fields_are_rejected(
    minimal_report_data: dict[str, object], path: tuple[object, ...], field: str
) -> None:
    target: object = minimal_report_data
    for part in path:
        target = target[part]
    target[field] = "不允许的字段"

    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        AgentReport.model_validate(minimal_report_data)


@pytest.mark.parametrize(
    ("path", "field"),
    [
        ((), "title"),
        ((), "requirement_summary"),
        (("workflow", 0), "name"),
        (("workflow", 0, "suggested_tools", 0), "purpose"),
        (("risks", 0), "mitigation"),
        (("acceptance_metrics", 0), "definition"),
    ],
)
def test_required_text_cannot_be_blank(
    minimal_report_data: dict[str, object], path: tuple[object, ...], field: str
) -> None:
    target: object = minimal_report_data
    for part in path:
        target = target[part]
    target[field] = " \t\n "

    with pytest.raises(ValidationError):
        AgentReport.model_validate(minimal_report_data)


def test_json_round_trip_preserves_report(full_report_data: dict[str, object]) -> None:
    report = AgentReport.model_validate(full_report_data)

    restored = AgentReport.model_validate_json(report.model_dump_json())

    assert restored == report
    assert restored.model_dump(mode="json") == report.model_dump(mode="json")
