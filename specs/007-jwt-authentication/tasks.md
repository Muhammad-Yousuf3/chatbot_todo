# Tasks: JWT Authentication Migration

**Input**: Design documents from `/specs/007-jwt-authentication/`
**Prerequisites**: spec.md (complete), plan.md (complete)

---

## Phase 1: Dependencies & Configuration

**Purpose**: Set up JWT library and environment variables

- [x] T001 Add python-jose[cryptography] dependency to backend/pyproject.toml
- [x] T002 Run `uv sync` to install new dependency
- [x] T003 Add JWT_SECRET and JWT_EXPIRATION_HOURS to backend/.env.example
- [x] T004 Create JWT utility module at backend/src/api/jwt.py with encode_token and decode_token functions

---

## Phase 2: Token Generation

**Purpose**: Modify auth endpoints to return JWT tokens

- [x] T005 Add TokenResponse schema to backend/src/api/schemas/auth.py
- [x] T006 Update AuthResponse schema to include access_token field in backend/src/api/schemas/auth.py
- [x] T007 Modify signup endpoint to generate and return JWT in backend/src/api/routes/auth.py
- [x] T008 Modify signin endpoint to generate and return JWT in backend/src/api/routes/auth.py

**Checkpoint**: Signup and signin return JWT tokens

---

## Phase 3: Token Validation

**Purpose**: Replace X-User-Id dependency with JWT validation

- [x] T009 Rewrite get_current_user_id in backend/src/api/deps.py to extract and validate JWT from Authorization header
- [x] T010 Add proper error responses for missing token (401 MISSING_TOKEN)
- [x] T011 Add proper error responses for invalid token (401 INVALID_TOKEN)
- [x] T012 Add proper error responses for expired token (401 TOKEN_EXPIRED)
- [x] T013 Update /api/auth/me endpoint to use JWT dependency in backend/src/api/routes/auth.py

**Checkpoint**: Protected endpoints require valid JWT

---

## Phase 4: CORS & Preflight

**Purpose**: Ensure OPTIONS requests bypass authentication

- [x] T014 Verify CORS middleware in backend/src/main.py allows preflight without auth
- [x] T015 [P] Test OPTIONS request to /api/tasks returns 200 without auth header

---

## Phase 5: Verification & Cleanup

**Purpose**: Verify JWT flows through entire stack

- [x] T016 Test /api/tasks endpoints with JWT authentication
- [x] T017 Test /api/chat endpoints with JWT authentication
- [x] T018 Test /api/conversations endpoints with JWT authentication
- [x] T019 Verify agent DecisionContext receives verified user_id from JWT
- [x] T020 Verify MCP tool execution receives verified user_id from JWT
- [x] T021 Verify observability logs contain correct user_id from JWT
- [x] T022 Remove any remaining X-User-Id header references from codebase
- [x] T023 [P] Update frontend AuthContext to store and send JWT token

---

## Phase 6: Constitution & Documentation

**Purpose**: Update project documentation

- [x] T024 Update constitution.md to replace "Better Auth" with "JWT Authentication"
- [x] T025 Add JWT authentication notes to CLAUDE.md if needed

---

## Dependencies & Execution Order

### Sequential Dependencies

```
T001 → T002 (install after adding dep)
T004 → T007, T008 (jwt.py needed for auth routes)
T005, T006 → T007, T008 (schemas needed for response)
T009-T012 → T016-T021 (validation needed before testing)
T016-T021 → T022 (verify before cleanup)
```

### Parallel Opportunities

- T003, T004 can run in parallel after T001-T002
- T005, T006 can run in parallel
- T014, T015 can run in parallel with Phase 5
- T023, T024, T025 can run in parallel after verification

---

## Task Summary

| Phase | Count |
|-------|-------|
| Phase 1: Dependencies | 4 |
| Phase 2: Token Generation | 4 |
| Phase 3: Token Validation | 5 |
| Phase 4: CORS | 2 |
| Phase 5: Verification | 8 |
| Phase 6: Documentation | 2 |
| **Total** | **25** |

---

## Implementation Notes

### JWT Utility Functions (T004)

```python
# backend/src/api/jwt.py
import os
from datetime import datetime, timedelta
from jose import jwt, JWTError

JWT_SECRET = os.getenv("JWT_SECRET")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = int(os.getenv("JWT_EXPIRATION_HOURS", "24"))

def encode_token(user_id: str, email: str) -> str:
    """Create JWT token with user claims."""
    payload = {
        "sub": user_id,
        "email": email,
        "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS),
        "iat": datetime.utcnow(),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def decode_token(token: str) -> dict:
    """Decode and validate JWT token."""
    return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
```

### Auth Dependency (T009)

```python
# backend/src/api/deps.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from src.api.jwt import decode_token
from jose import JWTError, ExpiredSignatureError

security = HTTPBearer()

async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> str:
    """Extract and validate user_id from JWT token."""
    try:
        payload = decode_token(credentials.credentials)
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"error": {"code": "INVALID_TOKEN", "message": "Invalid token payload"}},
            )
        return user_id
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": {"code": "TOKEN_EXPIRED", "message": "Token has expired"}},
        )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": {"code": "INVALID_TOKEN", "message": "Invalid token"}},
        )
```

---

## Environment Setup

Before running tasks, ensure `.env` has:

```bash
JWT_SECRET=your-secure-secret-key-at-least-32-characters-long
JWT_EXPIRATION_HOURS=24
```
