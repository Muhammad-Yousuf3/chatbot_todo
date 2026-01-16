# Research: Agent Behavior & Tool Invocation Policy

**Feature Branch**: `003-agent-behavior-policy`
**Date**: 2026-01-03
**Status**: Complete

## Research Questions

1. What agent orchestration patterns best support deterministic, auditable behavior?
2. How should intent classification be implemented for predictable results?
3. What guardrail strategies ensure safe tool invocation?
4. How to handle ambiguous inputs while maintaining user experience?

---

## 1. Agent Orchestration Patterns

### Decision: Hybrid ReAct with Deterministic Controls

**Rationale**: Pure ReAct (Reasoning + Acting) patterns allow flexible tool selection but are inherently non-deterministic. Production systems require a hybrid approach combining LLM reasoning with deterministic validation layers.

**Key Principle**: "LLM → decides intent, Runtime → validates + executes, LLM → reasons on the result" (Dev Community, 2025). This separation enables security, sandboxing, retry logic, observability, deterministic behavior, and compliance auditability.

**Alternatives Considered**:

| Pattern | Pros | Cons | Decision |
|---------|------|------|----------|
| Pure ReAct | Flexible, adaptive | Non-deterministic, hard to audit | Rejected |
| Plan-then-Execute | Deterministic flow | Less flexible for simple queries | Partial adoption |
| Function Calling | Structured output, lower error rate | Requires strict schema | **Adopted** |
| Sequential Agent | Fully deterministic | Cannot handle dynamic conversation | Rejected |

**Implementation Approach**:
- Use structured function calling for tool invocation (not free-form ReAct)
- Agent proposes action → validation layer approves → tool executes
- Deterministic state machine for conversation flow

**References**:
- Yao et al. (2022). ReAct: Synergizing Reasoning and Acting in Language Models.
- [ReAct vs Tool Calling](https://dev.to/parth_sarthisharma_105e7/react-vs-tool-calling-why-your-llm-should-decide-but-never-execute-cp3) - Dev Community
- [Plan-and-Execute Pattern](https://dev.to/jamesli/react-vs-plan-and-execute-a-practical-comparison-of-llm-agent-patterns-4gh9)

---

## 2. Intent Classification Strategy

### Decision: LLM-Based Classification with Strict Schema Validation

**Rationale**: While rule-based keyword matching is fully deterministic, it fails on natural language variation ("I gotta remember to..." vs "remind me to..."). LLM-based classification with structured output schema provides flexibility while maintaining predictability through validation.

**Key Principle**: "Function calling offers a more streamlined approach, presenting a well-organized structure and framework that can yield deterministic results from LLM with a reduced error rate" (Medium, 2025).

**Alternatives Considered**:

| Approach | Determinism | Language Flexibility | Error Rate | Decision |
|----------|-------------|---------------------|------------|----------|
| Rule-based keywords | 100% | Low (brittle) | High (false negatives) | Rejected |
| LLM + strict schema | High (validated) | High | Low | **Adopted** |
| ML classifier | Medium | Medium | Medium | Rejected (complexity) |
| Hybrid rules + LLM | High | High | Low | Future consideration |

**Implementation Approach**:
- Define strict intent schema: `create_task | list_tasks | complete_task | update_task | delete_task | general_conversation | ambiguous`
- LLM classifies intent into one of these categories
- Validation layer rejects invalid classifications
- Fallback to `ambiguous` when confidence is low

**Determinism Guarantee**:
- Same input + same conversation history → same classification (temperature=0)
- Schema validation ensures only valid intents proceed
- Audit log captures classification decision

---

## 3. Guardrail Strategy

### Decision: Layered Deterministic + LLM Guardrails

**Rationale**: "The most robust approach combines multiple layers of protection: Deterministic Guardrails (hard rules), LLM-Based Guardrails (context understanding), and Granular Access Control" (Civic, 2025).

**Key Principles**:
1. Deterministic guardrails provide absolute boundaries that cannot be linguistically manipulated
2. LLM-based guardrails understand context and nuance
3. All tool invocations must pass through both layers

**Guardrail Architecture**:

```
User Message
     ↓
[Layer 1: Input Validation]
  - Required fields present (user_id)
  - Message length limits
  - Character encoding validation
     ↓
[Layer 2: Intent Classification]
  - LLM classifies intent
  - Schema validation
     ↓
[Layer 3: Policy Enforcement]
  - Destructive action confirmation required
  - Read-before-write enforcement
  - Tool invocation whitelist
     ↓
[Layer 4: Tool Execution]
  - MCP tool invocation
  - Result validation
     ↓
[Layer 5: Output Sanitization]
  - No internal details exposed
  - User-friendly formatting
```

**References**:
- [NeMo Guardrails](https://developer.nvidia.com/nemo-guardrails) - NVIDIA
- [Deterministic Guardrails for AI Agent Security](https://www.civic.com/resources/deterministic-guardrails-for-ai-agent-security) - Civic
- [LLM Guardrails Best Practices](https://www.datadoghq.com/blog/llm-guardrails-best-practices/) - Datadog

---

## 4. Ambiguous Input Handling

### Decision: Ask Clarification Before Acting

**Rationale**: "Never silently mutate data on ambiguous input" is a core safety principle. Asking for clarification preserves user trust and prevents incorrect actions.

**Alternatives Considered**:

| Approach | User Experience | Safety | Decision |
|----------|----------------|--------|----------|
| Ask clarification | Slightly slower | High | **Adopted** |
| Choose safest no-op | Fast | Medium (may frustrate user) | Rejected |
| Probabilistic guess | Fast | Low (wrong actions) | Rejected |

**Implementation Rules**:
1. If intent classification returns `ambiguous` → ask clarifying question
2. If task reference is unclear (multiple matches) → list options and ask
3. If required parameter is missing → prompt for it
4. Never invoke mutating tool (add/update/complete/delete) without clear intent

---

## 5. Destructive Action Handling

### Decision: Two-Step Confirmation for Delete Only

**Rationale**: Delete is irreversible and should require explicit confirmation. Complete is idempotent and less risky, so single-step is acceptable.

**Confirmation Matrix**:

| Action | Confirmation Required | Rationale |
|--------|----------------------|-----------|
| add_task | No | Creating is not destructive |
| list_tasks | No | Read-only operation |
| update_task | No | Can be reverted by another update |
| complete_task | No | Idempotent, can be re-completed |
| delete_task | **Yes** | Irreversible, data loss |

**Two-Step Flow for Delete**:
1. User: "delete the groceries task"
2. Agent: "Are you sure you want to delete 'buy groceries'? This cannot be undone. Reply 'yes' to confirm."
3. User: "yes"
4. Agent: [invokes delete_task] "Task 'buy groceries' has been deleted."

---

## 6. Ordering Guarantees

### Decision: Read-Before-Write, Sequential Tool Calls

**Rationale**: Task-referencing operations (complete, update, delete) require knowing which task to target. The agent must call `list_tasks` to identify the task before mutating.

**Rules**:
1. **Read-before-write**: Always invoke `list_tasks` before `complete_task`, `update_task`, or `delete_task`
2. **Sequential execution**: One tool call completes before the next begins
3. **No parallel mutations**: Prevents race conditions and ensures auditability

**Allowed Sequences**:
- `add_task` (standalone)
- `list_tasks` (standalone)
- `list_tasks` → `complete_task` (must identify first)
- `list_tasks` → `update_task` (must identify first)
- `list_tasks` → [confirmation] → `delete_task` (must identify and confirm)
- `add_task` → `list_tasks` (for "add X and show my list")

---

## Summary of Decisions

| Decision Area | Choice | Key Rationale |
|---------------|--------|---------------|
| Agent Pattern | Hybrid ReAct + Deterministic Controls | Balance flexibility with auditability |
| Intent Classification | LLM with Strict Schema | Natural language understanding + validation |
| Guardrails | Layered (Deterministic + LLM) | Defense in depth |
| Ambiguous Input | Ask Clarification | Safety over speed |
| Destructive Confirmation | Delete only (two-step) | Risk-proportionate UX |
| Ordering | Read-before-write, sequential | Prevent incorrect mutations |

---

## Sources

- [ReAct Prompting Guide](https://www.promptingguide.ai/techniques/react)
- [ReAct vs Tool Calling](https://dev.to/parth_sarthisharma_105e7/react-vs-tool-calling-why-your-llm-should-decide-but-never-execute-cp3)
- [Plan-and-Execute Pattern](https://dev.to/jamesli/react-vs-plan-and-execute-a-practical-comparison-of-llm-agent-patterns-4gh9)
- [NeMo Guardrails](https://developer.nvidia.com/nemo-guardrails)
- [Deterministic Guardrails for AI Agent Security](https://www.civic.com/resources/deterministic-guardrails-for-ai-agent-security)
- [LLM Guardrails Best Practices](https://www.datadoghq.com/blog/llm-guardrails-best-practices/)
- [Agent Framework Comparison](https://medium.com/@roberto.g.infante/the-state-of-ai-agent-frameworks-comparing-langgraph-openai-agent-sdk-google-adk-and-aws-d3e52a497720)
