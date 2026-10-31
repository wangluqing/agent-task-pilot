"""Validated domain contract for Agent diagnostic reports."""

from enum import StrEnum
from typing import Annotated, Self

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

NonBlankText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
NonEmptyTextList = Annotated[list[NonBlankText], Field(min_length=1)]


class DomainModel(BaseModel):
    """Strict base model shared by all report contract types."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class ApplicabilityVerdict(StrEnum):
    """Supported Agent applicability outcomes."""

    SUITABLE = "适合"
    CONDITIONALLY_SUITABLE = "有条件适合"
    UNSUITABLE = "不适合"


class RiskCategory(StrEnum):
    """Risk categories supported by the V0.1 report contract."""

    PRIVACY = "隐私"
    PERMISSION = "权限"
    ERRONEOUS_OUTPUT = "错误输出"
    OTHER = "其他"


class RiskLevel(StrEnum):
    """Likelihood and severity levels kept as separate dimensions."""

    LOW = "低"
    MEDIUM = "中"
    HIGH = "高"


class Applicability(DomainModel):
    """Agent applicability conclusion and supporting evidence."""

    verdict: ApplicabilityVerdict
    reasons: NonEmptyTextList
    prerequisites: list[NonBlankText] = Field(default_factory=list)

    @model_validator(mode="after")
    def require_conditional_prerequisites(self) -> Self:
        """Conditional suitability must state at least one prerequisite."""
        if self.verdict is ApplicabilityVerdict.CONDITIONALLY_SUITABLE and not self.prerequisites:
            raise ValueError("有条件适合时 prerequisites 至少需要一项")
        return self


class SuggestedTool(DomainModel):
    """A non-executing recommendation for a tool or capability."""

    name: NonBlankText
    purpose: NonBlankText
    required_access: NonBlankText


class HumanReview(DomainModel):
    """Human review requirement associated with one workflow step."""

    required: bool
    checkpoint: NonBlankText | None = None
    reviewer: NonBlankText | None = None
    pass_criteria: NonBlankText | None = None

    @model_validator(mode="after")
    def require_review_details(self) -> Self:
        """Required reviews must fully describe the checkpoint and owner."""
        if self.required and not all((self.checkpoint, self.reviewer, self.pass_criteria)):
            raise ValueError("需要人工审核时 checkpoint、reviewer、pass_criteria 均为必填")
        return self


class WorkflowStep(DomainModel):
    """One ordered and independently reviewable workflow step."""

    step: int = Field(ge=1)
    name: NonBlankText
    objective: NonBlankText
    inputs: NonEmptyTextList
    actions: NonEmptyTextList
    outputs: NonEmptyTextList
    suggested_tools: Annotated[list[SuggestedTool], Field(min_length=1)]
    human_review: HumanReview


class Risk(DomainModel):
    """A risk with separate likelihood and severity dimensions."""

    category: RiskCategory
    description: NonBlankText
    impact: NonBlankText
    likelihood: RiskLevel
    severity: RiskLevel
    mitigation: NonBlankText


class AcceptanceMetric(DomainModel):
    """A measurable acceptance metric with an explicitly suggested target."""

    name: NonBlankText
    definition: NonBlankText
    measurement: NonBlankText
    target: NonBlankText

    @model_validator(mode="after")
    def require_suggested_target_label(self) -> Self:
        """AI-proposed targets must be visibly labelled as suggestions."""
        if "建议" not in self.target:
            raise ValueError("target 必须明确标注为建议值")
        return self


class AgentReport(DomainModel):
    """Root contract for a validated Agent diagnostic report."""

    title: NonBlankText
    requirement_summary: NonBlankText
    applicability: Applicability
    workflow: Annotated[list[WorkflowStep], Field(min_length=1)]
    risks: Annotated[list[Risk], Field(min_length=3)]
    acceptance_metrics: Annotated[list[AcceptanceMetric], Field(min_length=1)]
    assumptions: list[NonBlankText] = Field(default_factory=list)
    open_questions: list[NonBlankText] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_workflow_sequence_and_required_risks(self) -> Self:
        """Enforce consecutive steps and the three mandatory risk categories."""
        actual_steps = [item.step for item in self.workflow]
        expected_steps = list(range(1, len(self.workflow) + 1))
        if actual_steps != expected_steps:
            raise ValueError("workflow.step 必须从 1 开始连续递增")

        required_categories = {
            RiskCategory.PRIVACY,
            RiskCategory.PERMISSION,
            RiskCategory.ERRONEOUS_OUTPUT,
        }
        present_categories = {risk.category for risk in self.risks}
        missing_categories = required_categories - present_categories
        if missing_categories:
            missing = "、".join(sorted(category.value for category in missing_categories))
            raise ValueError(f"risks 缺少必备类别：{missing}")
        return self
