"""Gemini LLM adapter for the agent runtime.

This module handles communication with the Google Gemini API,
converting between internal message formats and Gemini's expected format.
"""

import asyncio
import logging
import os
from typing import Any

from google import genai
from google.genai import types

from src.llm_runtime.errors import (
    InvalidResponseError,
    LLMError,
    LLMTimeoutError,
    RateLimitError,
)
from src.llm_runtime.schemas import (
    FunctionCall,
    LLMMessage,
    LLMResponse,
    TokenUsage,
    ToolDeclaration,
)

logger = logging.getLogger(__name__)


class GeminiAdapter:
    """Gemini-specific implementation of the LLM adapter.

    Handles:
    - Message format conversion
    - Function/tool calling
    - Error handling and retries
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "gemini-2.0-flash",
        timeout: int = 30,
        max_retries: int = 1,
    ) -> None:
        """Initialize the Gemini client.

        Args:
            api_key: Google AI API key. If not provided, reads from GEMINI_API_KEY env var.
            model: Model identifier (default: gemini-2.0-flash).
            timeout: Request timeout in seconds.
            max_retries: Number of retries for transient failures.
        """
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set")

        self.model = model
        self.timeout = timeout
        self.max_retries = max_retries

        # Initialize the client
        self._client = genai.Client(api_key=self.api_key)

    async def generate(
        self,
        messages: list[LLMMessage],
        tools: list[ToolDeclaration],
        temperature: float = 0.0,
        max_tokens: int = 1024,
    ) -> LLMResponse:
        """Generate a response from Gemini.

        Args:
            messages: Conversation history in LLMMessage format.
            tools: Available tool declarations.
            temperature: Sampling temperature (0.0 = deterministic).
            max_tokens: Maximum response tokens.

        Returns:
            LLMResponse with content and/or function calls.

        Raises:
            LLMError: On API failures.
            RateLimitError: When rate limited.
            LLMTimeoutError: On request timeout.
        """
        # Convert messages to Gemini format
        gemini_contents = self._convert_messages_to_gemini(messages)

        # Convert tool declarations to Gemini format
        gemini_tools = self._convert_tools_to_gemini(tools) if tools else None

        # Build config
        config = types.GenerateContentConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
        )

        # Add tools if available
        if gemini_tools:
            config = types.GenerateContentConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
                tools=[gemini_tools],
            )

        # Make the API call with retry logic
        for attempt in range(self.max_retries + 1):
            try:
                response = await self._call_api(gemini_contents, config)
                return self._parse_response(response)

            except RateLimitError:
                raise  # Don't retry rate limits
            except LLMTimeoutError:
                if attempt < self.max_retries:
                    logger.warning(f"Timeout on attempt {attempt + 1}, retrying...")
                    await asyncio.sleep(1)  # Brief delay before retry
                else:
                    raise
            except LLMError:
                if attempt < self.max_retries:
                    logger.warning(f"Error on attempt {attempt + 1}, retrying...")
                    await asyncio.sleep(1)
                else:
                    raise

        # Should not reach here, but just in case
        raise LLMError("Max retries exceeded")

    async def _call_api(
        self,
        contents: list[types.Content],
        config: types.GenerateContentConfig,
    ) -> types.GenerateContentResponse:
        """Make the actual API call.

        Args:
            contents: Gemini-formatted messages.
            config: Generation configuration.

        Returns:
            Gemini API response.

        Raises:
            RateLimitError: On 429 status.
            LLMTimeoutError: On timeout.
            LLMError: On other errors.
        """
        try:
            # Run synchronous API call in executor to avoid blocking
            loop = asyncio.get_event_loop()
            response = await asyncio.wait_for(
                loop.run_in_executor(
                    None,
                    lambda: self._client.models.generate_content(
                        model=self.model,
                        contents=contents,
                        config=config,
                    ),
                ),
                timeout=self.timeout,
            )
            return response

        except asyncio.TimeoutError as e:
            logger.error(f"Request timed out after {self.timeout}s")
            raise LLMTimeoutError(f"Request timed out after {self.timeout}s") from e

        except Exception as e:
            error_msg = str(e).lower()

            # Check for rate limiting
            if "429" in error_msg or "rate limit" in error_msg:
                logger.warning("Rate limit exceeded")
                raise RateLimitError()

            # Check for quota issues
            if "quota" in error_msg:
                logger.error("API quota exceeded")
                raise RateLimitError("API quota exceeded")

            # Generic error
            logger.error(f"Gemini API error: {e}")
            raise LLMError(f"API error: {e}") from e

    def _convert_messages_to_gemini(
        self, messages: list[LLMMessage]
    ) -> list[types.Content]:
        """Convert internal messages to Gemini format.

        Args:
            messages: List of LLMMessage objects.

        Returns:
            List of Gemini Content objects.
        """
        gemini_contents: list[types.Content] = []

        for msg in messages:
            if msg.role == "user":
                gemini_contents.append(
                    types.Content(
                        role="user",
                        parts=[types.Part(text=msg.content)],
                    )
                )

            elif msg.role == "assistant":
                if msg.function_call:
                    # Assistant message with function call
                    gemini_contents.append(
                        types.Content(
                            role="model",
                            parts=[
                                types.Part(
                                    function_call=types.FunctionCall(
                                        name=msg.function_call.name,
                                        args=msg.function_call.arguments,
                                    )
                                )
                            ],
                        )
                    )
                elif msg.content:
                    # Assistant text message
                    gemini_contents.append(
                        types.Content(
                            role="model",
                            parts=[types.Part(text=msg.content)],
                        )
                    )

            elif msg.role == "function":
                # Function response
                if msg.function_response:
                    gemini_contents.append(
                        types.Content(
                            role="user",
                            parts=[
                                types.Part(
                                    function_response=types.FunctionResponse(
                                        name=msg.function_response.name,
                                        response=msg.function_response.response,
                                    )
                                )
                            ],
                        )
                    )

        return gemini_contents

    def _convert_tools_to_gemini(
        self, tools: list[ToolDeclaration]
    ) -> types.Tool:
        """Convert tool declarations to Gemini format.

        Args:
            tools: List of ToolDeclaration objects.

        Returns:
            Gemini Tool object with function declarations.
        """
        function_declarations = []

        for tool in tools:
            func_decl = types.FunctionDeclaration(
                name=tool.name,
                description=tool.description,
                parameters=tool.parameters,
            )
            function_declarations.append(func_decl)

        return types.Tool(function_declarations=function_declarations)

    def _parse_response(
        self, response: types.GenerateContentResponse
    ) -> LLMResponse:
        """Parse Gemini response into internal format.

        Args:
            response: Gemini API response.

        Returns:
            LLMResponse object.

        Raises:
            InvalidResponseError: If response cannot be parsed.
        """
        try:
            # Check for valid response
            if not response.candidates:
                return LLMResponse(
                    content=None,
                    function_calls=None,
                    finish_reason="error",
                    error="No candidates in response",
                )

            candidate = response.candidates[0]
            content = candidate.content

            # Extract text content and function calls
            text_content: str | None = None
            function_calls: list[FunctionCall] = []

            if content and content.parts:
                for part in content.parts:
                    if hasattr(part, "text") and part.text:
                        text_content = part.text
                    elif hasattr(part, "function_call") and part.function_call:
                        fc = part.function_call
                        function_calls.append(
                            FunctionCall(
                                name=fc.name,
                                arguments=dict(fc.args) if fc.args else {},
                            )
                        )

            # Determine finish reason
            finish_reason: str = "stop"
            if function_calls:
                finish_reason = "tool_calls"
            elif candidate.finish_reason:
                reason = str(candidate.finish_reason).lower()
                if "max_tokens" in reason or "length" in reason:
                    finish_reason = "max_tokens"
                elif "safety" in reason or "block" in reason:
                    finish_reason = "error"

            # Extract usage if available
            usage: TokenUsage | None = None
            if hasattr(response, "usage_metadata") and response.usage_metadata:
                usage = TokenUsage(
                    prompt_tokens=response.usage_metadata.prompt_token_count or 0,
                    completion_tokens=response.usage_metadata.candidates_token_count or 0,
                    total_tokens=response.usage_metadata.total_token_count or 0,
                )

            return LLMResponse(
                content=text_content,
                function_calls=function_calls if function_calls else None,
                finish_reason=finish_reason,
                usage=usage,
            )

        except Exception as e:
            logger.error(f"Failed to parse Gemini response: {e}")
            raise InvalidResponseError(
                f"Failed to parse response: {e}",
                raw_response=str(response),
            ) from e

    def get_tool_declarations(
        self, tool_names: list[str]
    ) -> list[ToolDeclaration]:
        """Get tool declarations for specified tool names.

        This is a helper method that returns predefined tool schemas.

        Args:
            tool_names: List of tool names to include.

        Returns:
            List of ToolDeclaration objects.
        """
        all_tools = {
            "add_task": ToolDeclaration(
                name="add_task",
                description="Create a new task. Use when user wants to add, create, or remember something.",
                parameters={
                    "type": "object",
                    "properties": {
                        "description": {"type": "string", "description": "Task description"}
                    },
                    "required": ["description"],
                },
            ),
            "list_tasks": ToolDeclaration(
                name="list_tasks",
                description="Get user's tasks. Use when user wants to see, view, or list their tasks.",
                parameters={
                    "type": "object",
                    "properties": {
                        "status": {
                            "type": "string",
                            "enum": ["pending", "completed", "all"],
                            "description": "Filter by status (default: all)",
                        }
                    },
                },
            ),
            "update_task": ToolDeclaration(
                name="update_task",
                description="Update a task's description. Use when user wants to change, edit, or rename a task.",
                parameters={
                    "type": "object",
                    "properties": {
                        "task_id": {"type": "string", "description": "Task ID to update"},
                        "description": {"type": "string", "description": "New description"},
                    },
                    "required": ["task_id", "description"],
                },
            ),
            "complete_task": ToolDeclaration(
                name="complete_task",
                description="Mark a task as completed. Use when user says done, finished, or completed.",
                parameters={
                    "type": "object",
                    "properties": {
                        "task_id": {"type": "string", "description": "Task ID to complete"}
                    },
                    "required": ["task_id"],
                },
            ),
            "delete_task": ToolDeclaration(
                name="delete_task",
                description="Delete a task permanently. Use when user wants to remove or delete a task.",
                parameters={
                    "type": "object",
                    "properties": {
                        "task_id": {"type": "string", "description": "Task ID to delete"}
                    },
                    "required": ["task_id"],
                },
            ),
        }

        return [all_tools[name] for name in tool_names if name in all_tools]
