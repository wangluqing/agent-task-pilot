"""Shared synchronous contract for diagnostic report providers.

Providers receive a requirement that has already passed input validation and
return a fully validated domain report. This boundary does not perform input
validation, provider routing, UI work, Markdown rendering, or secret/config
management.
"""

from typing import Protocol, runtime_checkable

from agent_task_pilot.domain import AgentReport


@runtime_checkable
class DiagnosisProvider(Protocol):
    """Synchronous report-generation boundary shared by all providers."""

    def diagnose(self, validated_requirement: str) -> AgentReport:
        """Create a validated report for an already validated requirement."""
        ...
