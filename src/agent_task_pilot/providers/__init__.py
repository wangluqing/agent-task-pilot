"""Provider contracts and safe error taxonomy."""

from agent_task_pilot.providers.contracts import DiagnosisProvider
from agent_task_pilot.providers.deepseek import DeepSeekProvider
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
from agent_task_pilot.providers.mock import MockProvider

__all__ = [
    "AuthenticationError",
    "ConfigurationMissingError",
    "DeepSeekProvider",
    "DiagnosisProvider",
    "ErrorCode",
    "NetworkError",
    "MockProvider",
    "ParseError",
    "ProviderError",
    "RateLimitedError",
    "ReportValidationError",
    "ServiceError",
    "TimeoutError",
    "UnknownProviderError",
    "map_provider_exception",
]
