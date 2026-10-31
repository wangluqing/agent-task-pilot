"""Framework-independent orchestration for Agent diagnosis requests."""

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Protocol

from pydantic import ValidationError

from agent_task_pilot.domain import AgentReport
from agent_task_pilot.providers import (
    ConfigurationMissingError,
    DiagnosisProvider,
    MockProvider,
    ProviderError,
    ReportValidationError,
    UnknownProviderError,
    map_provider_exception,
)
from agent_task_pilot.renderers import MarkdownRenderer
from agent_task_pilot.services.input_validation import (
    AnalysisMode,
    validate_analysis_input,
)


class ReportRenderer(Protocol):
    """Minimal rendering boundary used for dependency injection in the service."""

    def render(self, report: AgentReport) -> str:
        """Render one validated report."""
        ...


@dataclass(frozen=True, slots=True)
class DiagnosisResult:
    """Complete successful result; failures are represented only by exceptions."""

    report: AgentReport
    markdown: str


class DiagnosisService:
    """Validate, diagnose, revalidate, and render one request synchronously."""

    def __init__(
        self,
        providers: Mapping[AnalysisMode, DiagnosisProvider] | None = None,
        renderer: ReportRenderer | None = None,
    ) -> None:
        configured_providers: dict[AnalysisMode, DiagnosisProvider] = {
            AnalysisMode.MOCK: MockProvider()
        }
        if providers is not None:
            configured_providers.update(providers)
        self._providers = configured_providers
        self._renderer = renderer or MarkdownRenderer()

    def analyze(
        self,
        requirement: object,
        mode: object = AnalysisMode.MOCK,
    ) -> DiagnosisResult:
        """Run the complete diagnosis pipeline or raise a safe typed error."""
        validated_input = validate_analysis_input(requirement, mode)
        provider = self._providers.get(validated_input.mode)
        if provider is None:
            raise ConfigurationMissingError

        raw_report = self._call_provider(provider, validated_input.validated_requirement)
        report = self._validate_report(raw_report)
        markdown = self._render_report(report)
        return DiagnosisResult(report=report, markdown=markdown)

    @staticmethod
    def _call_provider(provider: DiagnosisProvider, requirement: str) -> object:
        try:
            return provider.diagnose(requirement)
        except ProviderError:
            raise
        except Exception as error:
            raise map_provider_exception(error) from None

    @staticmethod
    def _validate_report(raw_report: object) -> AgentReport:
        if not isinstance(raw_report, AgentReport):
            raise ReportValidationError
        try:
            return AgentReport.model_validate(raw_report.model_dump(mode="python"))
        except ValidationError:
            raise ReportValidationError from None
        except Exception:
            raise UnknownProviderError from None

    def _render_report(self, report: AgentReport) -> str:
        try:
            markdown = self._renderer.render(report)
        except Exception:
            raise UnknownProviderError from None
        if not isinstance(markdown, str) or not markdown.strip():
            raise UnknownProviderError
        return markdown
