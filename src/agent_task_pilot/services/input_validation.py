"""Framework-independent validation for analysis request input."""

from enum import StrEnum

from pydantic import BaseModel, ConfigDict

MAX_REQUIREMENT_LENGTH = 2000

EMPTY_REQUIREMENT_MESSAGE = "请输入业务需求，内容不能仅包含空白字符。"
INVALID_REQUIREMENT_TYPE_MESSAGE = "业务需求必须是文本。"
REQUIREMENT_TOO_LONG_MESSAGE = "业务需求不能超过 2000 个字符，请精简后重试。"
INVALID_MODE_MESSAGE = "分析模式无效，仅支持 mock 或 deepseek。"


class AnalysisMode(StrEnum):
    """Analysis providers selectable by a user request."""

    MOCK = "mock"
    DEEPSEEK = "deepseek"


class InputValidationError(ValueError):
    """Safe validation failure intended for presentation to end users."""


class ValidatedAnalysisInput(BaseModel):
    """Validated input while retaining the exact user-provided requirement."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    raw_requirement: str
    validated_requirement: str
    mode: AnalysisMode


def validate_analysis_input(
    requirement: object,
    mode: object = AnalysisMode.MOCK,
) -> ValidatedAnalysisInput:
    """Validate raw user input without mutating or silently truncating it.

    Raises:
        InputValidationError: With a stable, user-safe Chinese message.
    """
    if not isinstance(requirement, str):
        raise InputValidationError(INVALID_REQUIREMENT_TYPE_MESSAGE)

    validated_requirement = requirement.strip()
    if not validated_requirement:
        raise InputValidationError(EMPTY_REQUIREMENT_MESSAGE)
    if len(validated_requirement) > MAX_REQUIREMENT_LENGTH:
        raise InputValidationError(REQUIREMENT_TOO_LONG_MESSAGE)

    if not isinstance(mode, str):
        raise InputValidationError(INVALID_MODE_MESSAGE)
    try:
        validated_mode = AnalysisMode(mode)
    except ValueError:
        raise InputValidationError(INVALID_MODE_MESSAGE) from None

    return ValidatedAnalysisInput(
        raw_requirement=requirement,
        validated_requirement=validated_requirement,
        mode=validated_mode,
    )
