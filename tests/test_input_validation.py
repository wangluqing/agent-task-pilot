"""Tests for framework-independent analysis input validation."""

import pytest

from agent_task_pilot.services import (
    AnalysisMode,
    InputValidationError,
    validate_analysis_input,
)
from agent_task_pilot.services.input_validation import (
    EMPTY_REQUIREMENT_MESSAGE,
    INVALID_MODE_MESSAGE,
    INVALID_REQUIREMENT_TYPE_MESSAGE,
    REQUIREMENT_TOO_LONG_MESSAGE,
)


@pytest.mark.parametrize(
    "requirement",
    [
        "",
        " ",
        "\t",
        "\n",
        " \t\r\n ",
        "\u00a0",  # no-break space
        "\u2003",  # em space
        "\u3000",  # ideographic space
        "\u2028\u2029",  # Unicode line and paragraph separators
    ],
)
def test_empty_and_unicode_whitespace_requirements_are_rejected(requirement: str) -> None:
    with pytest.raises(InputValidationError, match=f"^{EMPTY_REQUIREMENT_MESSAGE}$"):
        validate_analysis_input(requirement)


@pytest.mark.parametrize("length", [1, 1999, 2000])
def test_valid_requirement_length_boundaries_are_accepted(length: int) -> None:
    requirement = "需" * length

    result = validate_analysis_input(requirement)

    assert result.raw_requirement == requirement
    assert result.validated_requirement == requirement
    assert len(result.validated_requirement) == length


def test_requirement_over_maximum_length_is_rejected_without_truncation() -> None:
    requirement = "需" * 2001

    with pytest.raises(InputValidationError, match=f"^{REQUIREMENT_TOO_LONG_MESSAGE}$"):
        validate_analysis_input(requirement)

    assert len(requirement) == 2001


def test_length_is_measured_after_trimming_outer_whitespace() -> None:
    requirement = f"  {'A' * 2000}\n"

    result = validate_analysis_input(requirement)

    assert result.raw_requirement == requirement
    assert len(result.validated_requirement) == 2000


def test_default_mode_is_mock() -> None:
    result = validate_analysis_input("分析客服工单")

    assert result.mode is AnalysisMode.MOCK


@pytest.mark.parametrize(
    ("mode", "expected"),
    [("mock", AnalysisMode.MOCK), ("deepseek", AnalysisMode.DEEPSEEK)],
)
def test_explicit_valid_modes_are_accepted(mode: str, expected: AnalysisMode) -> None:
    result = validate_analysis_input("分析客服工单", mode=mode)

    assert result.mode is expected


@pytest.mark.parametrize("mode", ["other", "Mock", "DEEPSEEK", " deepseek ", ""])
def test_invalid_or_wrong_case_modes_are_rejected(mode: str) -> None:
    with pytest.raises(InputValidationError, match=f"^{INVALID_MODE_MESSAGE}$"):
        validate_analysis_input("分析客服工单", mode=mode)


@pytest.mark.parametrize("mode", [None, 1, True, ["mock"]])
def test_non_string_modes_are_rejected(mode: object) -> None:
    with pytest.raises(InputValidationError, match=f"^{INVALID_MODE_MESSAGE}$"):
        validate_analysis_input("分析客服工单", mode=mode)


@pytest.mark.parametrize("requirement", [None, 1, 1.5, True, ["需求"], {"需求": "分类"}])
def test_non_string_requirements_are_rejected(requirement: object) -> None:
    with pytest.raises(InputValidationError, match=f"^{INVALID_REQUIREMENT_TYPE_MESSAGE}$"):
        validate_analysis_input(requirement)


@pytest.mark.parametrize(
    "requirement",
    [
        "自动分类客服工单",
        "Classify customer support tickets",
        "2026",
        "将 ticket 123 分类到售后队列",
    ],
)
def test_chinese_english_numeric_and_mixed_text_are_accepted(requirement: str) -> None:
    result = validate_analysis_input(requirement)

    assert result.validated_requirement == requirement


def test_raw_and_validated_requirements_are_distinct_and_unambiguous() -> None:
    requirement = " \t分析客服工单\n "

    result = validate_analysis_input(requirement)

    assert result.raw_requirement == requirement
    assert result.validated_requirement == "分析客服工单"
    assert result.raw_requirement != result.validated_requirement


@pytest.mark.parametrize(
    ("requirement", "mode", "expected_message"),
    [
        (None, "mock", INVALID_REQUIREMENT_TYPE_MESSAGE),
        ("\u3000", "mock", EMPTY_REQUIREMENT_MESSAGE),
        ("A" * 2001, "mock", REQUIREMENT_TOO_LONG_MESSAGE),
        ("合法需求", "invalid", INVALID_MODE_MESSAGE),
    ],
)
def test_errors_expose_only_stable_safe_messages(
    requirement: object,
    mode: object,
    expected_message: str,
) -> None:
    with pytest.raises(InputValidationError) as caught:
        validate_analysis_input(requirement, mode=mode)

    message = str(caught.value)
    assert message == expected_message
    assert "pydantic" not in message.lower()
    assert "traceback" not in message.lower()
    assert repr(requirement) not in message
