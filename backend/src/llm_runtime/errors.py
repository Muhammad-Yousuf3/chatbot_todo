"""LLM-specific error types for the agent runtime.

These errors provide granular control over error handling in the LLM
communication and tool execution layers.
"""


class LLMError(Exception):
    """Base exception for LLM operations.

    Attributes:
        message: Human-readable error description.
        code: Machine-readable error code for programmatic handling.
    """

    def __init__(self, message: str, code: str = "LLM_ERROR") -> None:
        self.message = message
        self.code = code
        super().__init__(message)


class RateLimitError(LLMError):
    """API rate limit exceeded.

    Attributes:
        retry_after: Seconds to wait before retrying (if provided by API).
    """

    def __init__(
        self, message: str = "Rate limit exceeded", retry_after: int | None = None
    ) -> None:
        super().__init__(message, code="RATE_LIMITED")
        self.retry_after = retry_after


class LLMTimeoutError(LLMError):
    """Request timed out.

    Named LLMTimeoutError to avoid shadowing builtin TimeoutError.
    """

    def __init__(self, message: str = "Request timed out") -> None:
        super().__init__(message, code="TIMEOUT")


class InvalidResponseError(LLMError):
    """Malformed LLM response that cannot be parsed.

    Attributes:
        raw_response: The raw response string that failed to parse.
    """

    def __init__(
        self, message: str = "Invalid LLM response", raw_response: str | None = None
    ) -> None:
        super().__init__(message, code="INVALID_RESPONSE")
        self.raw_response = raw_response


class ToolNotFoundError(LLMError):
    """Unknown tool requested by the LLM.

    Attributes:
        tool_name: The name of the tool that was not found.
    """

    def __init__(self, tool_name: str) -> None:
        super().__init__(f"Unknown tool: {tool_name}", code="TOOL_NOT_FOUND")
        self.tool_name = tool_name
