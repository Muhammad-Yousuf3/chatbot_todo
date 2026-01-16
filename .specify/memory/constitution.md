<!--
================================================================================
SYNC IMPACT REPORT
================================================================================
Version change: 1.0.0 → 1.1.0 (MINOR: Authentication technology update)

Modified principles: N/A

Modified sections:
  - Technical Constraints: Changed "Better Auth" to "JWT (python-jose)"
    Reason: Better Auth is TypeScript-only, incompatible with Python/FastAPI backend

Added sections: N/A

Removed sections: N/A

Templates validated:
  ✅ .specify/templates/plan-template.md - Constitution Check section exists
  ✅ .specify/templates/spec-template.md - Requirements and success criteria aligned
  ✅ .specify/templates/tasks-template.md - Task categorization compatible

Follow-up TODOs:
  - Implement JWT authentication per specs/007-jwt-authentication/

================================================================================
-->

# AI-Powered Todo Application Constitution

## Core Principles

### I. Spec-Driven Development

All functionality MUST be defined in specifications before implementation. This principle
is non-negotiable and ensures predictable, reviewable, and maintainable development.

- Every feature MUST follow the sequence: specify → plan → tasks → implement
- Specifications define behavior and contracts, never code
- Plans define architecture and decisions, never tasks
- Tasks MUST be small, ordered, and independently executable
- Implementations MUST strictly follow approved tasks
- No implementation before specification approval

**Rationale**: Spec-driven development ensures that all stakeholders understand what
will be built before code is written. This reduces rework, enables clear validation,
and makes the project auditable.

### II. Stateless Backend Architecture

The backend MUST maintain no server-side memory across requests. All state MUST be
persisted in the database or passed explicitly via request parameters.

- All API endpoints MUST be stateless and idempotent where applicable
- Conversation state MUST be persisted in the database, not memory
- No hidden global or in-memory state
- Each request MUST be self-contained and independently processable

**Rationale**: Stateless architecture enables horizontal scaling, simplifies debugging,
and ensures predictable behavior regardless of which server instance handles a request.

### III. Clear Responsibility Boundaries

The system MUST maintain strict separation between layers: UI, API, Agent, MCP Tools,
and Database. Each layer has defined responsibilities that MUST NOT be violated.

- UI: User interaction and presentation only
- API: Request handling, validation, and routing only
- Agent: Natural language processing and tool orchestration only
- MCP Tools: Database operations and external integrations only
- Database: Data persistence only

**Rationale**: Clear boundaries enable independent testing, reduce coupling, and make
the system easier to understand, debug, and extend.

### IV. AI Safety Through Controlled Tool Usage

AI agents MUST NOT directly access the database or perform uncontrolled actions.
All AI actions MUST be routed exclusively through MCP tools.

- AI agents may only perform actions through MCP tools
- MCP tools are the sole layer allowed to read/write the database
- No direct database access from AI agents
- All AI capabilities MUST be explicitly defined via tools
- Tool definitions MUST include clear constraints and validation

**Rationale**: Constraining AI actions through a controlled tool layer ensures
predictable behavior, enables auditing, and prevents unintended database modifications.

### V. Simplicity Over Cleverness

Code and architecture MUST prioritize simplicity, clarity, and maintainability
over clever solutions or premature optimization.

- Minimal, readable, and maintainable code
- No speculative features or scope creep
- Prefer explicit over implicit
- Avoid over-engineering and unnecessary abstractions
- Each component MUST justify its complexity

**Rationale**: Simple systems are easier to understand, debug, and extend. Clever
solutions often become maintenance burdens and introduce subtle bugs.

### VI. Deterministic, Debuggable Behavior

The system MUST behave predictably and provide clear visibility into its operations
for debugging and validation purposes.

- All logic MUST be explainable via specs and plans
- Explicit error handling and user-facing confirmations
- Clear separation of concerns between layers
- System behavior MUST be reproducible given the same inputs
- All state changes MUST be traceable

**Rationale**: Deterministic behavior enables reliable testing, simplifies debugging,
and builds user trust through predictable responses.

## Technical Constraints

The following technical constraints MUST be followed for all implementations:

| Layer | Technology | Notes |
|-------|------------|-------|
| Backend Framework | FastAPI | All API endpoints |
| Database ORM | SQLModel | All database models |
| Database | PostgreSQL (Neon) | Production database |
| Authentication | JWT (python-jose) | HS256 signed tokens, stateless validation |
| AI Orchestration | OpenAI Agents SDK | Agent implementation |
| Tool Interface | Official MCP SDK | All tool definitions |
| Frontend Chat UI | OpenAI ChatKit | User interface |

**Prohibited Patterns**:

- No direct database access from AI agents
- No hidden global or in-memory state
- No implementation before specification approval
- No hardcoded secrets or tokens (use `.env` and docs)
- No speculative features or unspecified functionality

## Development Workflow

All development MUST follow this sequence:

1. **Specify** (`/sp.specify`): Create feature specification defining behavior,
   requirements, user stories, and success criteria
2. **Plan** (`/sp.plan`): Create implementation plan with architecture decisions,
   technical context, and project structure
3. **Tasks** (`/sp.tasks`): Decompose plan into ordered, executable tasks with
   clear dependencies and acceptance criteria
4. **Implement** (`/sp.implement`): Execute tasks in order, following the plan

**Quality Gates**:

- Each spec MUST define scope, goals, non-goals, and constraints
- Architectural decisions MUST include trade-offs
- Testing and validation strategy MUST be documented per phase
- Code review MUST verify compliance with this constitution

**Success Criteria** (for the AI chatbot):

- AI chatbot can correctly add, list, update, complete, and delete todos via
  natural language
- All AI actions are routed exclusively through MCP tools
- Backend remains fully stateless across requests
- Conversation history persists correctly across sessions
- Each subsystem is independently understandable and testable
- The project can be reviewed, extended, or modified safely using the specs alone

## Governance

This constitution supersedes all other practices and guidelines. All development
decisions MUST comply with these principles.

**Amendment Process**:

1. Proposed amendments MUST be documented with rationale
2. Amendments MUST be reviewed for impact on existing specifications
3. Breaking changes require migration plan
4. Version MUST be incremented per semantic versioning:
   - MAJOR: Backward incompatible governance/principle changes
   - MINOR: New principle/section added or materially expanded
   - PATCH: Clarifications, wording, typo fixes

**Compliance**:

- All PRs/reviews MUST verify compliance with this constitution
- Complexity MUST be justified against Principle V (Simplicity)
- Violations MUST be documented and resolved before merge

**Version**: 1.1.0 | **Ratified**: 2026-01-02 | **Last Amended**: 2026-01-10
