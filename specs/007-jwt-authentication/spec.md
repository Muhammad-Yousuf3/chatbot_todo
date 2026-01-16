# Feature Specification: JWT Authentication Migration

**Feature Branch**: `007-jwt-authentication`
**Created**: 2026-01-10
**Status**: Draft
**Input**: User request to migrate from insecure X-User-Id header to production-ready JWT authentication

---

## Context & Problem Statement

### Current State (INSECURE)

The backend currently uses a simple `X-User-Id` header for authentication:

```python
# backend/src/api/deps.py
async def get_current_user_id(
    x_user_id: Annotated[str | None, Header(alias="X-User-Id")] = None,
) -> str:
    if not x_user_id:
        raise HTTPException(status_code=401, ...)
    return x_user_id  # TRUSTS THE HEADER BLINDLY
```

**Security Vulnerability**: Any client can impersonate any user by sending a different `X-User-Id` header. There is no token validation, no cryptographic verification, and no session management.

### Target State (SECURE)

Replace with JWT-based authentication:
- Signup/signin returns signed JWT access tokens
- All protected endpoints require valid JWT in `Authorization: Bearer <token>` header
- Tokens are cryptographically signed and verified on each request
- User ID is extracted from verified token payload (cannot be forged)

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - User Signup (Priority: P1)

A new user creates an account with email, password, and display name. Upon successful registration, they receive a JWT access token to immediately start using the API.

**Independent Test**: POST `/api/auth/signup` with valid data returns 201 with `access_token` in response body.

**Acceptance Scenarios**:

1. **Given** valid signup data, **When** user submits, **Then** account is created and JWT returned
2. **Given** existing email, **When** user submits, **Then** 409 Conflict with "EMAIL_EXISTS" error
3. **Given** weak password (<6 chars), **When** user submits, **Then** 422 validation error

---

### User Story 2 - User Signin (Priority: P1)

An existing user signs in with email and password. Upon successful authentication, they receive a fresh JWT access token.

**Independent Test**: POST `/api/auth/signin` with valid credentials returns 200 with `access_token`.

**Acceptance Scenarios**:

1. **Given** valid credentials, **When** user signs in, **Then** JWT returned with user info
2. **Given** wrong password, **When** user signs in, **Then** 401 Unauthorized
3. **Given** non-existent email, **When** user signs in, **Then** 401 Unauthorized (same error to prevent enumeration)

---

### User Story 3 - Access Protected Endpoints (Priority: P1)

An authenticated user accesses protected API endpoints by including their JWT in the Authorization header. The backend validates the token and extracts the user ID.

**Independent Test**: GET `/api/tasks` with valid `Authorization: Bearer <token>` returns user's tasks.

**Acceptance Scenarios**:

1. **Given** valid JWT, **When** accessing protected route, **Then** request succeeds with user context
2. **Given** expired JWT, **When** accessing protected route, **Then** 401 with "TOKEN_EXPIRED" error
3. **Given** invalid/tampered JWT, **When** accessing protected route, **Then** 401 with "INVALID_TOKEN" error
4. **Given** no Authorization header, **When** accessing protected route, **Then** 401 with "MISSING_TOKEN" error

---

### User Story 4 - Agent & MCP Tool Execution (Priority: P1)

The authenticated user's ID (from verified JWT) is propagated to the agent layer and MCP tools. All tool executions use the verified user_id.

**Independent Test**: Send chat message with valid JWT, agent executes `add_task` tool, task is created with correct `user_id`.

**Acceptance Scenarios**:

1. **Given** valid JWT, **When** agent executes MCP tool, **Then** tool receives verified user_id
2. **Given** valid JWT, **When** decision is logged, **Then** observability records correct user_id

---

### User Story 5 - CORS Preflight (Priority: P2)

OPTIONS requests for CORS preflight bypass authentication to allow browsers to negotiate cross-origin access.

**Independent Test**: OPTIONS `/api/tasks` returns 200 without Authorization header.

**Acceptance Scenarios**:

1. **Given** OPTIONS request, **When** no auth header, **Then** 200 OK with CORS headers

---

### Edge Cases

- What happens when JWT is malformed (not base64)? → 401 "INVALID_TOKEN"
- What happens when JWT signature doesn't match? → 401 "INVALID_TOKEN"
- What happens when JWT is expired? → 401 "TOKEN_EXPIRED"
- What happens when JWT has wrong issuer/audience? → 401 "INVALID_TOKEN"
- What happens when user is deleted but has valid JWT? → 401 "USER_NOT_FOUND" (optional: check on critical ops)

---

## Requirements *(mandatory)*

### Functional Requirements

#### Token Issuance
- **FR-001**: System MUST return JWT access token on successful signup
- **FR-002**: System MUST return JWT access token on successful signin
- **FR-003**: JWT MUST contain: sub (user_id), email, exp (expiration), iat (issued at)
- **FR-004**: JWT MUST be signed with HS256 algorithm using secret from environment

#### Token Validation
- **FR-005**: System MUST extract JWT from `Authorization: Bearer <token>` header
- **FR-006**: System MUST verify JWT signature before trusting payload
- **FR-007**: System MUST reject expired tokens with 401 "TOKEN_EXPIRED"
- **FR-008**: System MUST reject invalid/malformed tokens with 401 "INVALID_TOKEN"
- **FR-009**: System MUST extract user_id from verified token's `sub` claim

#### Protected Routes
- **FR-010**: All routes under `/api/tasks/*` MUST require valid JWT
- **FR-011**: All routes under `/api/chat/*` MUST require valid JWT
- **FR-012**: All routes under `/api/conversations/*` MUST require valid JWT
- **FR-013**: Routes `/api/auth/signup` and `/api/auth/signin` MUST NOT require JWT
- **FR-014**: Route `/api/auth/me` MUST require valid JWT

#### User ID Propagation
- **FR-015**: Verified user_id MUST be available to all route handlers via FastAPI dependency
- **FR-016**: Verified user_id MUST be passed to agent DecisionContext
- **FR-017**: Verified user_id MUST be passed to MCP tool executions
- **FR-018**: Verified user_id MUST be logged in observability records

#### Security
- **FR-019**: JWT secret MUST be read from `JWT_SECRET` environment variable
- **FR-020**: JWT secret MUST be at least 32 characters
- **FR-021**: System MUST NOT log JWT tokens or secrets
- **FR-022**: OPTIONS requests MUST bypass authentication for CORS

---

### Non-Functional Requirements

- **NFR-001**: Token validation MUST complete in <10ms (excluding network)
- **NFR-002**: Failed auth attempts MUST NOT reveal whether email exists (prevent enumeration)
- **NFR-003**: Token expiration default: 24 hours (configurable via `JWT_EXPIRATION_HOURS`)
- **NFR-004**: All auth errors MUST return consistent error schema

---

### Key Entities

- **User**: Existing model - id (UUID), email, password_hash, display_name
- **JWTPayload**: Token payload - sub (user_id), email, exp, iat
- **TokenResponse**: API response - access_token, token_type, expires_in

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Zero endpoints accept forged user_id (X-User-Id header removed)
- **SC-002**: All 5 protected route files use JWT-based auth dependency
- **SC-003**: Agent and MCP tools receive verified user_id
- **SC-004**: Observability logs show correct user_id from JWT
- **SC-005**: Token validation adds <10ms to request latency
- **SC-006**: All existing API contracts preserved (same request/response shapes)

---

## Technical Constraints

- **Library**: `python-jose[cryptography]` for JWT encoding/decoding
- **Algorithm**: HS256 (symmetric, fast, suitable for single backend)
- **Header**: `Authorization: Bearer <token>` (OAuth2 standard)
- **Secret**: Minimum 32 characters from `JWT_SECRET` env var
- **Expiration**: Default 24 hours, configurable

---

## Files to Modify

| File | Change |
|------|--------|
| `backend/src/api/deps.py` | Replace X-User-Id with JWT validation |
| `backend/src/api/routes/auth.py` | Add JWT token generation to signup/signin |
| `backend/src/api/schemas/auth.py` | Add TokenResponse schema |
| `backend/.env.example` | Add JWT_SECRET, JWT_EXPIRATION_HOURS |
| `backend/pyproject.toml` | Add python-jose[cryptography] dependency |

Files that use `CurrentUserId` (no changes needed - dependency injection handles it):
- `backend/src/api/routes/tasks.py`
- `backend/src/api/routes/chat.py`
- `backend/src/api/routes/conversations.py`

---

## Assumptions

1. Single backend instance (no need for asymmetric keys or key rotation)
2. Token refresh not required for MVP (users re-login after expiry)
3. No blacklist/revocation for MVP (tokens valid until expiry)
4. Frontend will store token in memory/localStorage and include in requests

---

## Out of Scope

- Refresh tokens
- Token revocation/blacklist
- OAuth2 social login
- Multi-factor authentication
- Password reset flow
- Email verification
