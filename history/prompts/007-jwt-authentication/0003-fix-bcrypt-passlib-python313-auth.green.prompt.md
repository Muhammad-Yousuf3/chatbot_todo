---
id: "0003"
title: "Fix bcrypt passlib Python 3.13 auth"
stage: green
date: 2026-01-11
surface: agent
model: claude-opus-4-5
feature: 007-jwt-authentication
branch: 006-frontend-chat-ui
user: muhammad-yousuf
command: /sp.implement
labels: ["auth", "bcrypt", "python313", "security", "bug-fix"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - backend/src/api/password.py (created)
  - backend/src/api/routes/auth.py (modified)
  - backend/pyproject.toml (modified)
  - backend/tests/unit/test_password.py (created)
tests:
  - tests/unit/test_password.py (20 tests, all passing)
---

## Prompt

Analyze the FastAPI backend auth error and fix it correctly.

Error details:
- passlib + bcrypt error on Python 3.13
- WARNING: error reading bcrypt version (__about__ missing)
- ValueError: password cannot be longer than 72 bytes
- Crash occurs during signup at password hashing

Tasks:
1. Fix bcrypt/passlib incompatibility with Python 3.13
   - Use a supported bcrypt backend or switch to passlib's recommended configuration
   - Pin compatible versions if required
2. Implement SAFE password hashing:
   - Enforce max password length BEFORE hashing (72 bytes for bcrypt)
   - Reject overly long passwords with a clear 400 error (do NOT silently truncate)
3. Ensure hashing + verification are centralized in a utility module
4. Update pyproject.toml with correct dependency versions
5. Add unit tests covering:
   - Normal password
   - Password >72 bytes (expect rejection)
6. Ensure signup endpoint returns proper error instead of 500

Constraints:
- Keep bcrypt (do not downgrade security)
- No breaking changes to user schema
- Follow spec-driven approach
- Code must work on Python 3.13

After fixing, explain briefly:
- Root cause
- Why this solution is correct

## Response snapshot

Fixed the bcrypt/passlib Python 3.13 compatibility issue by:

1. **Created centralized password module** (`backend/src/api/password.py`):
   - `PasswordTooLongError` exception for passwords >72 bytes
   - `validate_password_length()` - validates before hashing
   - `hash_password()` - hashes with validation
   - `verify_password()` - verifies with validation
   - Suppressed passlib warning about bcrypt `__about__` module

2. **Updated dependencies** (`pyproject.toml`):
   - Pinned `bcrypt>=4.0.0,<5` for Python 3.13 compatibility

3. **Updated auth endpoints** (`backend/src/api/routes/auth.py`):
   - Removed inline password hashing code
   - Import from centralized password module
   - Added try/except for PasswordTooLongError
   - Returns 400 error with PASSWORD_TOO_LONG code

4. **Added comprehensive tests** (20 tests, all passing):
   - Password length validation (short, exact 72, 73, 100 bytes)
   - UTF-8 multi-byte character handling
   - Hash generation and verification
   - Error handling

## Outcome

- ✅ Impact: High - fixes auth crash on Python 3.13
- 🧪 Tests: 20 passed, 0 failed
- 📁 Files: 4 (2 created, 2 modified)
- 🔁 Next prompts: Integration testing, consider passlib 2.x when released
- 🧠 Reflection: Silent truncation is a security anti-pattern - always reject invalid input explicitly

## Evaluation notes (flywheel)

- Failure modes observed: passlib 1.7.4 incompatible with bcrypt 4.x __about__ removal
- Graders run and results (PASS/FAIL): PASS - all 20 unit tests pass
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): Monitor passlib 2.x release for native bcrypt 4.x support
