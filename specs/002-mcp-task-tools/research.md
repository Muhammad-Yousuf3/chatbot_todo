# Research: MCP Task Tools

**Feature Branch**: `002-mcp-task-tools`
**Date**: 2026-01-03
**Status**: Complete

## Research Questions Addressed

### 1. MCP SDK Tool Definition Patterns

**Decision**: Use FastMCP high-level API with decorator-based tool definitions

**Rationale**:
- FastMCP automatically generates input schemas from Python type hints
- Docstrings become tool descriptions visible to AI agents
- Async/await support for database operations
- Structured output validation via Pydantic models
- Simpler than low-level API while maintaining full functionality

**Alternatives Considered**:
- Low-level API with explicit schema definitions: More verbose, manual schema maintenance
- Third-party wrappers: Less documentation, not officially supported

**Source**: [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk), [Build an MCP Server](https://modelcontextprotocol.io/docs/develop/build-server)

### 2. MCP Server Deployment Model

**Decision**: Embedded MCP server within FastAPI backend process

**Rationale**:
- Simplifies deployment for hackathon scope
- MCP server shares database connection pool with FastAPI
- Single process reduces operational complexity
- STDIO transport for local development; can migrate to SSE for production

**Alternatives Considered**:
- Separate MCP microservice: Better isolation but adds deployment complexity
- Hosted MCP Tools (OpenAI infrastructure): Requires OpenAI platform dependency

**Source**: [OpenAI Agents SDK MCP Integration](https://github.com/openai/openai-agents-python/blob/main/docs/mcp.md)

### 3. Tool Granularity

**Decision**: One tool per task action (add_task, list_tasks, update_task, complete_task, delete_task)

**Rationale**:
- Clear contracts for each operation
- Easier auditing and tracing
- Independent testing per tool
- AI agents can select precise action
- Aligns with constitution principle of deterministic behavior

**Alternatives Considered**:
- Generic `mutate_task` tool with action parameter: Higher ambiguity, harder to audit
- Combined `create_or_update` tool: Violates single responsibility principle

### 4. User Context and Ownership Enforcement

**Decision**: Enforce ownership inside each MCP tool; user_id passed as explicit parameter

**Rationale**:
- MCP tools are the security boundary per constitution (Principle IV)
- User ID is externally provided, not self-determined by AI
- Each tool validates ownership before any database operation
- Prevents data leakage even if agent layer is compromised

**Alternatives Considered**:
- Enforce in agent layer: Higher risk if agent bypassed
- Session-based context: Violates stateless principle

**Implementation Pattern**:
```python
@mcp.tool()
async def add_task(user_id: str, description: str, ctx: Context) -> TaskResult:
    """Create a new task for the specified user."""
    # user_id is required and validated
    # Database operation uses user_id for ownership
```

### 5. Error Handling Strategy

**Decision**: Structured error responses per tool using Pydantic models

**Rationale**:
- Predictable AI behavior based on error type
- Clear separation of success/error paths
- Validation errors are explicit and actionable
- Aligns with MCP structured output support

**Implementation Pattern**:
```python
class ToolResult(BaseModel):
    success: bool
    data: Optional[dict] = None
    error: Optional[str] = None
    error_code: Optional[str] = None  # e.g., "NOT_FOUND", "VALIDATION_ERROR", "ACCESS_DENIED"
```

**Alternatives Considered**:
- Exception-based errors: Less control, harder for AI to interpret
- String-only responses: No structured error handling

### 6. Database Access Pattern

**Decision**: Use SQLModel with async session via lifespan context

**Rationale**:
- Consistent with existing conversation persistence spec
- Lifespan pattern ensures proper connection pooling
- Async operations for non-blocking database calls
- SQLModel provides type safety with Pydantic integration

**Implementation Pattern**:
```python
from contextlib import asynccontextmanager
from sqlmodel.ext.asyncio.session import AsyncSession

@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[AppContext]:
    engine = create_async_engine(DATABASE_URL)
    try:
        yield AppContext(engine=engine)
    finally:
        await engine.dispose()

mcp = FastMCP("task-tools", lifespan=app_lifespan)

@mcp.tool()
async def add_task(user_id: str, description: str, ctx: Context) -> ToolResult:
    engine = ctx.request_context.lifespan_context.engine
    async with AsyncSession(engine) as session:
        # Database operations
```

### 7. Transport Configuration

**Decision**: STDIO transport for development, SSE for production

**Rationale**:
- STDIO is simplest for local testing with OpenAI Agents SDK
- SSE enables remote/distributed deployments
- OpenAI Agents SDK supports both via MCPServerStdio and MCPServerSSE

**Source**: [OpenAI Agents SDK](https://developers.openai.com/apps-sdk/concepts/mcp-server/)

### 8. Testing Strategy

**Decision**: Direct tool invocation tests without AI agent involvement

**Rationale**:
- Tools are deterministic and independently testable
- Faster test execution without AI roundtrips
- Clear validation of each tool's behavior
- Ownership enforcement tested via explicit user_id variations

**Test Categories**:
1. Unit tests: Individual tool functions with mocked database
2. Integration tests: Tools against real database
3. Contract tests: Verify input/output schemas
4. Ownership tests: Verify user isolation

## Technology Decisions Summary

| Decision | Choice | Constitution Alignment |
|----------|--------|----------------------|
| MCP SDK | FastMCP (high-level API) | Principle V: Simplicity |
| Deployment | Embedded in FastAPI | Principle II: Stateless Backend |
| Tool Granularity | One per action | Principle VI: Deterministic |
| Ownership Enforcement | Inside each tool | Principle IV: AI Safety |
| Error Handling | Structured responses | Principle VI: Debuggable |
| Database Access | SQLModel async lifespan | Technical Constraints |
| Transport | STDIO (dev) / SSE (prod) | Principle III: Clear Boundaries |

## Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| mcp | >=1.25,<2 | MCP Python SDK |
| fastmcp | (included in mcp) | High-level server API |
| sqlmodel | existing | Database ORM |
| pydantic | existing | Validation and schemas |
| httpx | existing | Async HTTP (if needed) |

## Open Questions Resolved

1. ~~How does user context flow from agent to MCP tool?~~ → Explicit user_id parameter
2. ~~Can MCP tools access shared database connection?~~ → Yes, via lifespan context
3. ~~What transport for production?~~ → SSE, with STDIO for development
4. ~~How to handle idempotent operations?~~ → Return success even if already completed/deleted
