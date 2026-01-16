"""LLM-specific Pydantic models for the agent runtime.

These models handle communication with the LLM provider (Gemini) and
are separate from the core agent schemas in src/agent/schemas.py.
"""

from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator


class FunctionCall(BaseModel):
    """Represents an LLM-requested tool invocation.

    This is returned by the LLM when it wants to call a tool.
    """

    name: str = Field(..., description="Tool name (must be in whitelist)")
    arguments: dict[str, Any] = Field(
        default_factory=dict, description="Parameters for the tool"
    )


class FunctionResponse(BaseModel):
    """Represents the result of a tool execution.

    This is sent back to the LLM after executing a tool.
    """

    name: str = Field(..., description="Tool name that was called")
    response: dict[str, Any] = Field(..., description="Serialized ToolResult")


class LLMMessage(BaseModel):
    """A single message in the LLM conversation format.

    Supports user messages, assistant responses, and function call/response
    messages for multi-turn tool execution.
    """

    role: Literal["user", "assistant", "function"] = Field(
        ..., description="Message sender role"
    )
    content: str | None = Field(
        default=None, description="Text content (required for user/assistant)"
    )
    function_call: FunctionCall | None = Field(
        default=None, description="Tool call from assistant"
    )
    function_response: FunctionResponse | None = Field(
        default=None, description="Result from tool execution"
    )

    @model_validator(mode="after")
    def validate_message_structure(self) -> "LLMMessage":
        """Validate that message structure matches role."""
        if self.role == "user":
            if self.content is None:
                raise ValueError("User messages must have content")
            if self.function_call is not None or self.function_response is not None:
                raise ValueError("User messages cannot have function_call or function_response")

        elif self.role == "assistant":
            # Assistant can have content, function_call, or both
            if self.function_response is not None:
                raise ValueError("Assistant messages cannot have function_response")

        elif self.role == "function":
            if self.function_response is None:
                raise ValueError("Function messages must have function_response")
            if self.content is not None or self.function_call is not None:
                raise ValueError("Function messages can only have function_response")

        return self


class TokenUsage(BaseModel):
    """Token consumption tracking."""

    prompt_tokens: int = Field(..., ge=0, description="Tokens in input")
    completion_tokens: int = Field(..., ge=0, description="Tokens in output")
    total_tokens: int = Field(..., ge=0, description="Sum of above")


class ToolDeclaration(BaseModel):
    """Schema for a tool available to the LLM.

    This follows the OpenAPI-compatible format expected by Gemini.
    """

    name: str = Field(..., description="Tool identifier")
    description: str = Field(..., description="What the tool does")
    parameters: dict[str, Any] = Field(..., description="JSON Schema for parameters")


class LLMRequest(BaseModel):
    """Request sent to the LLM adapter."""

    messages: list[LLMMessage] = Field(..., description="Conversation history")
    tools: list[ToolDeclaration] = Field(
        default_factory=list, description="Available tools"
    )
    temperature: float = Field(default=0.0, ge=0.0, le=2.0, description="Sampling temperature")
    max_tokens: int = Field(default=1024, gt=0, description="Max response tokens")


class LLMResponse(BaseModel):
    """Response from the LLM adapter."""

    content: str | None = Field(default=None, description="Text response")
    function_calls: list[FunctionCall] | None = Field(
        default=None, description="Requested tool calls"
    )
    finish_reason: Literal["stop", "tool_calls", "max_tokens", "error"] = Field(
        ..., description="Why generation stopped"
    )
    usage: TokenUsage | None = Field(default=None, description="Token consumption stats")
    error: str | None = Field(default=None, description="Error message if finish_reason is error")

    @model_validator(mode="after")
    def validate_response_structure(self) -> "LLMResponse":
        """Validate response structure matches finish_reason."""
        if self.finish_reason == "tool_calls":
            if not self.function_calls:
                raise ValueError("tool_calls finish_reason requires function_calls")
        if self.finish_reason == "error":
            if not self.error:
                raise ValueError("error finish_reason requires error message")
        return self
