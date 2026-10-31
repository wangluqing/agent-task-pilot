"""Stable, user-safe error taxonomy for diagnostic providers."""

from collections.abc import Mapping
from enum import StrEnum
from types import MappingProxyType


class ErrorCode(StrEnum):
    """Stable provider failure codes used across implementations."""

    CONFIG_MISSING = "CONFIG_MISSING"
    AUTH_FAILED = "AUTH_FAILED"
    RATE_LIMITED = "RATE_LIMITED"
    TIMEOUT = "TIMEOUT"
    NETWORK_ERROR = "NETWORK_ERROR"
    SERVICE_ERROR = "SERVICE_ERROR"
    PARSE_ERROR = "PARSE_ERROR"
    REPORT_VALIDATION_ERROR = "REPORT_VALIDATION_ERROR"
    UNKNOWN_ERROR = "UNKNOWN_ERROR"


ERROR_MESSAGES: Mapping[ErrorCode, str] = MappingProxyType(
    {
        ErrorCode.CONFIG_MISSING: "系统缺少必要配置，请联系管理员。",
        ErrorCode.AUTH_FAILED: "外部服务认证失败，请联系管理员检查配置。",
        ErrorCode.RATE_LIMITED: "请求过于频繁，请稍后重试。",
        ErrorCode.TIMEOUT: "处理请求超时，请稍后重试。",
        ErrorCode.NETWORK_ERROR: "无法连接外部服务，请稍后重试。",
        ErrorCode.SERVICE_ERROR: "外部服务暂时不可用，请稍后重试。",
        ErrorCode.PARSE_ERROR: "外部服务返回内容无法解析，请重试。",
        ErrorCode.REPORT_VALIDATION_ERROR: "生成的报告未通过结构校验，请重试。",
        ErrorCode.UNKNOWN_ERROR: "处理请求时发生未知错误，请稍后重试。",
    }
)


class ProviderError(Exception):
    """Base provider failure exposing only a stable code and safe message."""

    code: ErrorCode

    def __init__(self) -> None:
        self.user_message = ERROR_MESSAGES[self.code]
        super().__init__(self.user_message)


class ConfigurationMissingError(ProviderError):
    """Required provider configuration is unavailable."""

    code = ErrorCode.CONFIG_MISSING


class AuthenticationError(ProviderError):
    """The provider rejected configured credentials."""

    code = ErrorCode.AUTH_FAILED


class RateLimitedError(ProviderError):
    """The provider rejected a request due to rate limiting."""

    code = ErrorCode.RATE_LIMITED


class TimeoutError(ProviderError):
    """The provider request exceeded its configured timeout."""

    code = ErrorCode.TIMEOUT


class NetworkError(ProviderError):
    """The provider could not be reached over the network."""

    code = ErrorCode.NETWORK_ERROR


class ServiceError(ProviderError):
    """The provider service returned a non-specific service failure."""

    code = ErrorCode.SERVICE_ERROR


class ParseError(ProviderError):
    """The provider response could not be parsed."""

    code = ErrorCode.PARSE_ERROR


class ReportValidationError(ProviderError):
    """The parsed response did not satisfy the AgentReport contract."""

    code = ErrorCode.REPORT_VALIDATION_ERROR


class UnknownProviderError(ProviderError):
    """An unexpected provider-boundary failure occurred."""

    code = ErrorCode.UNKNOWN_ERROR


def map_provider_exception(error: Exception) -> ProviderError:
    """Map an exception to a safe provider error without retaining its details.

    Known provider errors are preserved. Unknown exceptions are deliberately
    replaced instead of wrapped, so their messages, response bodies, request
    data, credentials, and tracebacks cannot leak through the user-facing error.
    """
    if isinstance(error, ProviderError):
        return error
    return UnknownProviderError()
