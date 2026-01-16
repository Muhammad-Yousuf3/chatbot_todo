# Research: Agent Evaluation, Safety & Observability

**Feature**: 004-agent-observability
**Date**: 2026-01-04
**Status**: Complete

## Research Questions

### RQ1: Logging Format Decision

**Question**: Should logs use structured JSON or plain text format?

**Research Findings**:
Structured logging is the modern standard for observability (Sridharan, 2018). JSON-based logs enable:
- Machine parsing for automated analysis
- Consistent schema across all log entries
- Direct integration with log analysis tools
- Query capability without regex parsing

Plain text logs, while human-readable, require parsing for analysis and lack schema consistency.

**Decision**: Structured JSON logs
**Rationale**: The spec requires queryable logs (FR-013, FR-014) and automated validation (FR-023). JSON enables both while remaining human-readable with proper formatting.

**Alternatives Considered**:
- Plain text: Rejected - doesn't support querying requirements
- Binary formats (protobuf): Rejected - overengineered for this scope

---

### RQ2: Log Granularity Level

**Question**: What level of detail should logs capture?

**Research Findings**:
Observability best practices recommend "high-cardinality, low-volume" logging (Majors, 2022). For AI agents specifically:
- Every decision boundary should be logged (Amodei et al., 2016)
- Tool invocations require full request/response tracing
- Performance metrics should accompany each action

The spec requires complete decision traces (SC-001) while maintaining query performance (SC-008).

**Decision**: Detailed step-by-step logging with hierarchical structure
**Rationale**: Decision-level granularity captures:
1. Input received (user message)
2. Intent classification result
3. Decision type chosen
4. Tool invocations (if any) with full request/response
5. Final outcome category

Each decision gets a unique ID linking all related entries.

**Alternatives Considered**:
- High-level only: Rejected - insufficient for failure diagnosis (SC-003)
- Event sourcing (every state change): Rejected - excessive for scope

---

### RQ3: Drift Detection Strategy

**Question**: How should behavioral drift be detected?

**Research Findings**:
Drift detection in ML systems typically uses:
1. Statistical process control (threshold-based deviations)
2. Reference distribution comparison
3. Golden dataset testing

For demo-focused systems, manual scenario-based review with stored baselines provides simpler verification without ML infrastructure (Sculley et al., 2015).

**Decision**: Hybrid approach - Rule-based assertions with manual scenario review
**Rationale**:
- Store baseline snapshots of intent distribution and tool usage frequency
- Flag deviations exceeding 10% threshold (SC-005)
- Support manual comparison via canonical test messages
- No ML-based anomaly detection (per constraints)

**Alternatives Considered**:
- ML-based drift detection: Rejected - violates "no ML training" constraint
- Pure manual review: Rejected - doesn't meet automatic flagging requirement

---

### RQ4: Error Classification Taxonomy

**Question**: What categories should errors be classified into?

**Research Findings**:
Error taxonomies for AI systems typically distinguish (Russell & Norvig, 2020):
- System errors (infrastructure failures)
- Agent errors (incorrect reasoning)
- User errors (invalid input)
- Policy violations (intentional refusals)

The spec defines four outcome categories: SUCCESS, ERROR, REFUSAL, AMBIGUITY.

**Decision**: Two-level taxonomy (Category:Subcategory)
**Rationale**: Provides both aggregate metrics and detailed diagnosis:

| Category  | Subcategories |
|-----------|---------------|
| SUCCESS   | TASK_COMPLETED, RESPONSE_GIVEN, CLARIFICATION_ANSWERED |
| ERROR     | USER_INPUT, INTENT_CLASSIFICATION, TOOL_INVOCATION, RESPONSE_GENERATION |
| REFUSAL   | OUT_OF_SCOPE, MISSING_PERMISSION, RATE_LIMITED |
| AMBIGUITY | UNCLEAR_INTENT, MULTIPLE_MATCHES, MISSING_CONTEXT |

**Alternatives Considered**:
- Flat categories: Rejected - insufficient for aggregate analysis
- Three-level taxonomy: Rejected - unnecessary complexity

---

### RQ5: Observability Boundaries

**Question**: What must/must not be logged?

**Research Findings**:
Logging best practices require (OWASP, 2023):
- Never log passwords, tokens, or PII unnecessarily
- Log enough context for debugging without sensitive data
- Redact or mask sensitive fields

The spec operates within safety constraints from the constitution.

**Decision**: Explicit inclusion/exclusion lists

**MUST Log**:
- User message content (necessary for audit)
- Intent classification and confidence
- Decision type and rationale
- Tool names and parameters (user_id, task_id, descriptions)
- Timestamps and durations
- Error codes and messages
- Outcome categories

**MUST NOT Log**:
- Authentication tokens
- Session cookies
- Database credentials
- Full stack traces in production (summary only)
- Internal model weights or prompts

**MUST Redact/Mask**:
- User IDs in exported logs (hash or anonymize for external sharing)

---

### RQ6: Log Storage Architecture

**Question**: How should logs be stored given the "no external services" constraint?

**Research Findings**:
Local log storage options:
1. File-based JSON (append-only log files)
2. SQLite database for structured queries
3. In-memory with periodic flush

The spec requires query capability (FR-014) and 30-day retention (FR-015).

**Decision**: SQLite-based log storage
**Rationale**:
- Supports SQL queries for FR-014 requirements
- Single file, no external dependencies
- Handles concurrent writes safely
- Supports time-based retention with DELETE queries
- Portable for export (FR-016)

**Alternatives Considered**:
- JSON files: Rejected - querying requires loading entire file
- PostgreSQL: Rejected - already used for tasks, but logs should be separate for observability isolation
- In-memory only: Rejected - doesn't meet retention requirement

---

## Existing Architecture Analysis

### Current Agent Components (Spec 003)

The agent already includes foundational observability elements:

1. **ToolInvocationRecord** (schemas.py:283-309): Captures tool audit data
   - Conversation/message IDs
   - Tool name and parameters
   - Intent classification
   - Success/failure status
   - Duration in milliseconds

2. **Decision types** already enumerated in DecisionType enum

3. **Intent types** already enumerated in IntentType enum

### Integration Points

The observability layer will integrate at these points:
1. **Before intent classification**: Log incoming message
2. **After intent classification**: Log UserIntent result
3. **Before tool execution**: Log tool call request
4. **After tool execution**: Log tool result
5. **After decision**: Log final AgentDecision with outcome category

### No Modification Required To

- Agent behavior rules (Spec 003) - unchanged
- MCP tools (Spec 002) - unchanged
- Persistence layer (Spec 001) - unchanged

---

## References

Amodei, D., et al. (2016). Concrete problems in AI safety. arXiv preprint arXiv:1606.06565.

Majors, C. (2022). Observability Engineering. O'Reilly Media.

OWASP. (2023). Logging Cheat Sheet. https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html

Russell, S., & Norvig, P. (2020). Artificial Intelligence: A Modern Approach (4th ed.). Pearson.

Sculley, D., et al. (2015). Hidden technical debt in machine learning systems. NeurIPS.

Sridharan, C. (2018). Distributed Systems Observability. O'Reilly Media.
