"""Provider contracts and safe error taxonomy."""

from agent_task_pilot.providers.contracts import DiagnosisProvider
from agent_task_pilot.providers.errors import (
    AuthenticationError,
    ConfigurationMissingError,
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

__all__ = [
    "AuthenticationError",
    "ConfigurationMissingError",
    "DiagnosisProvider",
    "ErrorCode",
    "NetworkError",
    "ParseError",
    "ProviderError",
    "RateLimitedError",
    "ReportValidationError",
    "ServiceError",
    "TimeoutError",
    "UnknownProviderError",
    "map_provider_exception",
]
