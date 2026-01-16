# Implementation Plan: JWT Authentication Migration

**Branch**: `007-jwt-authentication` | **Date**: 2026-01-10 | **Spec**: `specs/007-jwt-authentication/spec.md`

---

## Summary

Migrate backend authentication from insecure X-User-Id header to production-ready JWT tokens. The migration preserves all existing API contracts while adding cryptographic verification of user identity.

---

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: FastAPI, python-jose[cryptography], passlib
**Existing**: SQLModel, Pydantic, uvicorn
**Testing**: pytest (existing)
**Target**: All protected API endpoints

---

## Constitution Check

| Principle | Status | Evidence |
|-----------|--------|----------|
| I. Spec-Driven Development | PASS | Full spec exists, following plan → tasks → implement |
| II. Stateless Backend Architecture | PASS | JWT is stateless - no server-side session storage |
| III. Clear Responsibility Boundaries | PASS | Auth layer validates tokens, routes use dependency injection |
| IV. AI Safety Through Controlled Tool Usage | PASS | User ID verified before reaching agent/MCP layer |
| V. Simplicity Over Cleverness | PASS | HS256 symmetric key, no complex key rotation |
| VI. Deterministic, Debuggable Behavior | PASS | Same token always validates same way |

**Note**: This feature updates the constitution to replace "Better Auth" (TypeScript-only) with "JWT Authentication" for Python backend.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                        Request Flow                          │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Client                                                      │
│    │                                                         │
│    ├─► POST /api/auth/signin                                │
│    │     └─► Verify password                                │
│    │         └─► Generate JWT (sub=user_id, exp=24h)       │
│    │             └─► Return { access_token, token_type }   │
│    │                                                         │
│    ├─► GET /api/tasks (Authorization: Bearer <token>)       │
│    │     └─► JWT Dependency                                 │
│    │         ├─► Extract token from header                  │
│    │         ├─► Verify signature (HS256 + JWT_SECRET)     │
│    │         ├─► Check expiration                          │
│    │         └─► Return verified user_id                   │
│    │             └─► Route handler uses user_id            │
│    │                 └─► Query tasks WHERE user_id = ...   │
│    │                                                         │
│    └─► POST /api/chat (with JWT)                            │
│          └─► JWT Dependency → verified user_id             │
│              └─► DecisionContext(user_id=verified)         │
│                  └─► Agent → MCP Tool(user_id=verified)    │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Key Design Decisions

### ADR-007-001: JWT Library Selection

**Context**: Need to encode/decode JWT tokens with signature verification.

**Options**:
1. PyJWT - Popular, minimal
2. python-jose - Supports multiple algorithms, well-maintained
3. authlib - Full OAuth2 implementation (overkill)

**Decision**: `python-jose[cryptography]`

**Rationale**:
- Well-maintained, widely used
- Supports HS256 and future migration to RS256
- cryptography backend is faster and more secure than pure Python

---

### ADR-007-002: Token Storage Strategy

**Context**: Where should tokens be stored client-side?

**Decision**: Frontend responsibility (out of backend scope)

**Guidance for frontend**:
- Memory (safest, lost on refresh)
- localStorage (persists, XSS vulnerable)
- httpOnly cookie (requires backend changes, CSRF concerns)

For hackathon MVP: localStorage is acceptable.

---

### ADR-007-003: Single Token vs Access/Refresh

**Context**: Should we implement refresh tokens?

**Decision**: Single access token (24h expiry)

**Rationale**:
- Simpler implementation
- Acceptable for hackathon/demo
- Can add refresh tokens later without breaking changes

---

## Project Structure Changes

```
backend/
├── src/
│   └── api/
│       ├── deps.py              # MODIFY: JWT validation dependency
│       ├── routes/
│       │   └── auth.py          # MODIFY: Add token generation
│       └── schemas/
│           └── auth.py          # MODIFY: Add TokenResponse
├── .env.example                 # MODIFY: Add JWT_SECRET
└── pyproject.toml               # MODIFY: Add python-jose
```

---

## Implementation Phases

### Phase 1: Dependencies & Configuration

- Add `python-jose[cryptography]` to pyproject.toml
- Add JWT_SECRET, JWT_EXPIRATION_HOURS to .env.example
- Create JWT utility functions (encode, decode)

### Phase 2: Token Generation

- Modify `/api/auth/signup` to return JWT
- Modify `/api/auth/signin` to return JWT
- Add TokenResponse schema
- Update AuthResponse to include token

### Phase 3: Token Validation

- Replace `get_current_user_id` in deps.py with JWT validation
- Extract token from Authorization header
- Verify signature and expiration
- Return verified user_id

### Phase 4: Verification & Testing

- Test all protected endpoints with JWT
- Verify agent receives correct user_id
- Verify MCP tools receive correct user_id
- Verify observability logs correct user_id
- Remove any X-User-Id header references

### Phase 5: Constitution Update

- Update constitution to reflect JWT authentication
- Replace "Better Auth" reference with "JWT Authentication"

---

## Migration Strategy

**Approach**: In-place replacement (no parallel systems)

1. **Add JWT generation** to signup/signin (additive change)
2. **Replace auth dependency** to require JWT (breaking change)
3. **Update frontend** to use JWT instead of X-User-Id

**Backward Compatibility**: None - this is a security fix. Old X-User-Id approach is insecure and must be fully replaced.

---

## Testing Strategy

### Unit Tests
- JWT encoding returns valid token
- JWT decoding extracts correct payload
- Expired token raises appropriate error
- Invalid signature raises error

### Integration Tests
- Signup returns token
- Signin returns token
- Protected route accepts valid token
- Protected route rejects invalid token
- Protected route rejects expired token
- Protected route rejects missing token

### Manual Verification
- [ ] Signup → receive token
- [ ] Signin → receive token
- [ ] Use token to access /api/tasks
- [ ] Chat message → agent uses correct user_id
- [ ] Observability shows correct user_id

---

## Risk Analysis

| Risk | Impact | Mitigation |
|------|--------|------------|
| JWT_SECRET leaked | CRITICAL | Use strong secret, never log, rotate if compromised |
| Token expiry too short | MEDIUM | Default 24h, configurable via env |
| Frontend not updated | HIGH | Coordinate frontend changes, clear migration docs |
| Existing sessions invalid | LOW | Expected - users re-login once |

---

## Success Criteria (from Spec)

- [ ] SC-001: Zero endpoints accept X-User-Id header
- [ ] SC-002: All protected routes use JWT dependency
- [ ] SC-003: Agent receives verified user_id
- [ ] SC-004: Observability logs correct user_id
- [ ] SC-005: Validation <10ms latency
- [ ] SC-006: API contracts preserved

---

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| JWT_SECRET | Yes | - | Signing key (min 32 chars) |
| JWT_EXPIRATION_HOURS | No | 24 | Token validity period |

---

## Next Steps

1. Run `/sp.tasks` to generate executable task list
2. Implement Phase 1-5 in order
3. Update frontend to use JWT
4. Update constitution
