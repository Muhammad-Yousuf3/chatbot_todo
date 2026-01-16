"""LLM-powered agent decision engine.

This module provides the core orchestration logic for the LLM agent runtime.
It replaces the rule-based AgentDecisionEngine with LLM-driven decisions.
"""

import logging
import time
from pathlib import Path
from typing import Any, Protocol

from src.agent.schemas import (
    AgentDecision,
    DecisionContext,
    DecisionType,
    ToolCall,
    ToolName,
)
from src.llm_runtime.errors import (
    LLMError,
    LLMTimeoutError,
    RateLimitError,
    ToolNotFoundError,
)
from src.llm_runtime.schemas import (
    FunctionCall,
    FunctionResponse,
    LLMMessage,
    LLMResponse,
    ToolDeclaration,
)

logger = logging.getLogger(__name__)


class LLMAdapterProtocol(Protocol):
    """Protocol for LLM adapters."""

    async def generate(
        self,
        messages: list[LLMMessage],
        tools: list[ToolDeclaration],
        temperature: float = 0.0,
        max_tokens: int = 1024,
    ) -> LLMResponse: ...


class ToolExecutorProtocol(Protocol):
    """Protocol for tool executors."""

    async def execute(
        self,
        tool_name: str,
        parameters: dict[str, Any],
        user_id: str,
    ) -> Any: ...

    def get_tool_declarations(self) -> list[ToolDeclaration]: ...


class LLMAgentEngine:
    """LLM-powered agent decision engine.

    Replaces the rule-based AgentDecisionEngine with LLM-driven decisions
    while maintaining the same DecisionContext -> AgentDecision contract.

    Usage:
        adapter = GeminiAdapter(api_key="...")
        executor = ToolExecutor()
        constitution = load_constitution()
        engine = LLMAgentEngine(adapter, executor, constitution)

        decision = await engine.process_message(context)
    """

    def __init__(
        self,
        llm_adapter: LLMAdapterProtocol,
        tool_executor: ToolExecutorProtocol,
        constitution: str,
        max_iterations: int = 5,
        temperature: float = 0.0,
        max_tokens: int = 1024,
    ) -> None:
        """Initialize the LLM agent engine.

        Args:
            llm_adapter: LLM provider adapter (e.g., GeminiAdapter).
            tool_executor: MCP tool execution adapter.
            constitution: System prompt defining agent behavior.
            max_iterations: Max tool-calling loop iterations (default: 5).
            temperature: LLM sampling temperature (default: 0.0 for determinism).
            max_tokens: Max response tokens (default: 1024).
        """
        self._adapter = llm_adapter
        self._executor = tool_executor
        self._constitution = constitution
        self._max_iterations = max_iterations
        self._temperature = temperature
        self._max_tokens = max_tokens

    async def process_message(
        self,
        context: DecisionContext,
    ) -> AgentDecision:
        """Process a user message and return an agent decision.

        This is the main entry point, matching the existing engine contract.

        Args:
            context: Complete decision context with message and history.

        Returns:
            AgentDecision with response or tool calls.
        """
        start_time = time.time()

        try:
            # Build initial messages from context
            messages = self._build_messages_from_context(context)

            # Get available tools
            tools = self._executor.get_tool_declarations()

            # Execute the tool loop
            decision, executed_tools = await self._tool_execution_loop(
                messages=messages,
                tools=tools,
                user_id=context.user_id,
            )

            # Log duration
            duration_ms = int((time.time() - start_time) * 1000)
            logger.debug(f"process_message completed in {duration_ms}ms")

            return decision

        except RateLimitError:
            logger.warning("Rate limit exceeded")
            return AgentDecision(
                decision_type=DecisionType.RESPOND_ONLY,
                response_text="I'm receiving too many requests right now. Please wait a moment and try again.",
            )

        except LLMTimeoutError:
            logger.error("LLM request timed out")
            return AgentDecision(
                decision_type=DecisionType.RESPOND_ONLY,
                response_text="I'm having trouble processing your request. Please try again.",
            )

        except LLMError as e:
            logger.error(f"LLM error: {e}")
            return AgentDecision(
                decision_type=DecisionType.RESPOND_ONLY,
                response_text="I'm having trouble processing your request. Please try again.",
            )

        except Exception as e:
            logger.exception(f"Unexpected error in process_message: {e}")
            return AgentDecision(
                decision_type=DecisionType.RESPOND_ONLY,
                response_text="Something went wrong. Please try again.",
            )

    def _build_messages_from_context(
        self,
        context: DecisionContext,
    ) -> list[LLMMessage]:
        """Build LLM messages from decision context.

        Args:
            context: Decision context with message and history.

        Returns:
            List of LLMMessage objects for the LLM.
        """
        messages: list[LLMMessage] = []

        # Add system prompt as first user message (Gemini doesn't have system role)
        # We'll prepend it to the first user message or add it separately
        system_content = self._constitution

        # Add conversation history
        for msg in context.message_history:
            if msg.role == "user":
                messages.append(LLMMessage(role="user", content=msg.content))
            elif msg.role == "assistant":
                messages.append(LLMMessage(role="assistant", content=msg.content))

        # Add current user message with system prompt prepended
        if not messages:
            # First message - include system prompt
            combined_content = f"{system_content}\n\n---\n\nUser message: {context.message}"
            messages.append(LLMMessage(role="user", content=combined_content))
        else:
            # Add current message
            messages.append(LLMMessage(role="user", content=context.message))
            # Insert system prompt at beginning
            messages.insert(
                0,
                LLMMessage(role="user", content=f"System instructions:\n{system_content}"),
            )
            messages.insert(
                1,
                LLMMessage(role="assistant", content="I understand. I'll follow these instructions."),
            )

        return messages

    async def _tool_execution_loop(
        self,
        messages: list[LLMMessage],
        tools: list[ToolDeclaration],
        user_id: str,
    ) -> tuple[AgentDecision, list[ToolCall]]:
        """Execute the tool calling loop.

        Args:
            messages: Current conversation messages.
            tools: Available tool declarations.
            user_id: User ID for tool execution.

        Returns:
            Tuple of (AgentDecision, list of executed ToolCalls).
        """
        executed_tools: list[ToolCall] = []
        iteration = 0

        while iteration < self._max_iterations:
            iteration += 1
            logger.debug(f"Tool loop iteration {iteration}/{self._max_iterations}")

            # Invoke LLM
            response = await self._adapter.generate(
                messages=messages,
                tools=tools,
                temperature=self._temperature,
                max_tokens=self._max_tokens,
            )

            # Check for direct response (no tools)
            if response.finish_reason == "stop" or not response.function_calls:
                return self._build_response_decision(response, executed_tools), executed_tools

            # Check for error
            if response.finish_reason == "error":
                logger.error(f"LLM returned error: {response.error}")
                return AgentDecision(
                    decision_type=DecisionType.RESPOND_ONLY,
                    response_text="I had trouble processing that. Please try again.",
                ), executed_tools

            # Execute tool calls
            for fc in response.function_calls:
                tool_result = await self._execute_single_tool(
                    fc, user_id, len(executed_tools) + 1
                )

                if tool_result:
                    executed_tools.append(tool_result)

                    # Add assistant message with function call
                    messages.append(
                        LLMMessage(
                            role="assistant",
                            content=None,
                            function_call=fc,
                        )
                    )

                    # Add function response
                    messages.append(
                        LLMMessage(
                            role="function",
                            function_response=FunctionResponse(
                                name=fc.name,
                                response=tool_result.parameters,  # Result data
                            ),
                        )
                    )

        # Max iterations reached
        logger.warning(f"Max iterations ({self._max_iterations}) reached")
        # Note: RESPOND_ONLY cannot include tool_calls per AgentDecision validation
        return AgentDecision(
            decision_type=DecisionType.RESPOND_ONLY,
            response_text="That request is a bit too complex. Could you break it into smaller steps?",
        ), executed_tools

    async def _execute_single_tool(
        self,
        function_call: FunctionCall,
        user_id: str,
        sequence: int,
    ) -> ToolCall | None:
        """Execute a single tool call.

        Args:
            function_call: The function call from the LLM.
            user_id: User ID for the tool.
            sequence: Execution sequence number.

        Returns:
            ToolCall record or None if tool not found.
        """
        tool_name = function_call.name

        # Map to ToolName enum if possible
        try:
            tool_enum = ToolName(tool_name)
        except ValueError:
            logger.warning(f"Unknown tool requested: {tool_name}")
            return None

        try:
            result = await self._executor.execute(
                tool_name=tool_name,
                parameters=function_call.arguments,
                user_id=user_id,
            )

            # Build ToolCall record
            return ToolCall(
                tool_name=tool_enum,
                parameters={
                    "user_id": user_id,
                    **function_call.arguments,
                    "_result": result.data if hasattr(result, "data") else result,
                    "_success": result.success if hasattr(result, "success") else True,
                },
                sequence=sequence,
            )

        except ToolNotFoundError:
            logger.warning(f"Tool not found: {tool_name}")
            return None

        except Exception as e:
            logger.error(f"Tool execution failed: {e}")
            # Return a tool call with error info
            return ToolCall(
                tool_name=tool_enum,
                parameters={
                    "user_id": user_id,
                    **function_call.arguments,
                    "_error": str(e),
                    "_success": False,
                },
                sequence=sequence,
            )

    def _build_response_decision(
        self,
        response: LLMResponse,
        executed_tools: list[ToolCall],
    ) -> AgentDecision:
        """Build an AgentDecision from an LLM response.

        Args:
            response: The LLM response.
            executed_tools: Tools that were executed.

        Returns:
            AgentDecision with appropriate type and content.
        """
        content = response.content or ""

        # Determine decision type
        if executed_tools:
            # Tools were executed
            decision_type = DecisionType.INVOKE_TOOL
        elif self._is_clarification_response(content):
            # Response is asking for clarification
            decision_type = DecisionType.ASK_CLARIFICATION
        else:
            # Direct response
            decision_type = DecisionType.RESPOND_ONLY

        # Build decision
        if decision_type == DecisionType.ASK_CLARIFICATION:
            return AgentDecision(
                decision_type=decision_type,
                clarification_question=content,
                response_text=content,
            )
        elif decision_type == DecisionType.INVOKE_TOOL:
            return AgentDecision(
                decision_type=decision_type,
                tool_calls=executed_tools,
                response_text=content,
            )
        else:
            return AgentDecision(
                decision_type=decision_type,
                response_text=content,
            )

    def _is_clarification_response(self, content: str) -> bool:
        """Check if a response is asking for clarification.

        Args:
            content: Response content.

        Returns:
            True if the response appears to be asking for clarification.
        """
        if not content:
            return False

        content_lower = content.lower()

        # Check for question patterns
        clarification_indicators = [
            "would you like",
            "do you want",
            "could you",
            "can you clarify",
            "what do you mean",
            "which task",
            "which one",
            "please specify",
            "not sure which",
            "are you referring to",
        ]

        return any(indicator in content_lower for indicator in clarification_indicators)


def load_constitution(path: str | Path | None = None) -> str:
    """Load constitution from file.

    Args:
        path: Path to constitution file. If None, uses default location.

    Returns:
        Constitution text.
    """
    if path is None:
        path = Path(__file__).parent / "constitution.md"

    path = Path(path)

    if not path.exists():
        logger.warning(f"Constitution file not found at {path}, using default")
        return "You are a helpful task management assistant."

    return path.read_text()
